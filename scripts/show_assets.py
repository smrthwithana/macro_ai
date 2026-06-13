import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.database import engine
import pandas as pd

query = """
SELECT asset, price, timestamp
FROM market_data
ORDER BY timestamp DESC;
"""

df = pd.read_sql(query, engine)

print(df)
