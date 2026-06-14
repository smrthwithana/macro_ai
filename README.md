# Macro AI

Macro AI is a Python data project that collects financial market data and macroeconomic indicators, stores them in PostgreSQL, and presents the latest values in a Streamlit dashboard.

The project currently supports market ingestion from `yfinance`, real macroeconomic ingestion from the FRED API, PostgreSQL-backed read scripts, and a browser dashboard for monitoring market and macro data.

## Architecture

```text
External Data Sources
    |
    |-- yfinance
    |      |-- SP500
    |      |-- NASDAQ
    |      |-- GOLD
    |      |-- OIL
    |      |-- EURUSD
    |      |-- USDINR
    |
    |-- FRED API
           |-- USA GDP
           |-- USA CPI
           |-- USA INTEREST_RATE

Python Ingestion Layer
    |
    |-- ingestion/market_ingestor.py
    |-- ingestion/macro_ingestor.py
    |-- ingestion/fred_client.py
    |-- ingestion/run_daily.py
    |-- ingestion/run_fred_macro_daily.py

PostgreSQL Database
    |
    |-- market_data
    |-- macro_data

Analysis and Display Layer
    |
    |-- scripts/read_market_data.py
    |-- scripts/read_macro_data.py
    |-- scripts/show_macro_summary.py
    |-- dashboard/app.py

Streamlit Dashboard
    |
    |-- latest market data
    |-- latest macro data
    |-- market chart
    |-- database summary
```

## Features

- Market data ingestion for `SP500`, `NASDAQ`, `GOLD`, `OIL`, `EURUSD`, and `USDINR`.
- Real macroeconomic data ingestion from FRED.
- PostgreSQL storage for market and macro data.
- Duplicate protection for market ingestion and real FRED macro ingestion.
- Environment-based configuration through a private `.env` file.
- Safe `.env.example` template for GitHub.
- Read scripts for checking market rows, macro rows, latest assets, and macro summaries.
- Streamlit dashboard with:
  - database summary metrics
  - latest market metrics
  - latest macroeconomic metrics
  - asset selector
  - macro indicator selector
  - market price chart
  - sidebar refresh confirmation

## Tech Stack

- Python
- PostgreSQL
- SQLAlchemy
- pandas
- yfinance
- FRED API
- requests
- Streamlit
- Git and GitHub

## Setup Instructions

1. Clone the repository.

```powershell
git clone https://github.com/smrthwithana/macro_ai.git
cd macro_ai
```

2. Create and activate a virtual environment.

```powershell
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies.

```powershell
pip install -r requirements.txt
```

4. Create a local `.env` file from the example.

```powershell
copy .env.example .env
```

5. Update `.env` with your local PostgreSQL password and FRED API key.

```text
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=macro_ai

ECONOMIC_API_PROVIDER=FRED
FRED_API_KEY=your_fred_api_key
FRED_BASE_URL=https://api.stlouisfed.org/fred
```

Important: keep `.env` private. GitHub should only contain `.env.example`.

6. Create database tables.

```powershell
python database\create_tables.py
```

7. Test the database connection.

```powershell
python database\db_connect.py
```

8. Run market ingestion.

```powershell
python ingestion\run_daily.py
```

9. Run real FRED macro ingestion.

```powershell
python ingestion\run_fred_macro_daily.py
```

10. Check summaries.

```powershell
python scripts\show_assets.py
python scripts\show_macro_summary.py
```

11. Run the dashboard.

```powershell
streamlit run dashboard\app.py
```

Open the local dashboard at:

```text
http://localhost:8501
```

## Screenshots

Add dashboard screenshots here as the UI evolves.

Suggested screenshot path:

```text
docs/screenshots/dashboard.png
```

Example Markdown:

```markdown
![Macro AI Dashboard](docs/screenshots/dashboard.png)
```

## What This Project Demonstrates

- Building a Python data ingestion pipeline.
- Connecting Python applications to PostgreSQL with SQLAlchemy.
- Separating private configuration from committed source code.
- Working with market APIs and real economic APIs.
- Designing database tables for time-series style data.
- Creating reusable scripts for validation and operational checks.
- Building a Streamlit dashboard from PostgreSQL data.
- Managing a project through staged phases and GitHub commits.

## Future Roadmap

- Add more FRED indicators and countries.
- Add scheduled ingestion jobs.
- Add better duplicate handling for all macro sources.
- Store ingestion run metadata and errors.
- Improve dashboard filtering and chart controls.
- Add multi-asset comparison charts.
- Add macro trend charts over time.
- Add automated tests for database and ingestion functions.
- Add deployment instructions for the dashboard.
- Add documentation screenshots.
