import argparse
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf
from sqlalchemy import text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.database import engine


ASSETS = [
    ("^GSPC", "SP500"),
    ("^IXIC", "NASDAQ"),
    ("GC=F", "GOLD"),
    ("CL=F", "OIL"),
    ("EURUSD=X", "EURUSD"),
    ("INR=X", "USDINR"),
]


def get_existing_dates(asset_name):
    query = text("""
    SELECT DISTINCT DATE(timestamp) AS price_date
    FROM market_data
    WHERE asset = :asset
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"asset": asset_name}).fetchall()

    return {row.price_date for row in rows}


def normalize_timestamp(value):
    timestamp = pd.Timestamp(value)

    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert(None)

    return timestamp.to_pydatetime()


def build_history_records(symbol, asset_name, period, interval):
    ticker = yf.Ticker(symbol)
    history_df = ticker.history(period=period, interval=interval)

    if history_df.empty:
        return []

    records = []

    for timestamp, row in history_df.iterrows():
        close_price = row.get("Close")

        if pd.isna(close_price):
            continue

        records.append(
            {
                "asset": asset_name,
                "price": float(close_price),
                "timestamp": normalize_timestamp(timestamp),
            }
        )

    return records


def insert_missing_records(asset_name, records):
    existing_dates = get_existing_dates(asset_name)
    missing_records = [
        record
        for record in records
        if record["timestamp"].date() not in existing_dates
    ]

    if not missing_records:
        return 0, len(records)

    insert_query = text("""
    INSERT INTO market_data(asset, price, timestamp)
    VALUES (:asset, :price, :timestamp)
    """)

    with engine.begin() as conn:
        conn.execute(insert_query, missing_records)

    skipped_count = len(records) - len(missing_records)
    return len(missing_records), skipped_count


def backfill_asset(symbol, asset_name, period, interval):
    records = build_history_records(symbol, asset_name, period, interval)
    inserted_count, skipped_count = insert_missing_records(asset_name, records)

    print(
        f"{asset_name}: fetched={len(records)} "
        f"inserted={inserted_count} skipped={skipped_count}"
    )

    return inserted_count


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backfill historical daily market data from yfinance."
    )
    parser.add_argument(
        "--period",
        default="2y",
        help="yfinance period to fetch, for example 6mo, 1y, 2y, 5y, max.",
    )
    parser.add_argument(
        "--interval",
        default="1d",
        help="yfinance interval to fetch. Use 1d for signal generation.",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    total_inserted = 0

    for symbol, asset_name in ASSETS:
        try:
            total_inserted += backfill_asset(
                symbol=symbol,
                asset_name=asset_name,
                period=args.period,
                interval=args.interval,
            )
        except Exception as exc:
            print(f"{asset_name}: error={exc}")

    print(f"Historical market backfill complete. Inserted rows: {total_inserted}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
