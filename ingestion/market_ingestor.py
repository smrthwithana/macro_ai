import yfinance as yf
from sqlalchemy import text
from datetime import datetime

from config.database import engine
from utils.logger import logger


def ingest_market_asset(symbol, asset_name):

    ticker = yf.Ticker(symbol)

    price = ticker.history(period="1d")["Close"].iloc[-1]

    with engine.connect() as conn:

        existing = conn.execute(
            text("""
            SELECT COUNT(*)
            FROM market_data
            WHERE asset = :asset
            AND price = :price
            """),
            {
                "asset": asset_name,
                "price": float(price)
            }
        ).scalar()

        if existing == 0:

            conn.execute(
                text("""
                INSERT INTO market_data(asset, price, timestamp)
                VALUES (:asset, :price, :timestamp)
                """),
                {
                    "asset": asset_name,
                    "price": float(price),
                    "timestamp": datetime.now()
                }
            )

            conn.commit()

            logger.info(f"{asset_name} inserted")

            print(f"Inserted {asset_name}: {price}")

        else:

            logger.info(f"{asset_name} duplicate skipped")

            print(f"Duplicate detected for {asset_name}")