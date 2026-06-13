import sys
from pathlib import Path

from sqlalchemy import text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.database import engine

create_market_table = """
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(50),
    price FLOAT,
    timestamp TIMESTAMP
);
"""

create_macro_table = """
CREATE TABLE IF NOT EXISTS macro_data (
    id SERIAL PRIMARY KEY,
    country VARCHAR(50),
    indicator VARCHAR(100),
    value DOUBLE PRECISION,
    record_date DATE,
    source VARCHAR(100),
    timestamp TIMESTAMP
);
"""

with engine.connect() as conn:
    conn.execute(text(create_market_table))
    conn.execute(text(create_macro_table))
    conn.commit()

print("Tables created successfully!")
