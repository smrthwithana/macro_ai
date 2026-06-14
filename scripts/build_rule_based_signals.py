import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
from config.database import engine


def value_exists(value):
    return pd.notna(value)


def build_signal(row):
    score = 0
    reasons = []
    price_feature_count = 0

    daily_return = row["daily_return"]
    weekly_return = row["weekly_return"]
    momentum = row["momentum"]
    volatility = row["volatility"]
    interest_rate = row["macro_interest_rate"]

    if value_exists(daily_return):
        price_feature_count += 1

        if daily_return > 0:
            score += 1
            reasons.append("Daily return is positive")
        elif daily_return < 0:
            score -= 1
            reasons.append("Daily return is negative")
        else:
            reasons.append("Daily return is flat")

    if value_exists(weekly_return):
        price_feature_count += 1

        if weekly_return > 0:
            score += 1
            reasons.append("Weekly return is positive")
        elif weekly_return < 0:
            score -= 1
            reasons.append("Weekly return is negative")
        else:
            reasons.append("Weekly return is flat")

    if value_exists(momentum):
        price_feature_count += 1

        if momentum > 0:
            score += 1
            reasons.append("Momentum is positive")
        elif momentum < 0:
            score -= 1
            reasons.append("Momentum is negative")
        else:
            reasons.append("Momentum is neutral")

    if value_exists(volatility):
        price_feature_count += 1

        if volatility > 0.03:
            score -= 1
            reasons.append("Volatility is elevated")
        else:
            reasons.append("Volatility is normal")

    if value_exists(interest_rate):
        if interest_rate >= 5:
            score -= 1
            reasons.append("Interest rate is restrictive")
        elif interest_rate <= 2:
            score += 1
            reasons.append("Interest rate is supportive")
        else:
            reasons.append("Interest rate is neutral")

    if price_feature_count == 0:
        signal = "INSUFFICIENT_DATA"
        confidence = "LOW"
        reasons.append("Not enough market history to calculate signal")
    elif score > 0:
        signal = "BULLISH"
    elif score < 0:
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"

    if price_feature_count >= 3:
        confidence = "HIGH"
    elif price_feature_count == 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    if signal == "INSUFFICIENT_DATA":
        confidence = "LOW"

    return pd.Series(
        {
            "rule_score": score,
            "market_signal": signal,
            "confidence": confidence,
            "reason": "; ".join(reasons)
        }
    )


query = """
SELECT
    asset,
    price,
    daily_return,
    weekly_return,
    momentum,
    volatility,
    macro_gdp,
    macro_cpi,
    macro_interest_rate,
    price_date
FROM market_signals
ORDER BY price_date DESC, asset;
"""

market_signals_df = pd.read_sql(query, engine)

if market_signals_df.empty:
    raise ValueError("market_signals table is empty. Run scripts/build_market_signals.py first.")

rule_results_df = market_signals_df.apply(build_signal, axis=1)

final_df = pd.concat(
    [
        market_signals_df,
        rule_results_df
    ],
    axis=1
)

final_df["created_at"] = datetime.now()

final_df.to_sql(
    "rule_based_signals",
    engine,
    if_exists="replace",
    index=False
)

print(f"Built {len(final_df)} rule-based signal rows into rule_based_signals.")
print()
print(
    final_df[
        [
            "asset",
            "price_date",
            "market_signal",
            "confidence",
            "rule_score",
            "reason"
        ]
    ]
)
