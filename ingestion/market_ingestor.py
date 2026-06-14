import yfinance as yf
from sqlalchemy import text
from datetime import datetime

from config.database import engine
from utils.logger import logger


def ingest_market_asset(symbol, asset_name):

    ticker = yf.Ticker(symbol)

    history = ticker.history(period="5d")

    if history.empty or "Close" not in history.columns:
        print(f"No latest market data available for {asset_name}")
        logger.warning(f"No latest market data available for {asset_name}")
        return

    close_prices = history["Close"].dropna()

    if close_prices.empty:
        print(f"No valid close price available for {asset_name}")
        logger.warning(f"No valid close price available for {asset_name}")
        return

    price = close_prices.iloc[-1]

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
