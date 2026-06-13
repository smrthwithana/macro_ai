import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.macro_ingestor import ingest_macro_indicator

ingest_macro_indicator(
    country="USA",
    indicator="INTEREST_RATE",
    value=4.5,
    record_date="2026-01-01",
    source="MANUAL_TEST"
)
