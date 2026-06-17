import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
import streamlit as st
from config.database import engine


st.set_page_config(
    page_title="Macro AI Dashboard",
    layout="wide",
)


SIMPLE_MARKET_ASSETS = ["SP500", "NASDAQ", "GOLD", "OIL", "EURUSD", "USDINR"]

BULLISH_SIMPLE_SIGNALS = {"STRONG_BULLISH", "BULLISH"}
BEARISH_SIMPLE_SIGNALS = {"STRONG_BEARISH", "BEARISH"}
LOW_TRUST_STATUSES = {"LOW_TRUST_NEEDS_IMPROVEMENT"}
LOW_CONFIDENCE_LABELS = {"LOW", "INSUFFICIENT_DATA"}
WEAK_PROBABILITY_DISTANCE = 0.10


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

rule_based_signals_query = """
SELECT
    asset,
    price_date,
    market_signal,
    confidence,
    rule_score,
    reason,
    daily_return,
    weekly_return,
    momentum,
    volatility,
    macro_gdp,
    macro_cpi,
    macro_interest_rate
FROM rule_based_signals
ORDER BY price_date DESC, asset;
"""

news_sentiment_query = """
SELECT
    related_asset,
    sentiment_label,
    sentiment_score,
    title,
    source,
    published_at,
    created_at
FROM news_sentiment
ORDER BY published_at DESC, related_asset;
"""

news_sentiment_summary_query = """
SELECT
    related_asset,
    recent_window_days,
    headline_count,
    average_sentiment_score,
    positive_count,
    negative_count,
    neutral_count,
    dominant_sentiment_label,
    latest_headline,
    latest_source,
    latest_published_date,
    created_at
FROM news_sentiment_summary
ORDER BY related_asset;
"""

combined_intelligence_query = """
SELECT
    asset,
    price_date,
    market_signal,
    confidence,
    sentiment_label,
    sentiment_score,
    combined_signal,
    combined_confidence,
    intelligence_summary,
    headline,
    daily_return,
    weekly_return,
    momentum,
    volatility,
    macro_gdp,
    macro_cpi,
    macro_interest_rate
FROM combined_intelligence_signals
ORDER BY price_date DESC, asset;
"""

model_predictions_query = """
SELECT
    asset,
    price_date,
    price,
    target_direction,
    predicted_direction,
    prediction_probability,
    model_name,
    model_accuracy,
    created_at
FROM model_predictions
ORDER BY price_date DESC, asset;
"""

live_predictions_query = """
SELECT
    asset,
    prediction_date,
    prediction_price,
    predicted_direction,
    prediction_probability,
    model_name,
    status,
    actual_date,
    actual_price,
    actual_direction,
    prediction_correct,
    star_rating,
    model_mood,
    trust_impact,
    reflection_message,
    created_at,
    updated_at
FROM live_predictions
ORDER BY prediction_date DESC, asset;
"""

model_performance_query = """
SELECT
    model_name,
    is_best_model,
    train_rows,
    test_rows,
    accuracy,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    created_at
FROM model_performance_summary
ORDER BY is_best_model DESC, accuracy DESC, f1_score DESC;
"""

prediction_rating_summary_query = """
SELECT
    summary_type,
    asset,
    prediction_count,
    lifetime_rating,
    recent_30_rating,
    overall_accuracy,
    asset_wise_rating,
    asset_wise_accuracy,
    asset_recent_30_rating,
    trust_status,
    created_at
FROM prediction_rating_summary
ORDER BY summary_type DESC, asset;
"""

prediction_ratings_query = """
SELECT
    asset,
    price_date,
    target_direction,
    predicted_direction,
    prediction_probability,
    prediction_correct,
    confidence_bucket,
    star_rating,
    model_mood,
    trust_impact,
    reflection_message,
    rating_created_at
FROM prediction_ratings
ORDER BY price_date DESC, asset;
"""

backtest_summary_query = """
SELECT
    summary_type,
    asset,
    model_name,
    total_trades,
    winning_trades,
    losing_trades,
    flat_trades,
    win_rate,
    average_trade_return,
    cumulative_return,
    best_trade_return,
    worst_trade_return,
    created_at
FROM backtest_summary
ORDER BY summary_type DESC, asset;
"""

backtest_results_query = """
SELECT
    asset,
    price_date,
    next_price_date,
    strategy_position,
    actual_next_return,
    strategy_return,
    trade_result,
    prediction_probability,
    asset_cumulative_return,
    overall_cumulative_return,
    model_name
FROM backtest_results
ORDER BY price_date DESC, asset;
"""

simple_model_predictions_query = """
WITH ranked_predictions AS (
    SELECT
        asset,
        price_date,
        price,
        predicted_direction,
        prediction_probability,
        model_name,
        model_accuracy,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY asset
            ORDER BY price_date DESC, created_at DESC
        ) AS row_num
    FROM model_predictions
)
SELECT
    asset,
    price_date,
    price,
    predicted_direction,
    prediction_probability,
    model_name,
    model_accuracy,
    created_at
FROM ranked_predictions
WHERE row_num = 1
ORDER BY asset;
"""

simple_combined_intelligence_query = """
WITH ranked_intelligence AS (
    SELECT
        asset,
        price_date,
        price,
        combined_signal,
        combined_confidence,
        sentiment_label,
        sentiment_score,
        intelligence_summary,
        ROW_NUMBER() OVER (
            PARTITION BY asset
            ORDER BY price_date DESC
        ) AS row_num
    FROM combined_intelligence_signals
)
SELECT
    asset,
    price_date,
    price,
    combined_signal,
    combined_confidence,
    sentiment_label,
    sentiment_score,
    intelligence_summary
FROM ranked_intelligence
WHERE row_num = 1
ORDER BY asset;
"""

simple_prediction_rating_summary_query = """
SELECT
    summary_type,
    asset,
    prediction_count,
    asset_wise_rating,
    asset_wise_accuracy,
    asset_recent_30_rating,
    trust_status,
    created_at
FROM prediction_rating_summary
WHERE summary_type IN ('ASSET', 'OVERALL')
ORDER BY summary_type DESC, asset;
"""

simple_backtest_summary_query = """
SELECT
    summary_type,
    asset,
    total_trades,
    win_rate,
    average_trade_return,
    cumulative_return,
    created_at
FROM backtest_summary
WHERE summary_type IN ('ASSET', 'OVERALL')
ORDER BY summary_type DESC, asset;
"""

simple_news_sentiment_summary_query = """
SELECT
    related_asset,
    headline_count,
    average_sentiment_score,
    dominant_sentiment_label,
    latest_headline,
    latest_source,
    latest_published_date,
    created_at
FROM news_sentiment_summary
ORDER BY related_asset;
"""


def read_sql(query):
    return pd.read_sql(query, engine)


def read_optional_sql(query, unavailable_message):
    try:
        return read_sql(query)
    except Exception:
        st.info(unavailable_message)
        return pd.DataFrame()


def latest_rows_by_asset(df, asset_column="asset"):
    if df.empty or asset_column not in df.columns:
        return {}

    asset_rows = {}

    for _, row in df.iterrows():
        asset = row.get(asset_column)

        if pd.notna(asset):
            asset_rows[str(asset)] = row

    return asset_rows


def rating_rows_by_asset(df):
    if df.empty:
        return {}, None

    asset_df = df[df["summary_type"] == "ASSET"]
    overall_df = df[df["summary_type"] == "OVERALL"]
    asset_rows = latest_rows_by_asset(asset_df)
    overall_row = overall_df.iloc[0] if not overall_df.empty else None

    return asset_rows, overall_row


def normalize_label(value, default="UNKNOWN"):
    if pd.isna(value):
        return default

    return str(value).strip().upper()


def readable_label(value):
    label = normalize_label(value, "N/A")

    if label == "N/A":
        return label

    return label.replace("_", " ")


def format_price(value):
    if pd.isna(value):
        return "N/A"

    return f"{float(value):,.2f}"


def format_percent(value):
    if pd.isna(value):
        return "N/A"

    return f"{float(value):.2%}"


def get_first_available(row_options, column_name):
    for row in row_options:
        if row is not None and column_name in row and pd.notna(row[column_name]):
            return row[column_name]

    return None


def prediction_direction(row):
    if row is None or pd.isna(row.get("predicted_direction")):
        return None

    return "UP" if int(row["predicted_direction"]) == 1 else "DOWN"


def probability_is_weak(probability):
    if pd.isna(probability):
        return True

    return abs(float(probability) - 0.5) < WEAK_PROBABILITY_DISTANCE


def build_simple_market_decision(
    asset,
    market_row,
    prediction_row,
    combined_row,
    rating_row,
    overall_rating_row,
    backtest_row,
    sentiment_row,
):
    ml_direction = prediction_direction(prediction_row)
    probability = get_first_available([prediction_row], "prediction_probability")
    combined_signal = normalize_label(
        get_first_available([combined_row], "combined_signal")
    )
    combined_confidence = normalize_label(
        get_first_available([combined_row], "combined_confidence")
    )
    trust_status = normalize_label(
        get_first_available([rating_row, overall_rating_row], "trust_status")
    )
    sentiment_label = normalize_label(
        get_first_available([sentiment_row, combined_row], "dominant_sentiment_label")
    )

    if sentiment_label == "UNKNOWN":
        sentiment_label = normalize_label(
            get_first_available([combined_row], "sentiment_label")
        )

    backtest_win_rate = get_first_available([backtest_row], "win_rate")
    price = get_first_available([market_row, prediction_row, combined_row], "price")

    caution_reasons = []

    if ml_direction is None:
        caution_reasons.append("ML prediction is not available")

    if combined_signal == "UNKNOWN":
        caution_reasons.append("combined signal is not available")

    if trust_status in LOW_TRUST_STATUSES:
        caution_reasons.append("model trust is low")

    if probability_is_weak(probability):
        caution_reasons.append("ML probability is close to 50%")

    if combined_confidence in LOW_CONFIDENCE_LABELS:
        caution_reasons.append("combined confidence is low")

    if combined_signal in {"MIXED", "NEUTRAL", "INSUFFICIENT_DATA"}:
        caution_reasons.append("signals are mixed or unclear")

    if pd.notna(backtest_win_rate) and float(backtest_win_rate) < 0.45:
        caution_reasons.append("recent backtest win rate is weak")

    if (
        ml_direction == "UP"
        and combined_signal in BEARISH_SIMPLE_SIGNALS
        or ml_direction == "DOWN"
        and combined_signal in BULLISH_SIMPLE_SIGNALS
    ):
        caution_reasons.append("ML and combined signals conflict")

    if ml_direction == "UP" and sentiment_label == "NEGATIVE":
        caution_reasons.append("news sentiment is negative")

    if ml_direction == "DOWN" and sentiment_label == "POSITIVE":
        caution_reasons.append("news sentiment is positive")

    if caution_reasons:
        return {
            "asset": asset,
            "direction": "WAIT / MIXED",
            "tone": "warning",
            "price": price,
            "ml_probability": probability,
            "trust_status": trust_status,
            "combined_signal": combined_signal,
            "sentiment_label": sentiment_label,
            "backtest_win_rate": backtest_win_rate,
            "explanation": "Signals are mixed, confidence is weak, or trust needs caution, so waiting is safer.",
            "details": "; ".join(caution_reasons),
        }

    if ml_direction == "UP" and combined_signal in BULLISH_SIMPLE_SIGNALS:
        return {
            "asset": asset,
            "direction": "LIKELY UP",
            "tone": "success",
            "price": price,
            "ml_probability": probability,
            "trust_status": trust_status,
            "combined_signal": combined_signal,
            "sentiment_label": sentiment_label,
            "backtest_win_rate": backtest_win_rate,
            "explanation": "The model and signals mostly agree that this asset may move up.",
            "details": "ML direction is UP and combined intelligence is bullish.",
        }

    if ml_direction == "DOWN" and combined_signal in BEARISH_SIMPLE_SIGNALS:
        return {
            "asset": asset,
            "direction": "LIKELY DOWN",
            "tone": "error",
            "price": price,
            "ml_probability": probability,
            "trust_status": trust_status,
            "combined_signal": combined_signal,
            "sentiment_label": sentiment_label,
            "backtest_win_rate": backtest_win_rate,
            "explanation": "The model and signals mostly agree that this asset may move down.",
            "details": "ML direction is DOWN and combined intelligence is bearish.",
        }

    return {
        "asset": asset,
        "direction": "WAIT / MIXED",
        "tone": "warning",
        "price": price,
        "ml_probability": probability,
        "trust_status": trust_status,
        "combined_signal": combined_signal,
        "sentiment_label": sentiment_label,
        "backtest_win_rate": backtest_win_rate,
        "explanation": "Signals are mixed, so waiting is safer.",
        "details": "The available signals do not line up strongly enough for a simple up or down view.",
    }


def render_simple_market_card(decision):
    with st.container(border=True):
        st.subheader(decision["asset"])

        if decision["tone"] == "success":
            st.success(decision["direction"])
        elif decision["tone"] == "error":
            st.error(decision["direction"])
        else:
            st.warning(decision["direction"])

        metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)

        with metric_col_1:
            st.metric("Latest Price", format_price(decision["price"]))

        with metric_col_2:
            st.metric("ML Probability", format_percent(decision["ml_probability"]))

        with metric_col_3:
            st.metric("Model Trust", readable_label(decision["trust_status"]))

        with metric_col_4:
            st.metric("Backtest Win Rate", format_percent(decision["backtest_win_rate"]))

        context_col_1, context_col_2 = st.columns(2)

        with context_col_1:
            st.write(f"Combined signal: **{readable_label(decision['combined_signal'])}**")

        with context_col_2:
            st.write(f"News sentiment: **{readable_label(decision['sentiment_label'])}**")

        st.write(decision["explanation"])
        st.caption(f"Why: {decision['details']}")
        st.caption(
            "Research tool only. This simple view is not guaranteed financial advice."
        )


def show_intro():
    st.title("Macro AI Dashboard")
    st.write("Market data, macroeconomic data, news sentiment, ML predictions, ratings, and backtesting from PostgreSQL.")
    st.warning(
        "Research and learning tool only. This dashboard is not guaranteed financial advice "
        "and should not be used as the sole basis for trading or investment decisions."
    )


def show_dashboard_guide():
    st.header("Dashboard Guide")
    st.markdown(
        """
        - **Prediction direction** shows whether the model expects the next available market move to be up or down.
        - **Prediction probability** is the model's confidence for an upward move. Values near 50% are uncertain.
        - **Trust status** summarizes long-term model reliability from historical prediction ratings.
        - **Model mood** translates recent prediction quality into a readable state such as CAUTIOUS or CONCERNED.
        - **Reflection message** explains what the model got right or wrong and how that affects trust.
        - **Backtest return** simulates a simple long/short strategy based on predicted direction.
        - **Win rate** shows how often the simulated strategy produced a positive trade result.
        - **Model comparison** shows which ML model performed best on the time-based test split.
        """
    )


def show_simple_market_view():
    st.header("Simple Market View")
    st.write(
        "Simple Market View converts the advanced model, sentiment, and signal outputs into beginner-friendly green/red/yellow cards."
    )
    st.warning(
        "Research and learning tool only. These cards are not guaranteed financial advice "
        "and should not be used as the sole basis for trading or investment decisions."
    )

    latest_market_df = read_optional_sql(
        latest_market_query,
        "Latest market prices are not available yet. Run the market ingestion first.",
    )
    model_predictions_df = read_optional_sql(
        simple_model_predictions_query,
        "Latest ML predictions are not available yet. Run scripts/train_direction_model.py first.",
    )
    combined_intelligence_df = read_optional_sql(
        simple_combined_intelligence_query,
        "Combined intelligence signals are not available yet. Run scripts/build_combined_intelligence.py first.",
    )
    prediction_rating_summary_df = read_optional_sql(
        simple_prediction_rating_summary_query,
        "Prediction trust ratings are not available yet. Run scripts/build_prediction_ratings.py first.",
    )
    backtest_summary_df = read_optional_sql(
        simple_backtest_summary_query,
        "Backtest summary is not available yet. Run scripts/build_backtest_results.py first.",
    )
    news_sentiment_summary_df = read_optional_sql(
        simple_news_sentiment_summary_query,
        "News sentiment summary is not available yet. Run scripts/build_news_sentiment_summary.py first.",
    )

    market_rows = latest_rows_by_asset(latest_market_df)
    prediction_rows = latest_rows_by_asset(model_predictions_df)
    combined_rows = latest_rows_by_asset(combined_intelligence_df)
    rating_rows, overall_rating_row = rating_rows_by_asset(prediction_rating_summary_df)
    backtest_rows = latest_rows_by_asset(
        backtest_summary_df[backtest_summary_df["summary_type"] == "ASSET"]
        if not backtest_summary_df.empty
        else backtest_summary_df
    )
    sentiment_rows = latest_rows_by_asset(news_sentiment_summary_df, "related_asset")

    available_assets = set(SIMPLE_MARKET_ASSETS)

    for rows in [
        market_rows,
        prediction_rows,
        combined_rows,
        rating_rows,
        backtest_rows,
        sentiment_rows,
    ]:
        available_assets.update(rows.keys())

    ordered_assets = SIMPLE_MARKET_ASSETS + sorted(
        asset for asset in available_assets if asset not in SIMPLE_MARKET_ASSETS
    )

    if not any(
        [
            market_rows,
            prediction_rows,
            combined_rows,
            rating_rows,
            backtest_rows,
            sentiment_rows,
        ]
    ):
        st.warning("No simple market inputs are available yet. Run the daily update first.")
        return

    st.caption(
        "Green means the ML model and combined signal agree upward. Red means they agree downward. "
        "Yellow means the inputs conflict, confidence is weak, or trust needs caution."
    )

    for row_start in range(0, len(ordered_assets), 2):
        card_cols = st.columns(2)

        for col_index, asset in enumerate(ordered_assets[row_start:row_start + 2]):
            with card_cols[col_index]:
                decision = build_simple_market_decision(
                    asset,
                    market_rows.get(asset),
                    prediction_rows.get(asset),
                    combined_rows.get(asset),
                    rating_rows.get(asset),
                    overall_rating_row,
                    backtest_rows.get(asset),
                    sentiment_rows.get(asset),
                )
                render_simple_market_card(decision)


def show_overview():
    st.header("Overview")
    st.caption("High-level health check for the database and latest update state.")

    try:
        latest_market_df = read_sql(latest_market_query)
        latest_macro_df = read_sql(latest_macro_query)
        market_count = read_sql(market_count_query)["row_count"].iloc[0]
        macro_count = read_sql(macro_count_query)["row_count"].iloc[0]

        latest_market_update = latest_market_df["timestamp"].max()
        latest_macro_update = latest_macro_df["timestamp"].max()
        latest_update = max(latest_market_update, latest_macro_update)

        summary_col_1, summary_col_2, summary_col_3 = st.columns(3)

        with summary_col_1:
            st.metric("Market Rows", market_count)

        with summary_col_2:
            st.metric("Macro Rows", macro_count)

        with summary_col_3:
            st.metric("Last Updated", str(latest_update).split(".")[0])

        st.subheader("Latest Market Snapshot")
        market_cols = st.columns(len(latest_market_df))

        for index, row in latest_market_df.iterrows():
            with market_cols[index]:
                st.metric(
                    label=row["asset"],
                    value=f"{row['price']:,.2f}",
                )

        st.subheader("Latest Macro Snapshot")
        st.dataframe(latest_macro_df, width="stretch")

    except Exception:
        st.warning("Overview data is not available yet. Run the daily update first.")


def show_market_data():
    st.header("Latest Market Data")
    st.caption("Latest stored prices for each tracked asset, pulled from PostgreSQL after market ingestion.")

    try:
        latest_market_df = read_sql(latest_market_query)
        market_history_df = read_sql(market_history_query)

        market_cols = st.columns(len(latest_market_df))

        for index, row in latest_market_df.iterrows():
            with market_cols[index]:
                st.metric(
                    label=row["asset"],
                    value=f"{row['price']:,.2f}",
                )

        selected_asset = st.selectbox(
            "Select Asset",
            latest_market_df["asset"].tolist(),
        )

        selected_asset_history_df = market_history_df[
            market_history_df["asset"] == selected_asset
        ]

        st.subheader(f"{selected_asset} Price History")

        if not selected_asset_history_df.empty:
            chart_df = selected_asset_history_df.set_index("timestamp")["price"]
            st.line_chart(chart_df)

        st.dataframe(latest_market_df, width="stretch")

    except Exception:
        st.warning("Market data is not available yet. Run the market ingestion first.")


def show_macro_data():
    st.header("Latest Macroeconomic Data")
    st.caption("Most recent macro indicators stored from FRED, used as economic context for signals and models.")

    try:
        latest_macro_df = read_sql(latest_macro_query)

        macro_cols = st.columns(len(latest_macro_df))

        for index, row in latest_macro_df.iterrows():
            with macro_cols[index]:
                st.metric(
                    label=f"{row['country']} {row['indicator']}",
                    value=f"{row['value']:,.2f}",
                )

        selected_macro_indicator = st.selectbox(
            "Select Macro Indicator",
            latest_macro_df["indicator"].tolist(),
        )

        selected_macro_df = latest_macro_df[
            latest_macro_df["indicator"] == selected_macro_indicator
        ]

        st.subheader(f"{selected_macro_indicator} Latest Data")
        st.dataframe(selected_macro_df, width="stretch")

        st.subheader("All Latest Macro Data")
        st.dataframe(latest_macro_df, width="stretch")

    except Exception:
        st.warning("Macro data is not available yet. Run the FRED macro ingestion first.")


def show_news_sentiment():
    st.header("News Sentiment")
    st.caption("Individual news headlines scored with a simple positive, negative, or neutral sentiment rule.")

    try:
        news_sentiment_df = read_sql(news_sentiment_query)

        if news_sentiment_df.empty:
            st.info("No news sentiment data available yet. Run scripts/build_news_sentiment.py first.")
        else:
            sentiment_asset = st.selectbox(
                "Select Sentiment Asset",
                news_sentiment_df["related_asset"].dropna().unique().tolist(),
            )

            selected_sentiment_df = news_sentiment_df[
                news_sentiment_df["related_asset"] == sentiment_asset
            ]

            latest_sentiment = selected_sentiment_df.iloc[0]

            sentiment_col_1, sentiment_col_2, sentiment_col_3 = st.columns(3)

            with sentiment_col_1:
                st.metric("Sentiment Label", latest_sentiment["sentiment_label"])

            with sentiment_col_2:
                st.metric("Sentiment Score", int(latest_sentiment["sentiment_score"]))

            with sentiment_col_3:
                st.metric("Source", latest_sentiment["source"])

            sentiment_value = latest_sentiment["sentiment_label"]

            if sentiment_value == "POSITIVE":
                st.success("News sentiment is positive for this asset.")
            elif sentiment_value == "NEGATIVE":
                st.error("News sentiment is negative for this asset.")
            else:
                st.warning("News sentiment is neutral for this asset.")

            st.subheader("Latest Related Headline")
            st.write(latest_sentiment["title"])

            st.subheader("News Sentiment Data")
            st.dataframe(selected_sentiment_df, width="stretch")

    except Exception:
        st.warning("News sentiment table not found yet. Run the news sentiment builder first.")

    st.header("News Sentiment Summary")
    st.caption("Recent headlines are grouped by asset to create a cleaner sentiment picture for combined intelligence.")

    try:
        news_sentiment_summary_df = read_sql(news_sentiment_summary_query)

        if news_sentiment_summary_df.empty:
            st.info("No news sentiment summary available yet. Run scripts/build_news_sentiment_summary.py first.")
        else:
            summary_asset = st.selectbox(
                "Select Sentiment Summary Asset",
                news_sentiment_summary_df["related_asset"].dropna().unique().tolist(),
            )

            selected_summary_df = news_sentiment_summary_df[
                news_sentiment_summary_df["related_asset"] == summary_asset
            ]

            latest_summary = selected_summary_df.iloc[0]

            summary_col_1, summary_col_2, summary_col_3, summary_col_4 = st.columns(4)

            with summary_col_1:
                st.metric("Headlines", int(latest_summary["headline_count"]))

            with summary_col_2:
                st.metric("Average Score", f"{latest_summary['average_sentiment_score']:.2f}")

            with summary_col_3:
                st.metric("Dominant Sentiment", latest_summary["dominant_sentiment_label"])

            with summary_col_4:
                st.metric("Latest Source", latest_summary["latest_source"])

            sentiment_mix_col_1, sentiment_mix_col_2, sentiment_mix_col_3 = st.columns(3)

            with sentiment_mix_col_1:
                st.metric("Positive Headlines", int(latest_summary["positive_count"]))

            with sentiment_mix_col_2:
                st.metric("Negative Headlines", int(latest_summary["negative_count"]))

            with sentiment_mix_col_3:
                st.metric("Neutral Headlines", int(latest_summary["neutral_count"]))

            st.subheader("Latest Summary Headline")
            st.write(latest_summary["latest_headline"])

            st.subheader("All Sentiment Summaries")
            st.dataframe(news_sentiment_summary_df, width="stretch")

    except Exception:
        st.warning("News sentiment summary table not found yet. Run the news sentiment summary builder first.")


def show_signals_and_intelligence():
    st.header("Market Signals")

    try:
        market_signals_df = read_sql(market_signals_query)

        if market_signals_df.empty:
            st.info("No market signals available yet. Run scripts/build_market_signals.py first.")
        else:
            signal_asset = st.selectbox(
                "Select Signal Asset",
                market_signals_df["asset"].dropna().unique().tolist(),
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
                    else "N/A",
                )

            with signal_col_2:
                st.metric(
                    "Weekly Return",
                    f"{latest_signal['weekly_return']:.4f}"
                    if pd.notna(latest_signal["weekly_return"])
                    else "N/A",
                )

            with signal_col_3:
                st.metric(
                    "Momentum",
                    f"{latest_signal['momentum']:.4f}"
                    if pd.notna(latest_signal["momentum"])
                    else "N/A",
                )

            with signal_col_4:
                st.metric(
                    "Volatility",
                    f"{latest_signal['volatility']:.4f}"
                    if pd.notna(latest_signal["volatility"])
                    else "N/A",
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

    except Exception:
        st.warning("Market signals table not found yet. Run the signal builder first.")

    st.header("Rule-Based Market Intelligence")

    try:
        rule_based_signals_df = read_sql(rule_based_signals_query)

        if rule_based_signals_df.empty:
            st.info("No rule-based signals available yet. Run scripts/build_rule_based_signals.py first.")
        else:
            rule_asset = st.selectbox(
                "Select Rule-Based Signal Asset",
                rule_based_signals_df["asset"].dropna().unique().tolist(),
            )

            selected_rule_df = rule_based_signals_df[
                rule_based_signals_df["asset"] == rule_asset
            ]

            latest_rule_signal = selected_rule_df.iloc[0]

            rule_col_1, rule_col_2, rule_col_3 = st.columns(3)

            with rule_col_1:
                st.metric("Market Signal", latest_rule_signal["market_signal"])

            with rule_col_2:
                st.metric("Confidence", latest_rule_signal["confidence"])

            with rule_col_3:
                st.metric("Rule Score", int(latest_rule_signal["rule_score"]))

            signal_value = latest_rule_signal["market_signal"]

            if signal_value == "BULLISH":
                st.success("The rule-based engine is currently bullish for this asset.")
            elif signal_value == "BEARISH":
                st.error("The rule-based engine is currently bearish for this asset.")
            elif signal_value == "NEUTRAL":
                st.warning("The rule-based engine is currently neutral for this asset.")
            else:
                st.info("There is not enough market history to generate a strong signal yet.")

            st.subheader("Signal Explanation")
            st.write(latest_rule_signal["reason"])

            st.subheader("Rule-Based Signal Data")
            st.dataframe(selected_rule_df, width="stretch")

    except Exception:
        st.warning("Rule-based signals table not found yet. Run the rule-based signal builder first.")

    st.header("Combined Market Intelligence")
    st.caption("Rule-based market signals are combined with summarized news sentiment to create explainable market intelligence.")

    try:
        combined_intelligence_df = read_sql(combined_intelligence_query)

        if combined_intelligence_df.empty:
            st.info("No combined intelligence data available yet. Run scripts/build_combined_intelligence.py first.")
        else:
            combined_asset = st.selectbox(
                "Select Combined Intelligence Asset",
                combined_intelligence_df["asset"].dropna().unique().tolist(),
            )

            selected_combined_df = combined_intelligence_df[
                combined_intelligence_df["asset"] == combined_asset
            ]

            latest_combined = selected_combined_df.iloc[0]

            combined_col_1, combined_col_2, combined_col_3 = st.columns(3)

            with combined_col_1:
                st.metric("Combined Signal", latest_combined["combined_signal"])

            with combined_col_2:
                st.metric("Combined Confidence", latest_combined["combined_confidence"])

            with combined_col_3:
                st.metric(
                    "News Sentiment",
                    latest_combined["sentiment_label"]
                    if pd.notna(latest_combined["sentiment_label"])
                    else "UNKNOWN",
                )

            combined_signal_value = latest_combined["combined_signal"]

            if combined_signal_value in ["STRONG_BULLISH", "BULLISH", "SLIGHTLY_BULLISH"]:
                st.success("Combined intelligence is bullish for this asset.")
            elif combined_signal_value in ["STRONG_BEARISH", "BEARISH", "SLIGHTLY_BEARISH"]:
                st.error("Combined intelligence is bearish for this asset.")
            elif combined_signal_value == "MIXED":
                st.warning("Combined intelligence is mixed for this asset.")
            else:
                st.info("Combined intelligence is neutral or unclear.")

            st.subheader("Intelligence Summary")
            st.write(latest_combined["intelligence_summary"])

            st.subheader("Related Headline")
            if pd.notna(latest_combined["headline"]):
                st.write(latest_combined["headline"])
            else:
                st.write("No related headline available yet.")

            st.subheader("Combined Intelligence Data")
            st.dataframe(selected_combined_df, width="stretch")

    except Exception:
        st.warning("Combined intelligence table not found yet. Run the combined intelligence builder first.")


def show_ml_predictions():
    st.header("ML Direction Predictions")
    st.caption("Baseline machine learning predictions estimate whether each asset may move up on the next available market date.")

    try:
        model_predictions_df = read_sql(model_predictions_query)

        if model_predictions_df.empty:
            st.info("No ML predictions available yet. Run scripts/train_direction_model.py first.")
        else:
            prediction_asset = st.selectbox(
                "Select Prediction Asset",
                model_predictions_df["asset"].dropna().unique().tolist(),
            )

            selected_prediction_df = model_predictions_df[
                model_predictions_df["asset"] == prediction_asset
            ]

            latest_prediction = selected_prediction_df.iloc[0]
            predicted_direction = int(latest_prediction["predicted_direction"])
            prediction_label = "UP" if predicted_direction == 1 else "DOWN"

            prediction_col_1, prediction_col_2, prediction_col_3 = st.columns(3)

            with prediction_col_1:
                st.metric("Predicted Next Direction", prediction_label)

            with prediction_col_2:
                st.metric(
                    "Prediction Probability",
                    f"{latest_prediction['prediction_probability']:.2%}",
                )

            with prediction_col_3:
                st.metric("Model Accuracy", f"{latest_prediction['model_accuracy']:.2%}")

            if predicted_direction == 1:
                st.success("The ML model predicts this asset may move up on the next available market date.")
            else:
                st.error("The ML model predicts this asset may move down or stay flat on the next available market date.")

            st.subheader("Prediction Details")
            st.write(f"Model used: {latest_prediction['model_name']}")
            st.write(f"Prediction date: {latest_prediction['price_date']}")

            st.subheader("Prediction History")
            st.dataframe(selected_prediction_df, width="stretch")

    except Exception:
        st.warning("Model predictions table not found yet. Run the ML training script first.")

    st.header("Model Comparison")
    st.caption("Compares logistic regression against a second model using the same time-based train/test split.")

    try:
        model_performance_df = read_sql(model_performance_query)

        if model_performance_df.empty:
            st.info("No model comparison available yet. Run scripts/train_direction_model.py first.")
        else:
            best_model = model_performance_df[
                model_performance_df["is_best_model"] == True
            ].iloc[0]

            comparison_col_1, comparison_col_2, comparison_col_3, comparison_col_4 = st.columns(4)

            with comparison_col_1:
                st.metric("Best Model", best_model["model_name"])

            with comparison_col_2:
                st.metric("Best Accuracy", f"{best_model['accuracy']:.2%}")

            with comparison_col_3:
                st.metric("Best F1 Score", f"{best_model['f1_score']:.2%}")

            with comparison_col_4:
                st.metric("Test Rows", int(best_model["test_rows"]))

            model_performance_display_df = model_performance_df[
                [
                    "model_name",
                    "is_best_model",
                    "accuracy",
                    "precision_score",
                    "recall_score",
                    "f1_score",
                    "test_rows",
                ]
            ].copy()

            st.subheader("Model Performance Summary")
            st.write(f"Models compared: {', '.join(model_performance_df['model_name'].tolist())}")
            st.table(model_performance_display_df)

            st.subheader("Best Model Classification Report")
            st.text(best_model["classification_report"])

    except Exception:
        st.warning("Model performance table not found yet. Run the model training script first.")


def show_live_forward_predictions():
    st.header("Live Forward Predictions")
    st.caption(
        "Creates pending predictions from the latest market setup, then completes them when a newer market price arrives."
    )

    try:
        live_predictions_df = read_sql(live_predictions_query)

        if live_predictions_df.empty:
            st.info("No live predictions available yet. Run scripts/build_live_predictions.py first.")
            return

        pending_df = live_predictions_df[
            live_predictions_df["status"] == "PENDING"
        ].copy()
        completed_df = live_predictions_df[
            live_predictions_df["status"] == "COMPLETED"
        ].copy()
        latest_prediction_date = live_predictions_df["prediction_date"].max()

        live_col_1, live_col_2, live_col_3 = st.columns(3)

        with live_col_1:
            st.metric("Pending Predictions", len(pending_df))

        with live_col_2:
            st.metric("Completed Predictions", len(completed_df))

        with live_col_3:
            st.metric("Latest Prediction Date", str(latest_prediction_date))

        live_asset = st.selectbox(
            "Select Live Prediction Asset",
            live_predictions_df["asset"].dropna().unique().tolist(),
        )

        selected_live_df = live_predictions_df[
            live_predictions_df["asset"] == live_asset
        ]

        latest_live_prediction = selected_live_df.iloc[0]
        predicted_direction = int(latest_live_prediction["predicted_direction"])
        predicted_label = "UP" if predicted_direction == 1 else "DOWN"

        selected_col_1, selected_col_2, selected_col_3, selected_col_4 = st.columns(4)

        with selected_col_1:
            st.metric("Predicted Direction", predicted_label)

        with selected_col_2:
            st.metric(
                "Probability",
                f"{latest_live_prediction['prediction_probability']:.2%}",
            )

        with selected_col_3:
            st.metric("Status", latest_live_prediction["status"])

        with selected_col_4:
            st.metric("Model", latest_live_prediction["model_name"])

        if latest_live_prediction["status"] == "PENDING":
            st.info("This prediction is waiting for the next available market price.")
        else:
            actual_direction = int(latest_live_prediction["actual_direction"])
            actual_label = "UP" if actual_direction == 1 else "DOWN"
            was_correct = bool(latest_live_prediction["prediction_correct"])

            result_col_1, result_col_2, result_col_3 = st.columns(3)

            with result_col_1:
                st.metric("Actual Direction", actual_label)

            with result_col_2:
                st.metric("Actual Price", f"{latest_live_prediction['actual_price']:,.2f}")

            with result_col_3:
                st.metric("Result", "CORRECT" if was_correct else "WRONG")

            if was_correct:
                st.success("The completed live prediction was correct.")
            else:
                st.error("The completed live prediction was wrong.")

        st.subheader("Latest Live Reflection")
        st.write(latest_live_prediction["reflection_message"])

        st.subheader("Pending Predictions")
        if pending_df.empty:
            st.info("No pending live predictions right now.")
        else:
            st.dataframe(pending_df, width="stretch")

        st.subheader("Completed Predictions")
        if completed_df.empty:
            st.info("No completed live predictions yet. They will appear after newer market prices arrive.")
        else:
            st.dataframe(completed_df, width="stretch")

        st.subheader("Selected Asset Live History")
        st.dataframe(selected_live_df, width="stretch")

    except Exception:
        st.warning("Live prediction table not found yet. Run the live prediction builder first.")


def show_model_ratings():
    st.header("Prediction Rating + Model Reflection")
    st.caption("Historical predictions are scored, rated, and translated into model mood, trust impact, and reflection messages.")

    try:
        prediction_rating_summary_df = read_sql(prediction_rating_summary_query)
        prediction_ratings_df = read_sql(prediction_ratings_query)

        if prediction_rating_summary_df.empty or prediction_ratings_df.empty:
            st.info("No prediction ratings available yet. Run scripts/build_prediction_ratings.py first.")
        else:
            overall_rating_df = prediction_rating_summary_df[
                prediction_rating_summary_df["summary_type"] == "OVERALL"
            ]
            asset_rating_summary_df = prediction_rating_summary_df[
                prediction_rating_summary_df["summary_type"] == "ASSET"
            ]
            overall_rating = overall_rating_df.iloc[0]

            rating_col_1, rating_col_2, rating_col_3, rating_col_4 = st.columns(4)

            with rating_col_1:
                st.metric("Lifetime Rating", f"{overall_rating['lifetime_rating']:.2f} / 5")

            with rating_col_2:
                st.metric("Recent Rating", f"{overall_rating['recent_30_rating']:.2f} / 5")

            with rating_col_3:
                st.metric("Overall Accuracy", f"{overall_rating['overall_accuracy']:.2%}")

            with rating_col_4:
                st.metric("Trust Status", str(overall_rating["trust_status"]).replace("_", " "))

            rating_asset = st.selectbox(
                "Select Rating Asset",
                asset_rating_summary_df["asset"].dropna().unique().tolist(),
            )

            selected_asset_summary = asset_rating_summary_df[
                asset_rating_summary_df["asset"] == rating_asset
            ].iloc[0]

            selected_asset_ratings_df = prediction_ratings_df[
                prediction_ratings_df["asset"] == rating_asset
            ]

            latest_rating = selected_asset_ratings_df.iloc[0]

            asset_rating_col_1, asset_rating_col_2, asset_rating_col_3 = st.columns(3)

            with asset_rating_col_1:
                st.metric("Asset Rating", f"{selected_asset_summary['asset_wise_rating']:.2f} / 5")

            with asset_rating_col_2:
                st.metric("Asset Accuracy", f"{selected_asset_summary['asset_wise_accuracy']:.2%}")

            with asset_rating_col_3:
                st.metric("Model Mood", latest_rating["model_mood"])

            trust_impact = latest_rating["trust_impact"]

            if trust_impact == "TRUST_INCREASING":
                st.success("The latest rated prediction increased model trust.")
            elif trust_impact == "TRUST_STABLE":
                st.info("The latest rated prediction kept model trust stable.")
            elif trust_impact == "TRUST_DECREASING":
                st.warning("The latest rated prediction reduced model trust.")
            else:
                st.error("The latest rated prediction needs review.")

            st.subheader("Latest Model Reflection")
            st.write(latest_rating["reflection_message"])

            st.subheader("Asset Rating Summary")
            st.dataframe(asset_rating_summary_df, width="stretch")

            st.subheader("Prediction Rating History")
            st.dataframe(selected_asset_ratings_df, width="stretch")

    except Exception:
        st.warning("Prediction ratings table not found yet. Run the prediction rating builder first.")


def show_backtesting():
    st.header("Backtesting Performance")
    st.caption("Simulates a simple long/short strategy using the model's predicted direction and realized next return.")

    try:
        backtest_summary_df = read_sql(backtest_summary_query)
        backtest_results_df = read_sql(backtest_results_query)

        if backtest_summary_df.empty or backtest_results_df.empty:
            st.info("No backtest results available yet. Run scripts/build_backtest_results.py first.")
        else:
            overall_backtest_df = backtest_summary_df[
                backtest_summary_df["summary_type"] == "OVERALL"
            ]

            asset_backtest_summary_df = backtest_summary_df[
                backtest_summary_df["summary_type"] == "ASSET"
            ]

            overall_backtest = overall_backtest_df.iloc[0]

            backtest_col_1, backtest_col_2, backtest_col_3, backtest_col_4 = st.columns(4)

            with backtest_col_1:
                st.metric("Total Return", f"{overall_backtest['cumulative_return']:.2%}")

            with backtest_col_2:
                st.metric("Win Rate", f"{overall_backtest['win_rate']:.2%}")

            with backtest_col_3:
                st.metric("Average Trade Return", f"{overall_backtest['average_trade_return']:.4%}")

            with backtest_col_4:
                st.metric("Total Trades", int(overall_backtest["total_trades"]))

            backtest_asset = st.selectbox(
                "Select Backtest Asset",
                asset_backtest_summary_df["asset"].dropna().unique().tolist(),
            )

            selected_backtest_summary = asset_backtest_summary_df[
                asset_backtest_summary_df["asset"] == backtest_asset
            ].iloc[0]

            selected_backtest_history_df = backtest_results_df[
                backtest_results_df["asset"] == backtest_asset
            ]

            asset_backtest_col_1, asset_backtest_col_2, asset_backtest_col_3 = st.columns(3)

            with asset_backtest_col_1:
                st.metric("Asset Total Return", f"{selected_backtest_summary['cumulative_return']:.2%}")

            with asset_backtest_col_2:
                st.metric("Asset Win Rate", f"{selected_backtest_summary['win_rate']:.2%}")

            with asset_backtest_col_3:
                st.metric("Asset Avg Trade Return", f"{selected_backtest_summary['average_trade_return']:.4%}")

            if overall_backtest["cumulative_return"] > 0:
                st.success("The backtest strategy is profitable over the tested period.")
            elif overall_backtest["cumulative_return"] < 0:
                st.error("The backtest strategy is losing over the tested period.")
            else:
                st.info("The backtest strategy is flat over the tested period.")

            st.subheader("Asset-Wise Backtest Summary")
            st.dataframe(asset_backtest_summary_df, width="stretch")

            st.subheader("Backtest History")
            st.dataframe(selected_backtest_history_df, width="stretch")

    except Exception:
        st.warning("Backtest tables not found yet. Run the backtest builder first.")


with st.sidebar:
    st.header("Dashboard Controls")
    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Simple Market View",
            "Market Data",
            "Macro Data",
            "News Sentiment",
            "Signals & Intelligence",
            "ML Predictions",
            "Live Forward Predictions",
            "Model Ratings",
            "Backtesting",
            "Guide",
        ],
    )

    refresh_clicked = st.button("Refresh Data")

    if refresh_clicked:
        st.session_state["last_refresh_click"] = datetime.now()

    if "last_refresh_click" in st.session_state:
        st.success(
            f"Dashboard refreshed at {st.session_state['last_refresh_click'].strftime('%H:%M:%S')}"
        )

    st.write("Use navigation to focus on one part of the system at a time.")


show_intro()

if page == "Overview":
    show_overview()
elif page == "Simple Market View":
    show_simple_market_view()
elif page == "Market Data":
    show_market_data()
elif page == "Macro Data":
    show_macro_data()
elif page == "News Sentiment":
    show_news_sentiment()
elif page == "Signals & Intelligence":
    show_signals_and_intelligence()
elif page == "ML Predictions":
    show_ml_predictions()
elif page == "Live Forward Predictions":
    show_live_forward_predictions()
elif page == "Model Ratings":
    show_model_ratings()
elif page == "Backtesting":
    show_backtesting()
else:
    show_dashboard_guide()
