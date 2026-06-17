import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
from sqlalchemy import text
from config.database import engine


BULLISH_SIGNALS = {"STRONG_BULLISH", "BULLISH", "SLIGHTLY_BULLISH"}
BEARISH_SIGNALS = {"STRONG_BEARISH", "BEARISH", "SLIGHTLY_BEARISH"}

CREATE_USER_POSITIONS_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS user_positions (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(50) NOT NULL,
    position_type VARCHAR(20),
    entry_date DATE,
    entry_price DOUBLE PRECISION,
    quantity DOUBLE PRECISION,
    status VARCHAR(20),
    exit_date DATE,
    exit_price DOUBLE PRECISION,
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
"""

CREATE_POSITION_SUMMARY_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS position_summary (
    user_position_id INTEGER,
    asset VARCHAR(50),
    position_type VARCHAR(20),
    entry_date DATE,
    entry_price DOUBLE PRECISION,
    quantity DOUBLE PRECISION,
    status VARCHAR(20),
    exit_date DATE,
    exit_price DOUBLE PRECISION,
    notes TEXT,
    current_price DOUBLE PRECISION,
    price_timestamp TIMESTAMP,
    invested_amount DOUBLE PRECISION,
    current_value DOUBLE PRECISION,
    unrealized_pnl DOUBLE PRECISION,
    unrealized_pnl_percent DOUBLE PRECISION,
    realized_pnl DOUBLE PRECISION,
    current_signal VARCHAR(100),
    signal_category VARCHAR(30),
    signal_source VARCHAR(100),
    suggested_action VARCHAR(100),
    created_at TIMESTAMP
);
"""

USER_POSITIONS_QUERY = """
SELECT
    id,
    asset,
    position_type,
    entry_date,
    entry_price,
    quantity,
    status,
    exit_date,
    exit_price,
    notes,
    created_at,
    updated_at
FROM user_positions
ORDER BY id;
"""

LATEST_MARKET_QUERY = """
WITH ranked_market AS (
    SELECT
        asset,
        price AS current_price,
        timestamp AS price_timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY asset
            ORDER BY timestamp DESC
        ) AS row_num
    FROM market_data
)
SELECT
    asset,
    current_price,
    price_timestamp
FROM ranked_market
WHERE row_num = 1;
"""

LATEST_COMBINED_QUERY = """
WITH ranked_intelligence AS (
    SELECT
        asset,
        combined_signal,
        combined_confidence,
        market_signal,
        price_date,
        ROW_NUMBER() OVER (
            PARTITION BY asset
            ORDER BY price_date DESC, created_at DESC
        ) AS row_num
    FROM combined_intelligence_signals
)
SELECT
    asset,
    combined_signal,
    combined_confidence,
    market_signal,
    price_date
FROM ranked_intelligence
WHERE row_num = 1;
"""

LATEST_MODEL_QUERY = """
WITH ranked_predictions AS (
    SELECT
        asset,
        predicted_direction,
        prediction_probability,
        model_name,
        price_date,
        ROW_NUMBER() OVER (
            PARTITION BY asset
            ORDER BY price_date DESC, created_at DESC
        ) AS row_num
    FROM model_predictions
)
SELECT
    asset,
    predicted_direction,
    prediction_probability,
    model_name,
    price_date
FROM ranked_predictions
WHERE row_num = 1;
"""


def ensure_tables():
    with engine.begin() as conn:
        conn.execute(text(CREATE_USER_POSITIONS_TABLE_QUERY))
        conn.execute(text(CREATE_POSITION_SUMMARY_TABLE_QUERY))


def read_optional(query):
    try:
        return pd.read_sql(query, engine)
    except Exception:
        return pd.DataFrame()


def normalize_position(row):
    position_type = str(row.get("position_type") or "BUY").upper()
    status = str(row.get("status") or "").upper()

    if not status:
        status = "WATCHING" if position_type == "WATCH" else "OPEN"

    return position_type, status


def signal_from_row(row):
    combined_signal = row.get("combined_signal")
    predicted_direction = row.get("predicted_direction")

    if pd.notna(combined_signal):
        combined_signal = str(combined_signal).upper()

        if combined_signal in BULLISH_SIGNALS:
            return f"GREEN / UP - {combined_signal}", "GREEN_UP", "combined_intelligence"
        if combined_signal in BEARISH_SIGNALS:
            return f"RED / DOWN - {combined_signal}", "RED_DOWN", "combined_intelligence"

        return f"YELLOW / MIXED - {combined_signal}", "YELLOW_MIXED", "combined_intelligence"

    if pd.notna(predicted_direction):
        if int(predicted_direction) == 1:
            return "GREEN / UP - MODEL_UP", "GREEN_UP", "model_predictions"

        return "RED / DOWN - MODEL_DOWN", "RED_DOWN", "model_predictions"

    return "YELLOW / MIXED - NO_SIGNAL", "YELLOW_MIXED", "none"


def suggested_action(status, signal_category):
    if status == "CLOSED":
        return "POSITION CLOSED"

    if status == "WATCHING":
        if signal_category == "GREEN_UP":
            return "WATCH FOR BUY OPPORTUNITY"
        if signal_category == "RED_DOWN":
            return "AVOID FOR NOW"

        return "WAIT"

    if status == "OPEN":
        if signal_category == "GREEN_UP":
            return "HOLD / CONTINUE"
        if signal_category == "RED_DOWN":
            return "REVIEW POSITION / RISK WARNING"

        return "HOLD CAREFULLY"

    return "WAIT"


def safe_number(value, default=0.0):
    if pd.isna(value):
        return default

    return float(value)


def build_summary_rows(positions_df, market_df, combined_df, model_df):
    market_by_asset = market_df.set_index("asset").to_dict("index") if not market_df.empty else {}
    combined_by_asset = combined_df.set_index("asset").to_dict("index") if not combined_df.empty else {}
    model_by_asset = model_df.set_index("asset").to_dict("index") if not model_df.empty else {}

    rows = []
    created_at = datetime.now()

    for _, position in positions_df.iterrows():
        asset = str(position["asset"]).upper().strip()
        position_type, status = normalize_position(position)

        market_row = market_by_asset.get(asset, {})
        signal_row = {}
        signal_row.update(model_by_asset.get(asset, {}))
        signal_row.update(combined_by_asset.get(asset, {}))

        current_price = market_row.get("current_price")
        price_timestamp = market_row.get("price_timestamp")
        entry_price = safe_number(position.get("entry_price"))
        quantity = safe_number(position.get("quantity"))
        exit_price = position.get("exit_price")

        invested_amount = entry_price * quantity
        current_value = safe_number(current_price) * quantity if pd.notna(current_price) else 0.0
        unrealized_pnl = current_value - invested_amount if status != "CLOSED" else 0.0
        unrealized_pnl_percent = (
            unrealized_pnl / invested_amount
            if invested_amount
            else 0.0
        )

        realized_pnl = None

        if status == "CLOSED" and pd.notna(exit_price):
            realized_pnl = (safe_number(exit_price) - entry_price) * quantity

        current_signal, signal_category, signal_source = signal_from_row(signal_row)
        action = suggested_action(status, signal_category)

        rows.append(
            {
                "user_position_id": int(position["id"]),
                "asset": asset,
                "position_type": position_type,
                "entry_date": position.get("entry_date"),
                "entry_price": entry_price,
                "quantity": quantity,
                "status": status,
                "exit_date": position.get("exit_date"),
                "exit_price": safe_number(exit_price) if pd.notna(exit_price) else None,
                "notes": position.get("notes"),
                "current_price": safe_number(current_price) if pd.notna(current_price) else None,
                "price_timestamp": price_timestamp,
                "invested_amount": invested_amount,
                "current_value": current_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_percent": unrealized_pnl_percent,
                "realized_pnl": realized_pnl,
                "current_signal": current_signal,
                "signal_category": signal_category,
                "signal_source": signal_source,
                "suggested_action": action,
                "created_at": created_at,
            }
        )

    return pd.DataFrame(rows)


def write_empty_summary():
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM position_summary;"))


def main():
    ensure_tables()

    positions_df = pd.read_sql(USER_POSITIONS_QUERY, engine)

    if positions_df.empty:
        write_empty_summary()
        print("No user positions found. Created/cleared position_summary.")
        print("Built 0 rows into position_summary.")
        return

    positions_df["asset"] = positions_df["asset"].astype(str).str.upper().str.strip()

    market_df = read_optional(LATEST_MARKET_QUERY)
    combined_df = read_optional(LATEST_COMBINED_QUERY)
    model_df = read_optional(LATEST_MODEL_QUERY)

    summary_df = build_summary_rows(
        positions_df,
        market_df,
        combined_df,
        model_df,
    )

    summary_df.to_sql(
        "position_summary",
        engine,
        if_exists="replace",
        index=False,
    )

    open_positions_df = summary_df[summary_df["status"] == "OPEN"]
    watchlist_df = summary_df[summary_df["status"] == "WATCHING"]

    total_invested = open_positions_df["invested_amount"].sum()
    current_value = open_positions_df["current_value"].sum()
    unrealized_pnl = open_positions_df["unrealized_pnl"].sum()
    unrealized_pnl_percent = unrealized_pnl / total_invested if total_invested else 0.0

    print(f"Built {len(summary_df)} rows into position_summary.")
    print()
    print("Portfolio metrics:")
    print(f"Total invested: {total_invested:,.2f}")
    print(f"Current value: {current_value:,.2f}")
    print(f"Total unrealized P&L: {unrealized_pnl:,.2f}")
    print(f"Total unrealized P&L %: {unrealized_pnl_percent:.2%}")
    print(f"Open positions: {len(open_positions_df)}")
    print(f"Watchlist items: {len(watchlist_df)}")
    print()
    print("Position summary:")
    print(
        summary_df[
            [
                "asset",
                "status",
                "entry_price",
                "current_price",
                "quantity",
                "unrealized_pnl",
                "unrealized_pnl_percent",
                "current_signal",
                "suggested_action",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
