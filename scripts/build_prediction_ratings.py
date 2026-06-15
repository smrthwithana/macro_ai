import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
from config.database import engine


MODEL_PREDICTIONS_QUERY = """
SELECT
    asset,
    price_date,
    price,
    target_direction,
    predicted_direction,
    prediction_probability,
    model_name,
    model_accuracy,
    created_at AS prediction_created_at
FROM model_predictions
ORDER BY price_date, asset;
"""


def direction_label(value):
    return "UP" if int(value) == 1 else "DOWN"


def confidence_bucket(probability):
    distance = abs(probability - 0.5)

    if distance >= 0.25:
        return "HIGH"
    if distance >= 0.15:
        return "MEDIUM"
    if distance >= 0.05:
        return "LOW"

    return "UNCERTAIN"


def star_rating(is_correct, bucket):
    if is_correct:
        if bucket == "HIGH":
            return 5
        if bucket == "MEDIUM":
            return 4
        return 3

    if bucket == "HIGH":
        return 1
    if bucket == "MEDIUM":
        return 2
    if bucket == "LOW":
        return 2

    return 3


def model_mood(rating):
    mood_by_rating = {
        5: "CONFIDENT",
        4: "SATISFIED",
        3: "CAUTIOUS",
        2: "CONCERNED",
        1: "DISAPPOINTED",
    }

    return mood_by_rating[rating]


def trust_impact(rating):
    if rating >= 4:
        return "TRUST_INCREASING"
    if rating == 3:
        return "TRUST_STABLE"
    if rating == 2:
        return "TRUST_DECREASING"

    return "NEEDS_REVIEW"


def trust_status(rating):
    if rating >= 4.2:
        return "STRONG_TRUST"
    if rating >= 3.5:
        return "MODERATE_TRUST"
    if rating >= 2.8:
        return "CAUTIOUS_TRUST"

    return "LOW_TRUST_NEEDS_IMPROVEMENT"


def reflection_message(row):
    asset = row["asset"]
    predicted = direction_label(row["predicted_direction"])
    actual = direction_label(row["target_direction"])
    probability = row["prediction_probability"]
    bucket = row["confidence_bucket"].lower()

    if row["prediction_correct"]:
        if row["star_rating"] >= 4:
            return (
                f"I predicted {asset} would move {predicted} with {bucket} confidence "
                f"({probability:.2%}), and it did. This signal increased trust."
            )

        return (
            f"I predicted {asset} would move {predicted}, and it did, but confidence "
            f"was only {bucket}. I should keep learning before raising conviction."
        )

    if row["star_rating"] <= 2:
        return (
            f"I predicted {asset} would move {predicted} with {bucket} confidence "
            f"({probability:.2%}), but it moved {actual}. I should reduce trust in "
            f"similar {asset} signals until more evidence improves them."
        )

    return (
        f"I predicted {asset} would move {predicted}, but it moved {actual}. "
        f"Because confidence was {bucket}, this is a caution signal rather than a major penalty."
    )


def build_rating_rows(predictions_df):
    ratings_df = predictions_df.copy()

    ratings_df["price_date"] = pd.to_datetime(ratings_df["price_date"])
    ratings_df["prediction_correct"] = (
        ratings_df["predicted_direction"].astype(int)
        == ratings_df["target_direction"].astype(int)
    )
    ratings_df["confidence_distance"] = (
        ratings_df["prediction_probability"] - 0.5
    ).abs()
    ratings_df["confidence_bucket"] = ratings_df["prediction_probability"].apply(confidence_bucket)

    ratings_df["star_rating"] = ratings_df.apply(
        lambda row: star_rating(row["prediction_correct"], row["confidence_bucket"]),
        axis=1,
    )
    ratings_df["model_mood"] = ratings_df["star_rating"].apply(model_mood)
    ratings_df["trust_impact"] = ratings_df["star_rating"].apply(trust_impact)
    ratings_df["reflection_message"] = ratings_df.apply(reflection_message, axis=1)
    ratings_df["rating_created_at"] = datetime.now()

    return ratings_df


def build_summary_rows(ratings_df):
    latest_ratings_df = ratings_df.sort_values(
        ["price_date", "rating_created_at"],
        ascending=[False, False],
    )

    lifetime_rating = ratings_df["star_rating"].mean()
    recent_30_rating = latest_ratings_df.head(30)["star_rating"].mean()
    overall_accuracy = ratings_df["prediction_correct"].mean()
    current_trust_status = trust_status(lifetime_rating)
    created_at = datetime.now()

    summary_rows = [
        {
            "summary_type": "OVERALL",
            "asset": "ALL",
            "prediction_count": len(ratings_df),
            "lifetime_rating": lifetime_rating,
            "recent_30_rating": recent_30_rating,
            "overall_accuracy": overall_accuracy,
            "asset_wise_rating": lifetime_rating,
            "asset_wise_accuracy": overall_accuracy,
            "asset_recent_30_rating": recent_30_rating,
            "trust_status": current_trust_status,
            "created_at": created_at,
        }
    ]

    for asset, asset_df in ratings_df.groupby("asset"):
        latest_asset_df = asset_df.sort_values(
            ["price_date", "rating_created_at"],
            ascending=[False, False],
        )

        asset_rating = asset_df["star_rating"].mean()

        summary_rows.append(
            {
                "summary_type": "ASSET",
                "asset": asset,
                "prediction_count": len(asset_df),
                "lifetime_rating": lifetime_rating,
                "recent_30_rating": recent_30_rating,
                "overall_accuracy": overall_accuracy,
                "asset_wise_rating": asset_rating,
                "asset_wise_accuracy": asset_df["prediction_correct"].mean(),
                "asset_recent_30_rating": latest_asset_df.head(30)["star_rating"].mean(),
                "trust_status": trust_status(asset_rating),
                "created_at": created_at,
            }
        )

    return pd.DataFrame(summary_rows)


def main():
    predictions_df = pd.read_sql(MODEL_PREDICTIONS_QUERY, engine)

    if predictions_df.empty:
        raise ValueError("model_predictions table is empty. Run scripts.train_direction_model first.")

    ratings_df = build_rating_rows(predictions_df)
    summary_df = build_summary_rows(ratings_df)

    ratings_df.to_sql(
        "prediction_ratings",
        engine,
        if_exists="replace",
        index=False,
    )

    summary_df.to_sql(
        "prediction_rating_summary",
        engine,
        if_exists="replace",
        index=False,
    )

    overall_summary = summary_df[summary_df["summary_type"] == "OVERALL"].iloc[0]
    asset_summary = summary_df[summary_df["summary_type"] == "ASSET"].copy()
    latest_reflections = ratings_df.sort_values(
        ["price_date", "rating_created_at"],
        ascending=[False, False],
    ).head(10)

    print(f"Built {len(ratings_df)} rows into prediction_ratings.")
    print(f"Built {len(summary_df)} rows into prediction_rating_summary.")
    print()
    print(f"Lifetime rating: {overall_summary['lifetime_rating']:.2f} / 5")
    print(f"Recent 30 prediction rating: {overall_summary['recent_30_rating']:.2f} / 5")
    print(f"Overall accuracy: {overall_summary['overall_accuracy']:.2%}")
    print(f"Trust status: {overall_summary['trust_status']}")
    print()
    print("Asset summary:")
    print(
        asset_summary[
            [
                "asset",
                "prediction_count",
                "asset_wise_rating",
                "asset_recent_30_rating",
                "asset_wise_accuracy",
                "trust_status",
            ]
        ].to_string(index=False)
    )
    print()
    print("Latest model reflections:")
    print(
        latest_reflections[
            [
                "asset",
                "price_date",
                "predicted_direction",
                "target_direction",
                "star_rating",
                "model_mood",
                "trust_impact",
                "reflection_message",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
