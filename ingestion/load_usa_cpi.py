from ingestion.macro_ingestor import ingest_macro_indicator

ingest_macro_indicator(
    country="USA",
    indicator="CPI",
    value=3.1,
    record_date="2026-01-01",
    source="MANUAL_TEST"
)