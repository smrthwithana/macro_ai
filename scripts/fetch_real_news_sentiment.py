import sys
from pathlib import Path
from datetime import datetime, timedelta

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import os
import requests
from sqlalchemy import text
from config.database import engine

ENV_PATH = ROOT_DIR / ".env"

if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

if not NEWS_API_KEY:
    raise ValueError("NEWS_API_KEY is missing. Add it to your local .env file.")

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
    "improves",
    "beats",
    "higher",
    "up"
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
    "fear",
    "lower",
    "down"
]

asset_queries = {
    "SP500": "S&P 500 OR US stocks OR Wall Street",
    "NASDAQ": "Nasdaq OR technology stocks",
    "GOLD": "gold price OR gold market",
    "OIL": "oil prices OR crude oil",
    "USDINR": "USD INR OR Indian rupee dollar",
    "EURUSD": "EUR USD OR euro dollar"
}


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


def fetch_news_for_asset(asset_name, query):
    from_date = (datetime.now() - timedelta(days=7)).date().isoformat()

    response = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": query,
            "from": from_date,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 5,
            "apiKey": NEWS_API_KEY,
        },
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    if payload.get("status") != "ok":
        raise RuntimeError(
            f"NewsAPI error for {asset_name}: {payload.get('code')} {payload.get('message')}"
        )

    return payload.get("articles", [])


def normalize_published_date(value):
    if not value:
        return datetime.now().date().isoformat()

    return value.split("T", 1)[0]


def create_news_sentiment_table(conn):
    conn.execute(
        text("""
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
        """)
    )


def remove_sample_rows_if_real_news_exists(conn):
    real_news_count = conn.execute(
        text("""
        SELECT COUNT(*)
        FROM news_sentiment
        WHERE source <> 'SAMPLE'
        """)
    ).scalar()

    if real_news_count == 0:
        return 0

    result = conn.execute(
        text("""
        DELETE FROM news_sentiment
        WHERE source = 'SAMPLE'
        """)
    )

    return result.rowcount or 0


def insert_article(conn, article, asset_name):
    title = article.get("title")

    if not title:
        return "skipped"

    published_at = normalize_published_date(article.get("publishedAt"))
    source = (article.get("source") or {}).get("name") or "NewsAPI"
    score, label = score_headline(title)

    existing = conn.execute(
        text("""
        SELECT COUNT(*)
        FROM news_sentiment
        WHERE title = :title
        AND published_at = :published_at
        """),
        {
            "title": title,
            "published_at": published_at,
        },
    ).scalar()

    if existing:
        return "skipped"

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
            "source": source,
            "title": title,
            "related_asset": asset_name,
            "sentiment_score": score,
            "sentiment_label": label,
            "published_at": published_at,
            "created_at": datetime.now(),
        },
    )

    return "inserted"


def main():
    total_inserted = 0
    total_skipped = 0
    total_errors = 0

    with engine.begin() as conn:
        create_news_sentiment_table(conn)

        for asset_name, query in asset_queries.items():
            try:
                articles = fetch_news_for_asset(asset_name, query)
            except Exception as exc:
                total_errors += 1
                print(f"{asset_name}: error={exc}")
                continue

            asset_inserted = 0
            asset_skipped = 0

            for article in articles:
                result = insert_article(conn, article, asset_name)

                if result == "inserted":
                    asset_inserted += 1
                else:
                    asset_skipped += 1

            total_inserted += asset_inserted
            total_skipped += asset_skipped

            print(
                f"{asset_name}: fetched={len(articles)} "
                f"inserted={asset_inserted} skipped={asset_skipped}"
            )

        sample_rows_removed = remove_sample_rows_if_real_news_exists(conn)

        if sample_rows_removed:
            print(f"Removed {sample_rows_removed} sample news sentiment rows.")

    print(
        "Real news sentiment fetch complete. "
        f"Inserted: {total_inserted}. Skipped: {total_skipped}. Errors: {total_errors}."
    )

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
