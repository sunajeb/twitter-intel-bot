#!/bin/bash
# Daily Twitter Monitor Script
# Add this to your crontab to run daily at 9 AM: 0 9 * * * /path/to/run_daily.sh

cd "$(dirname "$0")"
source twitter_monitor_env/bin/activate
python3 twitter_monitor.py >> monitor.log 2>&1