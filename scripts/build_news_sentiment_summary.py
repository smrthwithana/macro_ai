import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
from config.database import engine


RECENT_NEWS_DAYS = 14

NEWS_QUERY = """
SELECT
    related_asset,
    sentiment_label,
    sentiment_score,
    title,
    source,
    published_at,
    created_at
FROM news_sentiment
WHERE related_asset IS NOT NULL
ORDER BY related_asset, published_at, created_at;
"""


def dominant_sentiment(group_df):
    label_counts = group_df["sentiment_label"].value_counts()
    top_count = label_counts.max()
    top_labels = label_counts[label_counts == top_count].index.tolist()

    if len(top_labels) == 1:
        return top_labels[0]

    average_score = group_df["sentiment_score"].mean()

    if average_score > 0:
        return "POSITIVE"
    if average_score < 0:
        return "NEGATIVE"

    return "NEUTRAL"


def build_summary(news_df):
    news_df = news_df.copy()
    news_df["published_at"] = pd.to_datetime(news_df["published_at"])
    news_df["created_at"] = pd.to_datetime(news_df["created_at"])
    news_df["sentiment_score"] = news_df["sentiment_score"].fillna(0)
    news_df["sentiment_label"] = news_df["sentiment_label"].fillna("NEUTRAL")

    latest_news_date = news_df["published_at"].max()
    recent_start_date = latest_news_date - timedelta(days=RECENT_NEWS_DAYS)
    recent_news_df = news_df[news_df["published_at"] >= recent_start_date].copy()

    if recent_news_df.empty:
        recent_news_df = news_df.copy()

    summary_rows = []
    created_at = datetime.now()

    for asset, asset_df in recent_news_df.groupby("related_asset"):
        sorted_asset_df = asset_df.sort_values(
            ["published_at", "created_at"],
            ascending=[False, False],
        )
        latest_row = sorted_asset_df.iloc[0]

        summary_rows.append(
            {
                "related_asset": asset,
                "recent_window_days": RECENT_NEWS_DAYS,
                "headline_count": len(asset_df),
                "average_sentiment_score": asset_df["sentiment_score"].mean(),
                "positive_count": int((asset_df["sentiment_label"] == "POSITIVE").sum()),
                "negative_count": int((asset_df["sentiment_label"] == "NEGATIVE").sum()),
                "neutral_count": int((asset_df["sentiment_label"] == "NEUTRAL").sum()),
                "dominant_sentiment_label": dominant_sentiment(asset_df),
                "latest_headline": latest_row["title"],
                "latest_source": latest_row["source"],
                "latest_published_date": latest_row["published_at"].date(),
                "created_at": created_at,
            }
        )

    return pd.DataFrame(summary_rows).sort_values("related_asset")


def main():
    news_df = pd.read_sql(NEWS_QUERY, engine)

    if news_df.empty:
        raise ValueError("news_sentiment table is empty. Run scripts.fetch_real_news_sentiment first.")

    summary_df = build_summary(news_df)

    summary_df.to_sql(
        "news_sentiment_summary",
        engine,
        if_exists="replace",
        index=False,
    )

    print(f"Built {len(summary_df)} rows into news_sentiment_summary.")
    print()
    print("News sentiment summary:")
    print(
        summary_df[
            [
                "related_asset",
                "headline_count",
                "average_sentiment_score",
                "positive_count",
                "negative_count",
                "neutral_count",
                "dominant_sentiment_label",
                "latest_source",
                "latest_published_date",
            ]
        ].to_string(index=False)
    )
    print()
    print("Latest summarized headlines:")
    print(
        summary_df[
            [
                "related_asset",
                "latest_source",
                "latest_published_date",
                "latest_headline",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
