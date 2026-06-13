import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.database import engine


query = """
WITH ranked_macro AS (
    SELECT
        country,
        indicator,
        value,
        record_date,
        source,
        timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY country, indicator
            ORDER BY record_date DESC, timestamp DESC
        ) AS row_num
    FROM macro_data
)
SELECT
    country,
    indicator,
    value,
    record_date,
    source
FROM ranked_macro
WHERE row_num = 1
ORDER BY country, indicator;
"""


def format_value(value):
    if pd.isna(value):
        return "n/a"

    return f"{float(value):,.4f}".rstrip("0").rstrip(".")


df = pd.read_sql(query, engine)

if df.empty:
    print("No macro data found.")
else:
    for row in df.itertuples(index=False):
        label = f"{row.country} {row.indicator}"
        print(
            f"{label:<18} "
            f"{format_value(row.value):>14}   "
            f"{row.record_date}   "
            f"{row.source}"
        )
