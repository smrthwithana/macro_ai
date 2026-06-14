import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
import streamlit as st
from config.database import engine

st.set_page_config(
    page_title="Macro AI Dashboard",
    layout="wide"
)

st.title("Macro AI Dashboard")
st.write("Market data and macroeconomic data from PostgreSQL")

with st.sidebar:
    st.header("Dashboard Controls")

    refresh_clicked = st.button("Refresh Data")

    if refresh_clicked:
        st.session_state["last_refresh_click"] = datetime.now()

    if "last_refresh_click" in st.session_state:
        st.success(
            f"Dashboard refreshed at {st.session_state['last_refresh_click'].strftime('%H:%M:%S')}"
        )

    st.write("Use this dashboard to monitor market and macroeconomic data.")

latest_market_query = """
WITH ranked_market AS (
    SELECT
        asset,
        price,
        timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY asset
            ORDER BY timestamp DESC
        ) AS row_num
    FROM market_data
)
SELECT
    asset,
    price,
    timestamp
FROM ranked_market
WHERE row_num = 1
ORDER BY asset;
"""

market_history_query = """
SELECT
    asset,
    price,
    timestamp
FROM market_data
ORDER BY timestamp;
"""

latest_macro_query = """
WITH ranked_macro AS (
    SELECT
        country,
        indicator,
        value,
        record_date,
        source,
        timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY country, indicator
            ORDER BY record_date DESC, timestamp DESC
        ) AS row_num
    FROM macro_data
)
SELECT
    country,
    indicator,
    value,
    record_date,
    source,
    timestamp
FROM ranked_macro
WHERE row_num = 1
ORDER BY country, indicator;
"""

market_count_query = """
SELECT COUNT(*) AS row_count
FROM market_data;
"""

macro_count_query = """
SELECT COUNT(*) AS row_count
FROM macro_data;
"""

market_signals_query = """
SELECT
    asset,
    price,
    daily_return,
    weekly_return,
    momentum,
    volatility,
    macro_gdp,
    macro_cpi,
    macro_interest_rate,
    price_date
FROM market_signals
ORDER BY price_date DESC, asset;
"""

latest_market_df = pd.read_sql(latest_market_query, engine)
market_history_df = pd.read_sql(market_history_query, engine)
latest_macro_df = pd.read_sql(latest_macro_query, engine)

market_count = pd.read_sql(market_count_query, engine)["row_count"].iloc[0]
macro_count = pd.read_sql(macro_count_query, engine)["row_count"].iloc[0]

latest_market_update = latest_market_df["timestamp"].max()
latest_macro_update = latest_macro_df["timestamp"].max()

st.header("Database Summary")

summary_col_1, summary_col_2, summary_col_3 = st.columns(3)

with summary_col_1:
    st.metric("Market Rows", market_count)

with summary_col_2:
    st.metric("Macro Rows", macro_count)

with summary_col_3:
    latest_update = max(latest_market_update, latest_macro_update)
    st.metric("Last Updated", str(latest_update).split(".")[0])

st.header("Latest Market Data")

market_cols = st.columns(len(latest_market_df))

for index, row in latest_market_df.iterrows():
    with market_cols[index]:
        st.metric(
            label=row["asset"],
            value=f"{row['price']:,.2f}"
        )

selected_asset = st.selectbox(
    "Select Asset",
    latest_market_df["asset"].tolist()
)

selected_asset_history_df = market_history_df[
    market_history_df["asset"] == selected_asset
]

st.subheader(f"{selected_asset} Price History")

if not selected_asset_history_df.empty:
    chart_df = selected_asset_history_df.set_index("timestamp")["price"]
    st.line_chart(chart_df)

st.dataframe(latest_market_df, width="stretch")

st.header("Latest Macroeconomic Data")

macro_cols = st.columns(len(latest_macro_df))

for index, row in latest_macro_df.iterrows():
    with macro_cols[index]:
        st.metric(
            label=f"{row['country']} {row['indicator']}",
            value=f"{row['value']:,.2f}"
        )

selected_macro_indicator = st.selectbox(
    "Select Macro Indicator",
    latest_macro_df["indicator"].tolist()
)

selected_macro_df = latest_macro_df[
    latest_macro_df["indicator"] == selected_macro_indicator
]

st.subheader(f"{selected_macro_indicator} Latest Data")
st.dataframe(selected_macro_df, width="stretch")

st.subheader("All Latest Macro Data")
st.dataframe(latest_macro_df, width="stretch")

st.header("Market Signals")

try:
    market_signals_df = pd.read_sql(market_signals_query, engine)

    if market_signals_df.empty:
        st.info("No market signals available yet. Run scripts/build_market_signals.py first.")
    else:
        signal_asset = st.selectbox(
            "Select Signal Asset",
            market_signals_df["asset"].dropna().unique().tolist()
        )

        selected_signal_df = market_signals_df[
            market_signals_df["asset"] == signal_asset
        ]

        latest_signal = selected_signal_df.iloc[0]

        signal_col_1, signal_col_2, signal_col_3, signal_col_4 = st.columns(4)

        with signal_col_1:
            st.metric(
                "Daily Return",
                f"{latest_signal['daily_return']:.4f}"
                if pd.notna(latest_signal["daily_return"])
                else "N/A"
            )

        with signal_col_2:
            st.metric(
                "Weekly Return",
                f"{latest_signal['weekly_return']:.4f}"
                if pd.notna(latest_signal["weekly_return"])
                else "N/A"
            )

        with signal_col_3:
            st.metric(
                "Momentum",
                f"{latest_signal['momentum']:.4f}"
                if pd.notna(latest_signal["momentum"])
                else "N/A"
            )

        with signal_col_4:
            st.metric(
                "Volatility",
                f"{latest_signal['volatility']:.4f}"
                if pd.notna(latest_signal["volatility"])
                else "N/A"
            )

        st.subheader("Macro Context for Signal Date")

        macro_context_col_1, macro_context_col_2, macro_context_col_3 = st.columns(3)

        with macro_context_col_1:
            st.metric("GDP", f"{latest_signal['macro_gdp']:,.2f}")

        with macro_context_col_2:
            st.metric("CPI", f"{latest_signal['macro_cpi']:,.2f}")

        with macro_context_col_3:
            st.metric("Interest Rate", f"{latest_signal['macro_interest_rate']:,.2f}")

        st.subheader("Signal Data")
        st.dataframe(selected_signal_df, width="stretch")

except Exception as e:
    st.warning("Market signals table not found yet. Run the signal builder first.")
