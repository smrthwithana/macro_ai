from config.database import engine
import pandas as pd

query = """
SELECT *
FROM market_data
ORDER BY timestamp DESC
LIMIT 5;
"""

df = pd.read_sql(query, engine)

print(df)
print(df.dtypes)