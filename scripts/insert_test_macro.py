from sqlalchemy import text
from config.database import engine

with engine.connect() as conn:
    conn.execute(
        text("""
        INSERT INTO macro_data (
            country,
            indicator,
            value,
            record_date,
            source,
            timestamp
        )
        VALUES (
            :country,
            :indicator,
            :value,
            :record_date,
            :source,
            NOW()
        )
        """),
        {
            "country": "USA",
            "indicator": "GDP",
            "value": 2.8,
            "record_date": "2026-01-01",
            "source": "MANUAL_TEST"
        }
    )

    conn.commit()

print("Macro record inserted!")