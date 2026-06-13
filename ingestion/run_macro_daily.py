from ingestion.macro_ingestor import ingest_macro_indicator

ingest_macro_indicator(
    country="USA",
    indicator="GDP",
    value=2.8,
    record_date="2026-01-01",
    source="MANUAL_TEST"
)

ingest_macro_indicator(
    country="USA",
    indicator="CPI",
    value=3.1,
    record_date="2026-01-01",
    source="MANUAL_TEST"
)

ingest_macro_indicator(
    country="USA",
    indicator="INTEREST_RATE",
    value=4.5,
    record_date="2026-01-01",
    source="MANUAL_TEST"
)