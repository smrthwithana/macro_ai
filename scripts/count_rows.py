from config.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM market_data"))
    count = result.scalar()

print("Rows:", count)