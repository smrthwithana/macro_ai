import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

tasks = [
    ("Market data ingestion", "ingestion.run_daily"),
    ("FRED macro ingestion", "ingestion.run_fred_macro_daily"),
    ("Real news sentiment fetch", "scripts.fetch_real_news_sentiment"),
    ("Market signals build", "scripts.build_market_signals"),
    ("Rule-based signals build", "scripts.build_rule_based_signals"),
    ("Combined intelligence build", "scripts.build_combined_intelligence")
]


def run_task(task_name, module_name):
    print()
    print("=" * 80)
    print(f"Starting: {task_name}")
    print(f"Module: {module_name}")
    print(f"Time: {datetime.now()}")
    print("=" * 80)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            module_name
        ],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"{task_name} failed")

    print(f"Completed: {task_name}")


def main():
    print("Daily update started")
    print(f"Start time: {datetime.now()}")

    for task_name, module_name in tasks:
        run_task(task_name, module_name)

    print()
    print("Daily update completed successfully")
    print(f"End time: {datetime.now()}")


if __name__ == "__main__":
    main()
