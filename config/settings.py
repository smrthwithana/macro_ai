import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / ".env"


def _load_env_file(path=ENV_PATH):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


def get_env(name, default=None, required=False):
    value = os.getenv(name, default)

    if required and not value:
        raise RuntimeError(
            f"{name} is not set. Add it to {ENV_PATH} before running ingestion scripts."
        )

    return value


_load_env_file()

DATABASE_URL = get_env("DATABASE_URL")

DB_USER = get_env("DB_USER", "postgres")
DB_PASSWORD = get_env("DB_PASSWORD", required=not DATABASE_URL)
DB_HOST = get_env("DB_HOST", "localhost")
DB_PORT = get_env("DB_PORT", "5432")
DB_NAME = get_env("DB_NAME", "macro_ai")

ECONOMIC_API_PROVIDER = get_env("ECONOMIC_API_PROVIDER", "FRED")
FRED_API_KEY = get_env("FRED_API_KEY", "")
FRED_BASE_URL = get_env("FRED_BASE_URL", "https://api.stlouisfed.org/fred")
