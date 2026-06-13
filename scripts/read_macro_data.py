import pandas as pd
from config.database import engine

df = pd.read_sql(
    "SELECT * FROM macro_data",
    engine
)

print(df)
print()
print(df.dtypes)