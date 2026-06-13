import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from config.database import engine
from ingestion.fred_client import FredClient
from ingestion.macro_ingestor import ingest_macro_indicator


FRED_MACRO_SERIES = [
    {
        "country": "USA",
        "indicator": "GDP",
        "series_id": "GDP",
    },
    {
        "country": "USA",
        "indicator": "CPI",
        "series_id": "CPIAUCSL",
    },
    {
        "country": "USA",
        "indicator": "INTEREST_RATE",
        "series_id": "FEDFUNDS",
    },
]


def macro_record_exists(country, indicator, record_date, source):
    with engine.connect() as conn:
        return conn.execute(
            text("""
            SELECT COUNT(*)
            FROM macro_data
            WHERE country = :country
            AND indicator = :indicator
            AND record_date = :record_date
            AND source = :source
            """),
            {
                "country": country,
                "indicator": indicator,
                "record_date": record_date,
                "source": source,
            },
        ).scalar() > 0


def ingest_latest_fred_indicator(client, series_config):
    observation = client.get_latest_observation(series_config["series_id"])
    source = f"FRED:{observation.series_id}"

    if macro_record_exists(
        country=series_config["country"],
        indicator=series_config["indicator"],
        record_date=observation.record_date,
        source=source,
    ):
        print(
            "Duplicate skipped "
            f"{series_config['country']} {series_config['indicator']} "
            f"{observation.record_date}"
        )
        return "skipped"

    ingest_macro_indicator(
        country=series_config["country"],
        indicator=series_config["indicator"],
        value=observation.value,
        record_date=observation.record_date,
        source=source,
    )
    print(
        "Inserted real API data "
        f"{series_config['country']} {series_config['indicator']} "
        f"{observation.value} on {observation.record_date}"
    )
    return "inserted"


def main():
    try:
        client = FredClient()
    except RuntimeError as exc:
        print(exc)
        return 1

    inserted = 0
    skipped = 0
    errors = 0

    for series_config in FRED_MACRO_SERIES:
        try:
            result = ingest_latest_fred_indicator(client, series_config)
        except Exception as exc:
            errors += 1
            print(f"Error loading {series_config['indicator']}: {exc}")
            continue

        if result == "inserted":
            inserted += 1
        elif result == "skipped":
            skipped += 1

    print(f"FRED macro ingestion complete. Inserted: {inserted}. Skipped: {skipped}. Errors: {errors}.")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
