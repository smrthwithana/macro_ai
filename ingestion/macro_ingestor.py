from sqlalchemy import text
from config.database import engine
from datetime import datetime


def ingest_macro_indicator(
    country,
    indicator,
    value,
    record_date,
    source
):
    with engine.connect() as conn:

        conn.execute(
            text("""
            INSERT INTO macro_data(
                country,
                indicator,
                value,
                record_date,
                source,
                timestamp
            )
            VALUES(
                :country,
                :indicator,
                :value,
                :record_date,
                :source,
                :timestamp
            )
            """),
            {
                "country": country,
                "indicator": indicator,
                "value": value,
                "record_date": record_date,
                "source": source,
                "timestamp": datetime.now()
            }
        )

        conn.commit()

    print(f"Inserted {country} {indicator}")