import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import Date, DateTime, Float, String


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.database import engine


MARKET_QUERY = """
SELECT
    asset,
    price,
    timestamp
FROM market_data
ORDER BY asset, timestamp;
"""

MACRO_QUERY = """
SELECT
    country,
    indicator,
    value,
    record_date,
    source,
    timestamp
FROM macro_data
ORDER BY country, indicator, record_date, timestamp;
"""


def normalize_indicator_name(indicator):
    return f"macro_{indicator.lower()}"


def load_market_data():
    market_df = pd.read_sql(MARKET_QUERY, engine)

    if market_df.empty:
        return market_df

    market_df["timestamp"] = pd.to_datetime(market_df["timestamp"])
    market_df["price_date"] = market_df["timestamp"].dt.normalize()

    return market_df


def load_macro_snapshots():
    macro_df = pd.read_sql(MACRO_QUERY, engine)

    if macro_df.empty:
        return macro_df

    macro_df["record_date"] = pd.to_datetime(macro_df["record_date"])
    macro_df["timestamp"] = pd.to_datetime(macro_df["timestamp"])

    macro_latest = (
        macro_df.sort_values(["country", "indicator", "record_date", "timestamp"])
        .drop_duplicates(["country", "indicator", "record_date"], keep="last")
    )

    macro_values = (
        macro_latest.pivot_table(
            index=["country", "record_date"],
            columns="indicator",
            values="value",
            aggfunc="last",
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )

    rename_columns = {
        column: normalize_indicator_name(column)
        for column in macro_values.columns
        if column not in ("country", "record_date")
    }
    macro_values = macro_values.rename(columns=rename_columns)
    macro_value_columns = list(rename_columns.values())

    macro_values = macro_values.sort_values(["country", "record_date"])
    macro_values[macro_value_columns] = macro_values.groupby("country")[
        macro_value_columns
    ].ffill()

    return macro_values.rename(columns={"record_date": "macro_record_date"})


def build_market_signal_frame(market_df):
    market_daily = (
        market_df.sort_values(["asset", "price_date", "timestamp"])
        .drop_duplicates(["asset", "price_date"], keep="last")
        .copy()
    )

    market_daily = market_daily.sort_values(["asset", "price_date"])
    market_groups = market_daily.groupby("asset", group_keys=False)

    market_daily["daily_return"] = market_groups["price"].pct_change()
    market_daily["weekly_return"] = market_groups["price"].pct_change(periods=5)
    market_daily["momentum"] = market_groups["price"].pct_change(periods=3)
    market_daily["volatility"] = (
        market_groups["daily_return"]
        .rolling(window=5, min_periods=2)
        .std()
        .reset_index(level=0, drop=True)
    )

    market_daily["country"] = "USA"

    return market_daily


def join_macro_signals(market_signals_df, macro_snapshots_df):
    if macro_snapshots_df.empty:
        market_signals_df["macro_record_date"] = pd.NaT
        market_signals_df["macro_gdp"] = pd.NA
        market_signals_df["macro_cpi"] = pd.NA
        market_signals_df["macro_interest_rate"] = pd.NA
        return market_signals_df

    market_signals_df = market_signals_df.copy()
    macro_snapshots_df = macro_snapshots_df.copy()
    market_signals_df["price_date"] = (
        pd.to_datetime(market_signals_df["price_date"])
        .dt.normalize()
        .astype("datetime64[ns]")
    )
    macro_snapshots_df["macro_record_date"] = (
        pd.to_datetime(macro_snapshots_df["macro_record_date"])
        .dt.normalize()
        .astype("datetime64[ns]")
    )

    return pd.merge_asof(
        market_signals_df.sort_values("price_date"),
        macro_snapshots_df.sort_values("macro_record_date"),
        left_on="price_date",
        right_on="macro_record_date",
        by="country",
        direction="backward",
    )


def save_market_signals(signals_df):
    output_columns = [
        "asset",
        "country",
        "price_date",
        "timestamp",
        "price",
        "daily_return",
        "weekly_return",
        "momentum",
        "volatility",
        "macro_record_date",
        "macro_gdp",
        "macro_cpi",
        "macro_interest_rate",
        "signal_created_at",
    ]

    for column in output_columns:
        if column not in signals_df.columns:
            signals_df[column] = pd.NA

    signals_df = signals_df[output_columns].sort_values(["asset", "price_date"])
    signals_df["price_date"] = pd.to_datetime(signals_df["price_date"]).dt.date
    signals_df["macro_record_date"] = pd.to_datetime(
        signals_df["macro_record_date"]
    ).dt.date

    with engine.begin() as conn:
        signals_df.to_sql(
            "market_signals",
            conn,
            if_exists="replace",
            index=False,
            dtype={
                "asset": String(50),
                "country": String(50),
                "price_date": Date(),
                "timestamp": DateTime(),
                "price": Float(),
                "daily_return": Float(),
                "weekly_return": Float(),
                "momentum": Float(),
                "volatility": Float(),
                "macro_record_date": Date(),
                "macro_gdp": Float(),
                "macro_cpi": Float(),
                "macro_interest_rate": Float(),
                "signal_created_at": DateTime(),
            },
        )

    return signals_df


def main():
    market_df = load_market_data()

    if market_df.empty:
        print("No market data found. Run ingestion before building signals.")
        return 1

    macro_snapshots_df = load_macro_snapshots()
    market_signals_df = build_market_signal_frame(market_df)
    signals_df = join_macro_signals(market_signals_df, macro_snapshots_df)
    signals_df["signal_created_at"] = datetime.now()

    saved_df = save_market_signals(signals_df)

    print(f"Built {len(saved_df)} market signal rows into market_signals.")
    print()
    print(
        saved_df[
            [
                "asset",
                "price_date",
                "price",
                "daily_return",
                "weekly_return",
                "momentum",
                "volatility",
                "macro_gdp",
                "macro_cpi",
                "macro_interest_rate",
            ]
        ].tail(20)
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
