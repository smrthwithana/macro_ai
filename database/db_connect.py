import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.database import engine

try:
    connection = engine.connect()
    print("Database connection successful!")
    connection.close()

except Exception as e:
    print("Connection failed:")
    print(e)
