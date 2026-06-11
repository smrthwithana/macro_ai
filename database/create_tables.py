from sqlalchemy import create_engine, text

DB_USER = "postgres"
DB_PASSWORD = "12345"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "macro_ai"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

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
    value FLOAT,
    date DATE
);
"""

with engine.connect() as conn:
    conn.execute(text(create_market_table))
    conn.execute(text(create_macro_table))
    conn.commit()

print("Tables created successfully!")