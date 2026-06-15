import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
from config.database import engine


def combine_signal(row):
    rule_signal = row["market_signal"]
    rule_confidence = row["confidence"]
    sentiment_label = row["sentiment_label"]

    if pd.isna(sentiment_label):
        sentiment_label = "UNKNOWN"

    if rule_signal == "INSUFFICIENT_DATA":
        return pd.Series(
            {
                "combined_signal": "INSUFFICIENT_DATA",
                "combined_confidence": "LOW",
                "intelligence_summary": "Not enough market data to create a combined signal."
            }
        )

    if rule_signal == "BULLISH" and sentiment_label == "POSITIVE":
        combined_signal = "STRONG_BULLISH"
        summary = "Market rules are bullish and news sentiment is positive."
    elif rule_signal == "BULLISH" and sentiment_label == "NEGATIVE":
        combined_signal = "MIXED"
        summary = "Market rules are bullish, but news sentiment is negative."
    elif rule_signal == "BULLISH":
        combined_signal = "BULLISH"
        summary = "Market rules are bullish, with no strong negative news confirmation."

    elif rule_signal == "BEARISH" and sentiment_label == "NEGATIVE":
        combined_signal = "STRONG_BEARISH"
        summary = "Market rules are bearish and news sentiment is negative."
    elif rule_signal == "BEARISH" and sentiment_label == "POSITIVE":
        combined_signal = "MIXED"
        summary = "Market rules are bearish, but news sentiment is positive."
    elif rule_signal == "BEARISH":
        combined_signal = "BEARISH"
        summary = "Market rules are bearish, with no strong positive news confirmation."

    elif rule_signal == "NEUTRAL" and sentiment_label == "POSITIVE":
        combined_signal = "SLIGHTLY_BULLISH"
        summary = "Market rules are neutral, but news sentiment is positive."
    elif rule_signal == "NEUTRAL" and sentiment_label == "NEGATIVE":
        combined_signal = "SLIGHTLY_BEARISH"
        summary = "Market rules are neutral, but news sentiment is negative."
    else:
        combined_signal = "NEUTRAL"
        summary = "Both market rules and news sentiment are neutral or unclear."

    if rule_confidence == "HIGH" and sentiment_label != "UNKNOWN":
        combined_confidence = "HIGH"
    elif rule_confidence in ["HIGH", "MEDIUM"]:
        combined_confidence = "MEDIUM"
    else:
        combined_confidence = "LOW"

    return pd.Series(
        {
            "combined_signal": combined_signal,
            "combined_confidence": combined_confidence,
            "intelligence_summary": summary
        }
    )


query = """
WITH latest_sentiment AS (
    SELECT
        related_asset,
        sentiment_label,
        sentiment_score,
        title,
        source,
        published_at,
        ROW_NUMBER() OVER (
            PARTITION BY related_asset
            ORDER BY published_at DESC, created_at DESC
        ) AS row_num
    FROM news_sentiment
)
SELECT
    r.asset,
    r.price,
    r.price_date,
    r.market_signal,
    r.confidence,
    r.rule_score,
    r.reason,
    r.daily_return,
    r.weekly_return,
    r.momentum,
    r.volatility,
    r.macro_gdp,
    r.macro_cpi,
    r.macro_interest_rate,
    s.sentiment_label,
    s.sentiment_score,
    s.title AS headline,
    s.source AS news_source,
    s.published_at AS news_date
FROM rule_based_signals r
LEFT JOIN latest_sentiment s
    ON r.asset = s.related_asset
    AND s.row_num = 1
ORDER BY r.price_date DESC, r.asset;
"""

df = pd.read_sql(query, engine)

if df.empty:
    raise ValueError("No rule-based signals found. Run scripts/build_rule_based_signals.py first.")

combined_df = df.apply(combine_signal, axis=1)

final_df = pd.concat(
    [
        df,
        combined_df
    ],
    axis=1
)

final_df["created_at"] = datetime.now()

final_df.to_sql(
    "combined_intelligence_signals",
    engine,
    if_exists="replace",
    index=False
)

latest_df = (
    final_df
    .sort_values(["asset", "price_date"], ascending=[True, False])
    .groupby("asset")
    .head(1)
)

print(f"Built {len(final_df)} combined intelligence rows into combined_intelligence_signals.")
print()
print(
    latest_df[
        [
            "asset",
            "price_date",
            "market_signal",
            "sentiment_label",
            "combined_signal",
            "combined_confidence",
            "intelligence_summary"
        ]
    ]
)
