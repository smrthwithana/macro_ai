import sys
from pathlib import Path

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

latest_market_df = pd.read_sql(latest_market_query, engine)
market_history_df = pd.read_sql(market_history_query, engine)
latest_macro_df = pd.read_sql(latest_macro_query, engine)

st.header("Latest Market Data")

market_cols = st.columns(len(latest_market_df))

for index, row in latest_market_df.iterrows():
    with market_cols[index]:
        st.metric(
            label=row["asset"],
            value=f"{row['price']:,.2f}"
        )

st.dataframe(latest_market_df, use_container_width=True)

st.header("Market Price History")

if not market_history_df.empty:
    chart_df = market_history_df.pivot_table(
        index="timestamp",
        columns="asset",
        values="price",
        aggfunc="last"
    )

    st.line_chart(chart_df)

st.header("Latest Macroeconomic Data")

macro_cols = st.columns(len(latest_macro_df))

for index, row in latest_macro_df.iterrows():
    with macro_cols[index]:
        st.metric(
            label=f"{row['country']} {row['indicator']}",
            value=f"{row['value']:,.2f}"
        )

st.dataframe(latest_macro_df, use_container_width=True)
