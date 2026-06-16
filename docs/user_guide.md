# Dashboard User Guide

This guide explains how to use the Macro AI Streamlit dashboard.

Macro AI is a research and learning tool. It is not guaranteed financial advice
and should not be used as the only input for trading or investing.

## Start the Dashboard

From the project folder:

```powershell
venv\Scripts\activate
streamlit run dashboard\app.py
```

Open:

```text
http://localhost:8501
```

## Refresh Data

Use the sidebar `Refresh Data` button to refresh the dashboard view. The button
does not run the full ingestion pipeline by itself. To update the database, run:

```powershell
python -m scripts.run_daily_update
```

## Database Summary

This section shows:

- market row count
- macro row count
- latest database update time

Use it as a quick health check.

## Latest Market Data

This section shows the most recent stored price for each tracked asset.

Use the asset selector to choose a price history chart.

## Latest Macroeconomic Data

This section shows the latest GDP, CPI, and interest rate values stored from
FRED.

These values are used as macro context in feature engineering and machine
learning.

## Market Signals

This section shows engineered market features:

- daily return
- weekly return
- momentum
- volatility
- macro context for the signal date

These are inputs for later intelligence layers.

## Rule-Based Market Intelligence

This section uses transparent rules to assign:

- `BULLISH`
- `BEARISH`
- `NEUTRAL`
- `INSUFFICIENT_DATA`

The explanation text shows why the rule engine chose a signal.

## News Sentiment

This section shows individual headlines and their sentiment scores.

Sentiment labels:

- `POSITIVE`
- `NEGATIVE`
- `NEUTRAL`

## News Sentiment Summary

This section groups recent headlines by asset and shows:

- headline count
- average sentiment score
- positive headline count
- negative headline count
- neutral headline count
- dominant sentiment label
- latest headline and source

This gives combined intelligence a broader news view than one headline.

## Combined Market Intelligence

This section combines:

- rule-based market signal
- macro context
- summarized news sentiment

Example combined signals:

- `STRONG_BULLISH`
- `BULLISH`
- `MIXED`
- `BEARISH`
- `STRONG_BEARISH`

## ML Direction Predictions

This section shows the best model's prediction for the next available market
direction.

Prediction direction:

- `UP` means the model predicts the asset may rise.
- `DOWN` means the model predicts the asset may fall or stay flat.

Prediction probability is the model's estimated probability of an upward move.
Values close to 50% should be treated as uncertain.

## Model Comparison

This section compares the trained models:

- logistic regression
- random forest

It shows:

- best model
- accuracy
- precision
- recall
- F1 score
- classification report

The best model writes predictions into `model_predictions`.

## Prediction Rating + Model Reflection

This section checks historical model predictions against actual outcomes.

It shows:

- lifetime rating
- recent rating
- overall accuracy
- trust status
- asset rating
- asset accuracy
- model mood
- reflection message

Model mood examples:

- `CONFIDENT`
- `SATISFIED`
- `CAUTIOUS`
- `CONCERNED`
- `DISAPPOINTED`

Trust status summarizes whether the model is earning confidence or needs more
proof.

## Backtesting Performance

This section simulates a simple strategy:

- predicted UP -> long trade
- predicted DOWN -> short trade

It shows:

- total return
- win rate
- average trade return
- total trades
- asset-wise return
- backtest history

The backtest is simple and does not include transaction costs, slippage, or risk
management.

## Recommended Daily Workflow

Run the full update:

```powershell
python -m scripts.run_daily_update
```

Then open or refresh the dashboard:

```powershell
streamlit run dashboard\app.py
```

Review sections in this order:

1. Database Summary
2. Latest Market Data
3. Latest Macroeconomic Data
4. News Sentiment Summary
5. Combined Market Intelligence
6. ML Direction Predictions
7. Model Comparison
8. Prediction Rating + Model Reflection
9. Backtesting Performance

## Common Checks

If the dashboard shows missing table warnings, run:

```powershell
python -m scripts.run_daily_update
```

If API data is missing, check your local `.env` file. Do not commit `.env`.
