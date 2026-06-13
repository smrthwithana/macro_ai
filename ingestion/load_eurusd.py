import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.market_ingestor import ingest_market_asset

ingest_market_asset("EURUSD=X", "EURUSD")
