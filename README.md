# Macro AI

Macro AI is a Python and PostgreSQL project that turns market prices,
macroeconomic indicators, news sentiment, rule logic, machine learning
predictions, ratings, and backtesting into a single Streamlit intelligence
dashboard.

This is a research and learning project. It is not guaranteed financial advice
and should not be used as the sole basis for investment or trading decisions.

## Project Overview

The system collects:

- Market data from `yfinance`
- Macroeconomic data from FRED
- News headlines from NewsAPI

It then builds:

- Market return, momentum, and volatility features
- Rule-based bullish, bearish, and neutral signals
- Combined market intelligence using price, macro, and news context
- Machine learning direction predictions
- Prediction ratings and model reflections
- Backtest results for a simple prediction-based strategy

The final result is a local Streamlit dashboard backed by PostgreSQL.

## Architecture

```text
External data sources
    |
    |-- yfinance market data
    |-- FRED macroeconomic API
    |-- NewsAPI headlines
    |
Python ingestion scripts
    |
    |-- market ingestion
    |-- macro ingestion
    |-- news sentiment ingestion
    |
PostgreSQL database
    |
    |-- raw data tables
    |-- engineered feature tables
    |-- signal tables
    |-- ML prediction tables
    |-- rating and backtest tables
    |
Analytics layer
    |
    |-- market signals
    |-- rule-based signals
    |-- combined intelligence
    |-- model dataset
    |-- model comparison
    |-- prediction ratings
    |-- backtesting
    |
Streamlit dashboard
```

## Features Completed

- Market ingestion for `SP500`, `NASDAQ`, `GOLD`, `OIL`, `EURUSD`, and `USDINR`
- FRED macro ingestion for GDP, CPI, and interest rate data
- Real news sentiment ingestion with duplicate protection
- News sentiment summary by asset
- Market feature engineering:
  - daily returns
  - weekly returns
  - momentum
  - volatility
  - macro values joined to market data
- Rule-based market signals
- Combined market intelligence
- Machine learning model dataset
- Logistic regression baseline model
- Random forest comparison model
- Best-model prediction storage
- Prediction rating and reflection system
- Simple long/short backtesting engine
- Streamlit dashboard with all major outputs
- Windows `.bat` daily update script
- Master daily update command

## Tech Stack

- Python
- PostgreSQL
- SQLAlchemy
- pandas
- scikit-learn
- Streamlit
- yfinance
- FRED API
- NewsAPI
- requests
- Git and GitHub

## Database Tables

Main tables created by the pipeline:

- `market_data`
- `macro_data`
- `news_sentiment`
- `news_sentiment_summary`
- `market_signals`
- `rule_based_signals`
- `combined_intelligence_signals`
- `model_dataset`
- `model_predictions`
- `model_performance_summary`
- `prediction_ratings`
- `prediction_rating_summary`
- `backtest_results`
- `backtest_summary`

## Setup

Clone the repository:

```powershell
git clone https://github.com/smrthwithana/macro_ai.git
cd macro_ai
```

Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create your local `.env` file:

```powershell
copy .env.example .env
```

Fill in your local `.env` values. Keep this file private.

Expected keys:

```text
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
DB_NAME=
ECONOMIC_API_PROVIDER=
FRED_API_KEY=
FRED_BASE_URL=
NEWS_API_KEY=
```

Important: GitHub should contain `.env.example`, not `.env`.

Create database tables:

```powershell
python database\create_tables.py
```

Test the database connection:

```powershell
python database\db_connect.py
```

## Run the Daily Update

The full daily pipeline can be run with one command:

```powershell
python -m scripts.run_daily_update
```

The pipeline runs:

```text
market ingestion
FRED macro ingestion
real news sentiment fetch
market signal build
rule-based signal build
news sentiment summary build
combined intelligence build
model dataset build
model comparison training
prediction rating build
backtest result build
```

On Windows, Task Scheduler can run:

```powershell
run_daily_update.bat
```

Logs are written locally under `logs/`, which is ignored by Git.

## Run the Dashboard

Start Streamlit:

```powershell
streamlit run dashboard\app.py
```

Open:

```text
http://localhost:8501
```

Dashboard sections include:

- Database summary
- Latest market data
- Market price chart
- Latest macroeconomic data
- Market signals
- Rule-based market intelligence
- News sentiment
- News sentiment summary
- Combined market intelligence
- ML direction predictions
- Model comparison
- Prediction rating and model reflection
- Backtesting performance

## ML Model Explanation

The project builds a supervised learning dataset where each row contains
features available on a market date and a target for the next available market
date.

Features include:

- daily return
- weekly return
- momentum
- volatility
- GDP
- CPI
- interest rate
- sentiment score
- rule score
- asset identity

Target:

```text
1 = asset moved up on the next available market date
0 = asset moved down or stayed flat
```

The training script compares:

- `logistic_regression_v1`
- `random_forest_v1`

The best model is selected by accuracy, with F1 score as the tie-breaker. The
best model writes predictions to `model_predictions`.

## Prediction Rating Explanation

The rating system compares each predicted direction with the actual next-day
direction and assigns:

- prediction correctness
- confidence bucket
- 1 to 5 star rating
- model mood
- trust impact
- reflection message

Example moods:

- `CONFIDENT`
- `SATISFIED`
- `CAUTIOUS`
- `CONCERNED`
- `DISAPPOINTED`

The dashboard shows lifetime rating, recent rating, asset-wise rating, model
mood, trust status, and the latest reflection message.

## Backtesting Explanation

The backtesting engine simulates a simple strategy:

- predicted UP -> long trade
- predicted DOWN -> short trade

It calculates:

- actual next return
- strategy return
- win or loss
- cumulative return
- total trades
- win rate
- average trade return
- asset-wise performance

This backtest is intentionally simple and is used to evaluate the prediction
pipeline, not to recommend real trades.

## Screenshots

Suggested screenshot location:

```text
docs/screenshots/dashboard.png
```

Example:

```markdown
![Macro AI Dashboard](docs/screenshots/dashboard.png)
```

## What This Project Demonstrates

- API ingestion with Python
- PostgreSQL data modeling
- Environment-based configuration
- Feature engineering on time-series data
- Explainable rule-based intelligence
- Sentiment integration
- Supervised ML classification
- Model comparison
- Prediction evaluation and self-reflection
- Backtesting fundamentals
- Streamlit dashboard development
- Windows-friendly automation
- GitHub-based project delivery

## Limitations

- News sentiment uses a simple keyword-based approach.
- The ML model is a baseline classifier, not a production trading model.
- Backtesting does not include slippage, transaction costs, liquidity, or risk
  controls.
- Predictions are evaluated on historical test rows, not fully live forward
  predictions yet.
- The dashboard is designed for local research, not production deployment.

## Future Improvements

- Add more macro indicators and countries
- Add more asset classes
- Improve news sentiment with NLP or embeddings
- Store live forward predictions separately from historical test predictions
- Add risk-adjusted backtest metrics
- Add drawdown and Sharpe ratio
- Add model artifact saving
- Add automated tests
- Add deployment documentation
- Add dashboard screenshots
