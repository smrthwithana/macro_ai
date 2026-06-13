import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.market_ingestor import ingest_market_asset

assets = [
    ("^GSPC", "SP500"),
    ("^IXIC", "NASDAQ"),
    ("GC=F", "GOLD"),
    ("CL=F", "OIL"),
    ("EURUSD=X", "EURUSD"),
    ("INR=X", "USDINR")
]

for symbol, asset_name in assets:
    try:
        ingest_market_asset(symbol, asset_name)
    except Exception as e:
        print(f"Error loading {asset_name}: {e}")
