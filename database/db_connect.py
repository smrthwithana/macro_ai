from sqlalchemy import create_engine

DB_USER = "postgres"
DB_PASSWORD = "12345"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "macro_ai"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

try:
    connection = engine.connect()
    print("Database connection successful!")
    connection.close()

except Exception as e:
    print("Connection failed:")
    print(e)