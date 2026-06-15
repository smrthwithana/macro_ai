import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
from config.database import engine


query = """
SELECT
    asset,
    price_date,
    price,
    daily_return,
    weekly_return,
    momentum,
    volatility,
    macro_gdp,
    macro_cpi,
    macro_interest_rate,
    sentiment_score,
    rule_score,
    market_signal,
    confidence,
    combined_signal,
    combined_confidence
FROM combined_intelligence_signals
ORDER BY asset, price_date;
"""

df = pd.read_sql(query, engine)

if df.empty:
    raise ValueError("combined_intelligence_signals table is empty. Run scripts.build_combined_intelligence first.")

df["price_date"] = pd.to_datetime(df["price_date"])
df = df.sort_values(["asset", "price_date"])

df["next_price"] = df.groupby("asset")["price"].shift(-1)
df["next_price_date"] = df.groupby("asset")["price_date"].shift(-1)

df["target_next_return"] = (df["next_price"] - df["price"]) / df["price"]

df["target_direction"] = df["target_next_return"].apply(
    lambda value: 1 if pd.notna(value) and value > 0 else 0 if pd.notna(value) else None
)

df["sentiment_score"] = df["sentiment_score"].fillna(0)
df["rule_score"] = df["rule_score"].fillna(0)

df["daily_return"] = df["daily_return"].fillna(0)
df["weekly_return"] = df["weekly_return"].fillna(0)
df["momentum"] = df["momentum"].fillna(0)
df["volatility"] = df["volatility"].fillna(0)

df["macro_gdp"] = df["macro_gdp"].ffill().bfill()
df["macro_cpi"] = df["macro_cpi"].ffill().bfill()
df["macro_interest_rate"] = df["macro_interest_rate"].ffill().bfill()

df["created_at"] = datetime.now()

model_df = df.dropna(
    subset=[
        "next_price",
        "target_next_return",
        "target_direction"
    ]
).copy()

model_df["target_direction"] = model_df["target_direction"].astype(int)

model_df.to_sql(
    "model_dataset",
    engine,
    if_exists="replace",
    index=False
)

print(f"Built {len(model_df)} rows into model_dataset.")
print()
print(
    model_df[
        [
            "asset",
            "price_date",
            "price",
            "next_price_date",
            "next_price",
            "target_next_return",
            "target_direction"
        ]
    ].tail(20)
)

print()
print("Target distribution:")
print(model_df["target_direction"].value_counts())
