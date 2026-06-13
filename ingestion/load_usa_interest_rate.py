from ingestion.macro_ingestor import ingest_macro_indicator

ingest_macro_indicator(
    country="USA",
    indicator="INTEREST_RATE",
    value=4.5,
    record_date="2026-01-01",
    source="MANUAL_TEST"
)