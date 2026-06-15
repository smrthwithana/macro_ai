@echo off
cd /d C:\Users\samar\OneDrive\Documents\macro_ai

if not exist logs (
    mkdir logs
)

echo ======================================== >> logs\daily_update.log
echo Daily update started at %date% %time% >> logs\daily_update.log
echo ======================================== >> logs\daily_update.log

call venv\Scripts\activate

python -m scripts.run_daily_update >> logs\daily_update.log 2>&1

echo ======================================== >> logs\daily_update.log
echo Daily update finished at %date% %time% >> logs\daily_update.log
echo. >> logs\daily_update.log
