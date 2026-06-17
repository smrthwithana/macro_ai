import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
from sqlalchemy import text
from config.database import engine
from scripts.build_prediction_ratings import (
    confidence_bucket,
    direction_label,
    model_mood,
    star_rating,
    trust_impact,
)
from scripts.train_direction_model import (
    FEATURES,
    MODEL_DATASET_QUERY,
    build_feature_matrix,
    candidate_models,
    evaluate_model,
)


LIVE_INPUT_QUERY = """
WITH ranked_intelligence AS (
    SELECT
        asset,
        price_date,
        price,
        daily_return,
        weekly_return,
        momentum,
        volatility,
        macro_gdp,
        macro_cpi,
        macro_interest_rate,
        sentiment_score,
        rule_score,
        ROW_NUMBER() OVER (
            PARTITION BY asset
            ORDER BY price_date DESC, created_at DESC
        ) AS row_num
    FROM combined_intelligence_signals
)
SELECT
    asset,
    price_date,
    price,
    daily_return,
    weekly_return,
    momentum,
    volatility,
    macro_gdp,
    macro_cpi,
    macro_interest_rate,
    sentiment_score,
    rule_score
FROM ranked_intelligence
WHERE row_num = 1
ORDER BY asset;
"""

CREATE_LIVE_PREDICTIONS_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS live_predictions (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(50),
    prediction_date DATE,
    prediction_price DOUBLE PRECISION,
    predicted_direction INTEGER,
    prediction_probability DOUBLE PRECISION,
    model_name VARCHAR(100),
    status VARCHAR(20),
    actual_date DATE,
    actual_price DOUBLE PRECISION,
    actual_direction INTEGER,
    prediction_correct BOOLEAN,
    star_rating INTEGER,
    model_mood VARCHAR(30),
    trust_impact VARCHAR(40),
    reflection_message TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
"""

PENDING_PREDICTIONS_QUERY = """
SELECT
    id,
    asset,
    prediction_date,
    prediction_price,
    predicted_direction,
    prediction_probability,
    model_name
FROM live_predictions
WHERE status = 'PENDING'
ORDER BY prediction_date, asset;
"""

NEXT_MARKET_PRICE_QUERY = """
SELECT
    CAST(timestamp AS DATE) AS actual_date,
    price AS actual_price
FROM market_data
WHERE asset = :asset
AND CAST(timestamp AS DATE) > :prediction_date
ORDER BY timestamp ASC
LIMIT 1;
"""

DUPLICATE_PREDICTION_QUERY = """
SELECT COUNT(*)
FROM live_predictions
WHERE asset = :asset
AND prediction_date = :prediction_date;
"""

INSERT_PENDING_PREDICTION_QUERY = """
INSERT INTO live_predictions (
    asset,
    prediction_date,
    prediction_price,
    predicted_direction,
    prediction_probability,
    model_name,
    status,
    reflection_message,
    created_at,
    updated_at
)
VALUES (
    :asset,
    :prediction_date,
    :prediction_price,
    :predicted_direction,
    :prediction_probability,
    :model_name,
    'PENDING',
    :reflection_message,
    :created_at,
    :updated_at
);
"""

UPDATE_COMPLETED_PREDICTION_QUERY = """
UPDATE live_predictions
SET
    status = 'COMPLETED',
    actual_date = :actual_date,
    actual_price = :actual_price,
    actual_direction = :actual_direction,
    prediction_correct = :prediction_correct,
    star_rating = :star_rating,
    model_mood = :model_mood,
    trust_impact = :trust_impact,
    reflection_message = :reflection_message,
    updated_at = :updated_at
WHERE id = :id;
"""


def prepare_model_dataset():
    df = pd.read_sql(MODEL_DATASET_QUERY, engine)

    if df.empty:
        raise ValueError("model_dataset is empty. Run scripts.build_model_dataset first.")

    df["price_date"] = pd.to_datetime(df["price_date"])

    model_df = df.dropna(
        subset=FEATURES + ["target_direction"]
    ).copy()
    model_df = model_df.sort_values("price_date").reset_index(drop=True)

    if len(model_df) < 20:
        raise ValueError("Not enough model_dataset rows to train a live prediction model.")

    X = build_feature_matrix(model_df)
    y = model_df["target_direction"].astype(int)

    split_index = int(len(model_df) * 0.8)

    if split_index == 0 or split_index >= len(model_df):
        raise ValueError("Invalid live prediction train/test split. Add more model rows.")

    return model_df, X, y, split_index


def train_best_model():
    model_df, X, y, split_index = prepare_model_dataset()

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]
    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    model_results = []

    for model_name, model in candidate_models().items():
        model_results.append(
            evaluate_model(
                model_name,
                model,
                X_train,
                X_test,
                y_train,
                y_test,
            )
        )

    best_result = sorted(
        model_results,
        key=lambda result: (
            result["accuracy"],
            result["f1_score"],
        ),
        reverse=True,
    )[0]

    return {
        "model": best_result["model"],
        "model_name": best_result["model_name"],
        "model_accuracy": best_result["accuracy"],
        "feature_columns": X.columns,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "source_rows": len(model_df),
    }


def prepare_live_inputs(feature_columns):
    live_df = pd.read_sql(LIVE_INPUT_QUERY, engine)

    if live_df.empty:
        raise ValueError("combined_intelligence_signals is empty. Run scripts.build_combined_intelligence first.")

    live_df["price_date"] = pd.to_datetime(live_df["price_date"])

    for feature in FEATURES:
        live_df[feature] = pd.to_numeric(live_df[feature], errors="coerce").fillna(0)

    live_X = build_feature_matrix(live_df)
    live_X = live_X.reindex(columns=feature_columns, fill_value=0)

    return live_df, live_X


def predict_up_probabilities(model, X):
    probabilities = model.predict_proba(X)
    classes = list(getattr(model, "classes_", []))

    if 1 in classes:
        up_index = classes.index(1)
    else:
        up_index = 1

    return probabilities[:, up_index]


def live_reflection(asset, predicted_direction, actual_direction, probability, is_correct, rating):
    predicted = direction_label(predicted_direction)
    actual = direction_label(actual_direction)
    bucket = confidence_bucket(probability).lower()

    if is_correct:
        return (
            f"Live prediction for {asset} was correct. I predicted {predicted} "
            f"with {bucket} confidence ({probability:.2%}), and the next market price confirmed it."
        )

    if rating <= 2:
        return (
            f"Live prediction for {asset} was wrong. I predicted {predicted} "
            f"with {bucket} confidence ({probability:.2%}), but the next market move was {actual}. "
            f"This should reduce trust in similar live signals."
        )

    return (
        f"Live prediction for {asset} missed. I predicted {predicted}, but the next market move was {actual}. "
        f"Because confidence was {bucket}, this is a caution signal rather than a major penalty."
    )


def complete_pending_predictions():
    pending_df = pd.read_sql(PENDING_PREDICTIONS_QUERY, engine)

    if pending_df.empty:
        return 0

    completed_count = 0
    now = datetime.now()

    with engine.begin() as conn:
        for _, row in pending_df.iterrows():
            next_price_row = conn.execute(
                text(NEXT_MARKET_PRICE_QUERY),
                {
                    "asset": row["asset"],
                    "prediction_date": row["prediction_date"],
                },
            ).mappings().first()

            if not next_price_row:
                continue

            actual_price = float(next_price_row["actual_price"])
            prediction_price = float(row["prediction_price"])
            actual_direction = 1 if actual_price > prediction_price else 0
            predicted_direction = int(row["predicted_direction"])
            prediction_probability = float(row["prediction_probability"])
            prediction_correct = predicted_direction == actual_direction

            bucket = confidence_bucket(prediction_probability)
            rating = star_rating(prediction_correct, bucket)
            mood = model_mood(rating)
            impact = trust_impact(rating)
            reflection = live_reflection(
                row["asset"],
                predicted_direction,
                actual_direction,
                prediction_probability,
                prediction_correct,
                rating,
            )

            conn.execute(
                text(UPDATE_COMPLETED_PREDICTION_QUERY),
                {
                    "id": int(row["id"]),
                    "actual_date": next_price_row["actual_date"],
                    "actual_price": actual_price,
                    "actual_direction": actual_direction,
                    "prediction_correct": prediction_correct,
                    "star_rating": rating,
                    "model_mood": mood,
                    "trust_impact": impact,
                    "reflection_message": reflection,
                    "updated_at": now,
                },
            )

            completed_count += 1

    return completed_count


def create_pending_predictions(model_context):
    live_df, live_X = prepare_live_inputs(model_context["feature_columns"])
    predictions = model_context["model"].predict(live_X)
    probabilities = predict_up_probabilities(model_context["model"], live_X)

    inserted_count = 0
    skipped_count = 0
    now = datetime.now()

    with engine.begin() as conn:
        for index, row in live_df.reset_index(drop=True).iterrows():
            prediction_date = row["price_date"].date()
            asset = row["asset"]

            duplicate_count = conn.execute(
                text(DUPLICATE_PREDICTION_QUERY),
                {
                    "asset": asset,
                    "prediction_date": prediction_date,
                },
            ).scalar()

            if duplicate_count:
                skipped_count += 1
                continue

            predicted_direction = int(predictions[index])
            probability = float(probabilities[index])
            direction = direction_label(predicted_direction)

            conn.execute(
                text(INSERT_PENDING_PREDICTION_QUERY),
                {
                    "asset": asset,
                    "prediction_date": prediction_date,
                    "prediction_price": float(row["price"]),
                    "predicted_direction": predicted_direction,
                    "prediction_probability": probability,
                    "model_name": model_context["model_name"],
                    "reflection_message": (
                        f"Pending live prediction for {asset}: expected {direction} "
                        f"with {probability:.2%} probability. Waiting for the next available market price."
                    ),
                    "created_at": now,
                    "updated_at": now,
                },
            )

            inserted_count += 1

    return inserted_count, skipped_count


def main():
    with engine.begin() as conn:
        conn.execute(text(CREATE_LIVE_PREDICTIONS_TABLE_QUERY))

    completed_count = complete_pending_predictions()
    model_context = train_best_model()
    inserted_count, skipped_count = create_pending_predictions(model_context)

    status_counts_df = pd.read_sql(
        """
        SELECT status, COUNT(*) AS row_count
        FROM live_predictions
        GROUP BY status
        ORDER BY status;
        """,
        engine,
    )

    latest_predictions_df = pd.read_sql(
        """
        SELECT
            asset,
            prediction_date,
            prediction_price,
            predicted_direction,
            prediction_probability,
            status,
            actual_date,
            actual_price,
            prediction_correct,
            model_mood
        FROM live_predictions
        ORDER BY prediction_date DESC, asset
        LIMIT 20;
        """,
        engine,
    )

    print("Live prediction tracking complete.")
    print(f"Best live model: {model_context['model_name']}")
    print(f"Best live model accuracy: {model_context['model_accuracy']:.4f}")
    print(f"Training rows: {model_context['train_rows']}")
    print(f"Testing rows: {model_context['test_rows']}")
    print(f"Completed pending predictions: {completed_count}")
    print(f"New pending predictions: {inserted_count}")
    print(f"Skipped duplicate live predictions: {skipped_count}")
    print()
    print("Live prediction status counts:")
    print(status_counts_df.to_string(index=False))
    print()
    print("Latest live predictions:")
    print(latest_predictions_df.to_string(index=False))


if __name__ == "__main__":
    main()
