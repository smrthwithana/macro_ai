from urllib.parse import quote_plus

from sqlalchemy import create_engine

from config.settings import (
    DATABASE_URL as ENV_DATABASE_URL,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)


def _build_database_url():
    if ENV_DATABASE_URL:
        return ENV_DATABASE_URL

    password = quote_plus(DB_PASSWORD)
    return f"postgresql://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


DATABASE_URL = _build_database_url()
engine = create_engine(DATABASE_URL)
