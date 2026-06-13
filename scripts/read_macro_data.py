import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.database import engine

df = pd.read_sql(
    "SELECT * FROM macro_data",
    engine
)

print(df)
print()
print(df.dtypes)
