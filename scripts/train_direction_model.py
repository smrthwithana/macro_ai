import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from config.database import engine


MODEL_DATASET_QUERY = """
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
    target_direction
FROM model_dataset
ORDER BY price_date;
"""

FEATURES = [
    "daily_return",
    "weekly_return",
    "momentum",
    "volatility",
    "macro_gdp",
    "macro_cpi",
    "macro_interest_rate",
    "sentiment_score",
    "rule_score",
]


def build_feature_matrix(model_df):
    asset_dummies = pd.get_dummies(model_df["asset"], prefix="asset").astype(int)

    return pd.concat(
        [
            model_df[FEATURES],
            asset_dummies,
        ],
        axis=1,
    )


def candidate_models():
    return {
        "logistic_regression_v1": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(max_iter=1000)),
            ]
        ),
        "random_forest_v1": RandomForestClassifier(
            n_estimators=250,
            max_depth=8,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
    }


def evaluate_model(model_name, model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)

    return {
        "model_name": model_name,
        "model": model,
        "predictions": predictions,
        "probabilities": probabilities,
        "accuracy": accuracy,
        "precision_score": precision,
        "recall_score": recall,
        "f1_score": f1,
        "classification_report": classification_report(
            y_test,
            predictions,
            zero_division=0,
        ),
    }


def main():
    df = pd.read_sql(MODEL_DATASET_QUERY, engine)

    if df.empty:
        raise ValueError("model_dataset is empty. Run scripts.build_model_dataset first.")

    df["price_date"] = pd.to_datetime(df["price_date"])

    model_df = df.dropna(
        subset=FEATURES + ["target_direction"]
    ).copy()
    model_df = model_df.sort_values("price_date").reset_index(drop=True)

    if len(model_df) < 20:
        raise ValueError("Not enough model_dataset rows to train and test models.")

    X = build_feature_matrix(model_df)
    y = model_df["target_direction"].astype(int)

    split_index = int(len(model_df) * 0.8)

    if split_index == 0 or split_index >= len(model_df):
        raise ValueError("Invalid train/test split. Add more model_dataset rows.")

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    test_metadata = model_df.iloc[split_index:].copy()

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

    created_at = datetime.now()

    performance_df = pd.DataFrame(
        [
            {
                "model_name": result["model_name"],
                "is_best_model": result["model_name"] == best_result["model_name"],
                "train_rows": len(X_train),
                "test_rows": len(X_test),
                "accuracy": result["accuracy"],
                "precision_score": result["precision_score"],
                "recall_score": result["recall_score"],
                "f1_score": result["f1_score"],
                "classification_report": result["classification_report"],
                "created_at": created_at,
            }
            for result in model_results
        ]
    )

    prediction_df = test_metadata[
        [
            "asset",
            "price_date",
            "price",
            "target_direction",
        ]
    ].copy()

    prediction_df["predicted_direction"] = best_result["predictions"]
    prediction_df["prediction_probability"] = best_result["probabilities"]
    prediction_df["model_name"] = best_result["model_name"]
    prediction_df["model_accuracy"] = best_result["accuracy"]
    prediction_df["created_at"] = created_at

    performance_df.to_sql(
        "model_performance_summary",
        engine,
        if_exists="replace",
        index=False,
    )

    prediction_df.to_sql(
        "model_predictions",
        engine,
        if_exists="replace",
        index=False,
    )

    print(f"Trained models on {len(X_train)} rows.")
    print(f"Tested models on {len(X_test)} rows.")
    print()
    print("Model comparison:")
    print(
        performance_df[
            [
                "model_name",
                "is_best_model",
                "accuracy",
                "precision_score",
                "recall_score",
                "f1_score",
            ]
        ].to_string(index=False)
    )
    print()
    print(f"Best model: {best_result['model_name']}")
    print(f"Best accuracy: {best_result['accuracy']:.4f}")
    print()
    print("Best model classification report:")
    print(best_result["classification_report"])
    print()
    print("Latest best-model predictions:")
    print(
        prediction_df[
            [
                "asset",
                "price_date",
                "target_direction",
                "predicted_direction",
                "prediction_probability",
                "model_name",
            ]
        ].tail(20)
    )


if __name__ == "__main__":
    main()
