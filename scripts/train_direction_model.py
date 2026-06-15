import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from config.database import engine

query = """
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

df = pd.read_sql(query, engine)

if df.empty:
    raise ValueError("model_dataset is empty. Run scripts.build_model_dataset first.")

df["price_date"] = pd.to_datetime(df["price_date"])

features = [
    "daily_return",
    "weekly_return",
    "momentum",
    "volatility",
    "macro_gdp",
    "macro_cpi",
    "macro_interest_rate",
    "sentiment_score",
    "rule_score"
]

model_df = df.dropna(
    subset=features + ["target_direction"]
).copy()

asset_dummies = pd.get_dummies(model_df["asset"], prefix="asset")

X = pd.concat(
    [
        model_df[features],
        asset_dummies
    ],
    axis=1
)

y = model_df["target_direction"].astype(int)

split_index = int(len(model_df) * 0.8)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

test_metadata = model_df.iloc[split_index:].copy()

model = Pipeline(
    [
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=1000))
    ]
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, predictions)

prediction_df = test_metadata[
    [
        "asset",
        "price_date",
        "price",
        "target_direction"
    ]
].copy()

prediction_df["predicted_direction"] = predictions
prediction_df["prediction_probability"] = probabilities
prediction_df["model_name"] = "logistic_regression_v1"
prediction_df["model_accuracy"] = accuracy
prediction_df["created_at"] = datetime.now()

prediction_df.to_sql(
    "model_predictions",
    engine,
    if_exists="replace",
    index=False
)

print(f"Trained model on {len(X_train)} rows.")
print(f"Tested model on {len(X_test)} rows.")
print(f"Accuracy: {accuracy:.4f}")
print()
print("Classification report:")
print(classification_report(y_test, predictions))
print()
print("Latest predictions:")
print(
    prediction_df[
        [
            "asset",
            "price_date",
            "target_direction",
            "predicted_direction",
            "prediction_probability"
        ]
    ].tail(20)
)
