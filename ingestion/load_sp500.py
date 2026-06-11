import yfinance as yf
from sqlalchemy import create_engine, text
from datetime import datetime

DB_USER = "postgres"
DB_PASSWORD = "12345"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "macro_ai"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

sp500 = yf.Ticker("^GSPC")

price = sp500.history(period="1d")["Close"].iloc[-1]

with engine.connect() as conn:
    conn.execute(
        text("""
        INSERT INTO market_data(asset, price, timestamp)
        VALUES (:asset, :price, :timestamp)
        """),
        {
            "asset": "SP500",
            "price": float(price),
            "timestamp": datetime.now()
        }
    )
    conn.commit()

print(f"Inserted SP500 price: {price}")