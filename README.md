# Twitter Competitor Intelligence Monitor

Monitors @DecagonAI and @SierraPlatform daily for competitive intelligence insights.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API keys in `config.json`:
   - Get Twitter Bearer Token from Twitter Developer Portal
   - Get Gemini API key from Google AI Studio
   - Create Slack webhook URL from your Slack app

3. Set up daily cron job:
```bash
crontab -e
# Add this line to run daily at 9 AM:
0 9 * * * /path/to/run_daily.sh
```

## Manual Run
```bash
python3 twitter_monitor.py
```

The system will only send notifications when important competitive intelligence is found.