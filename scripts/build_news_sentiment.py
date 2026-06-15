import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from sqlalchemy import text
from config.database import engine

positive_words = [
    "growth",
    "strong",
    "rally",
    "gain",
    "gains",
    "positive",
    "eases",
    "cooling",
    "recovery",
    "optimism",
    "bullish",
    "surge",
    "improves"
]

negative_words = [
    "fall",
    "falls",
    "weak",
    "risk",
    "risks",
    "inflation",
    "recession",
    "slowdown",
    "pressure",
    "war",
    "crisis",
    "bearish",
    "decline",
    "declines",
    "fear"
]

sample_news = [
    {
        "source": "SAMPLE",
        "title": "US stocks rally as inflation pressure eases",
        "related_asset": "SP500",
        "published_at": "2026-06-15"
    },
    {
        "source": "SAMPLE",
        "title": "Oil prices fall as demand slowdown fears increase",
        "related_asset": "OIL",
        "published_at": "2026-06-15"
    },
    {
        "source": "SAMPLE",
        "title": "Gold gains as investors watch interest rate risks",
        "related_asset": "GOLD",
        "published_at": "2026-06-15"
    },
    {
        "source": "SAMPLE",
        "title": "Dollar strength puts pressure on emerging market currencies",
        "related_asset": "USDINR",
        "published_at": "2026-06-15"
    },
    {
        "source": "SAMPLE",
        "title": "Technology shares show strong momentum after market recovery",
        "related_asset": "NASDAQ",
        "published_at": "2026-06-15"
    }
]


def score_headline(title):
    title_lower = title.lower()

    positive_score = sum(1 for word in positive_words if word in title_lower)
    negative_score = sum(1 for word in negative_words if word in title_lower)

    score = positive_score - negative_score

    if score > 0:
        label = "POSITIVE"
    elif score < 0:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"

    return score, label


create_table_query = """
CREATE TABLE IF NOT EXISTS news_sentiment (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100),
    title TEXT,
    related_asset VARCHAR(50),
    sentiment_score INTEGER,
    sentiment_label VARCHAR(20),
    published_at DATE,
    created_at TIMESTAMP
);
"""

with engine.connect() as conn:
    conn.execute(text(create_table_query))

    inserted = 0
    skipped = 0

    for item in sample_news:
        score, label = score_headline(item["title"])

        existing = conn.execute(
            text("""
            SELECT COUNT(*)
            FROM news_sentiment
            WHERE title = :title
            AND published_at = :published_at
            """),
            {
                "title": item["title"],
                "published_at": item["published_at"]
            }
        ).scalar()

        if existing == 0:
            conn.execute(
                text("""
                INSERT INTO news_sentiment (
                    source,
                    title,
                    related_asset,
                    sentiment_score,
                    sentiment_label,
                    published_at,
                    created_at
                )
                VALUES (
                    :source,
                    :title,
                    :related_asset,
                    :sentiment_score,
                    :sentiment_label,
                    :published_at,
                    :created_at
                )
                """),
                {
                    "source": item["source"],
                    "title": item["title"],
                    "related_asset": item["related_asset"],
                    "sentiment_score": score,
                    "sentiment_label": label,
                    "published_at": item["published_at"],
                    "created_at": datetime.now()
                }
            )

            inserted += 1
        else:
            skipped += 1

    conn.commit()

print(f"News sentiment build complete. Inserted: {inserted}. Skipped: {skipped}.")
