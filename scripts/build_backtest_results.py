import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
from config.database import engine


BACKTEST_QUERY = """
SELECT
    p.asset,
    p.price_date,
    p.price,
    d.next_price_date,
    d.next_price,
    d.target_next_return AS actual_next_return,
    p.target_direction,
    p.predicted_direction,
    p.prediction_probability,
    p.model_name,
    p.model_accuracy
FROM model_predictions p
LEFT JOIN model_dataset d
    ON p.asset = d.asset
    AND p.price_date = d.price_date
ORDER BY p.price_date, p.asset;
"""


def build_backtest_rows(predictions_df):
    backtest_df = predictions_df.dropna(
        subset=[
            "actual_next_return",
            "target_direction",
            "predicted_direction",
        ]
    ).copy()

    if backtest_df.empty:
        raise ValueError("No complete prediction rows found for backtesting.")

    backtest_df["price_date"] = pd.to_datetime(backtest_df["price_date"])
    backtest_df["next_price_date"] = pd.to_datetime(backtest_df["next_price_date"])
    backtest_df["target_direction"] = backtest_df["target_direction"].astype(int)
    backtest_df["predicted_direction"] = backtest_df["predicted_direction"].astype(int)

    backtest_df["strategy_position"] = backtest_df["predicted_direction"].map(
        {
            1: "LONG",
            0: "SHORT",
        }
    )

    backtest_df["strategy_return"] = backtest_df.apply(
        lambda row: row["actual_next_return"]
        if row["predicted_direction"] == 1
        else -row["actual_next_return"],
        axis=1,
    )

    backtest_df["prediction_correct"] = (
        backtest_df["predicted_direction"] == backtest_df["target_direction"]
    )

    backtest_df["trade_result"] = backtest_df["strategy_return"].apply(
        lambda value: "WIN" if value > 0 else "LOSS" if value < 0 else "FLAT"
    )

    backtest_df = backtest_df.sort_values(["asset", "price_date"]).copy()
    backtest_df["asset_cumulative_return"] = (
        backtest_df.groupby("asset")["strategy_return"]
        .transform(lambda values: (1 + values).cumprod() - 1)
    )

    daily_portfolio_df = (
        backtest_df.groupby("price_date", as_index=False)["strategy_return"]
        .mean()
        .sort_values("price_date")
    )
    daily_portfolio_df["overall_cumulative_return"] = (
        (1 + daily_portfolio_df["strategy_return"]).cumprod() - 1
    )

    backtest_df = backtest_df.merge(
        daily_portfolio_df[["price_date", "overall_cumulative_return"]],
        on="price_date",
        how="left",
    )
    backtest_df["created_at"] = datetime.now()

    return backtest_df.sort_values(["price_date", "asset"]).reset_index(drop=True)


def summary_row(summary_type, asset, rows_df, overall_cumulative_return):
    total_trades = len(rows_df)
    winning_trades = (rows_df["trade_result"] == "WIN").sum()
    losing_trades = (rows_df["trade_result"] == "LOSS").sum()
    flat_trades = (rows_df["trade_result"] == "FLAT").sum()

    if summary_type == "OVERALL":
        cumulative_return = overall_cumulative_return
    else:
        cumulative_return = (1 + rows_df["strategy_return"]).prod() - 1

    return {
        "summary_type": summary_type,
        "asset": asset,
        "model_name": rows_df["model_name"].iloc[-1],
        "total_trades": total_trades,
        "winning_trades": int(winning_trades),
        "losing_trades": int(losing_trades),
        "flat_trades": int(flat_trades),
        "win_rate": winning_trades / total_trades if total_trades else 0,
        "average_trade_return": rows_df["strategy_return"].mean(),
        "cumulative_return": cumulative_return,
        "best_trade_return": rows_df["strategy_return"].max(),
        "worst_trade_return": rows_df["strategy_return"].min(),
        "created_at": datetime.now(),
    }


def build_summary_rows(backtest_df):
    daily_returns = (
        backtest_df.groupby("price_date")["strategy_return"]
        .mean()
        .sort_index()
    )
    overall_cumulative_return = (1 + daily_returns).prod() - 1

    summary_rows = [
        summary_row(
            "OVERALL",
            "ALL",
            backtest_df,
            overall_cumulative_return,
        )
    ]

    for asset, asset_df in backtest_df.groupby("asset"):
        summary_rows.append(
            summary_row(
                "ASSET",
                asset,
                asset_df,
                overall_cumulative_return,
            )
        )

    return pd.DataFrame(summary_rows)


def main():
    predictions_df = pd.read_sql(BACKTEST_QUERY, engine)

    if predictions_df.empty:
        raise ValueError("model_predictions table is empty. Run scripts.train_direction_model first.")

    backtest_df = build_backtest_rows(predictions_df)
    summary_df = build_summary_rows(backtest_df)

    backtest_df.to_sql(
        "backtest_results",
        engine,
        if_exists="replace",
        index=False,
    )

    summary_df.to_sql(
        "backtest_summary",
        engine,
        if_exists="replace",
        index=False,
    )

    overall_summary = summary_df[summary_df["summary_type"] == "OVERALL"].iloc[0]
    asset_summary = summary_df[summary_df["summary_type"] == "ASSET"].copy()

    print(f"Built {len(backtest_df)} rows into backtest_results.")
    print(f"Built {len(summary_df)} rows into backtest_summary.")
    print()
    print(f"Total trades: {int(overall_summary['total_trades'])}")
    print(f"Total return: {overall_summary['cumulative_return']:.2%}")
    print(f"Win rate: {overall_summary['win_rate']:.2%}")
    print(f"Average trade return: {overall_summary['average_trade_return']:.4%}")
    print()
    print("Asset-wise backtest summary:")
    print(
        asset_summary[
            [
                "asset",
                "total_trades",
                "win_rate",
                "average_trade_return",
                "cumulative_return",
            ]
        ].to_string(index=False)
    )
    print()
    print("Latest backtest rows:")
    print(
        backtest_df[
            [
                "asset",
                "price_date",
                "strategy_position",
                "actual_next_return",
                "strategy_return",
                "trade_result",
                "asset_cumulative_return",
            ]
        ].tail(20).to_string(index=False)
    )


if __name__ == "__main__":
    main()
