# Twitter + LinkedIn Competitor Intelligence

Daily competitive intelligence for selected companies from Twitter (via TwitterAPI.io) and LinkedIn (via ScrapIn), summarized with Gemini and posted to Slack.

## How It Runs (GitHub Actions)
- Daily Twitter tracker: `.github/workflows/daily-monitor.yml`
- Daily LinkedIn tracker: `.github/workflows/competitor-news.yml`
- Manual tests: `test-twitter-tracker.yml`, `test-linkedin-tracker.yml` (post to a test Slack webhook)

Required repository secrets (Settings → Secrets and variables → Actions → Secrets):
- `TWITTERAPI_IO_KEY`
- `GEMINI_API_KEY`
- `SLACK_WEBHOOK_URL` (and `TEST_SLACK_WEBHOOK_URL` for test workflows)
- `SCRAPIN_API` (LinkedIn only)

## Configuration
Master account lists in repo root:
- Twitter: `twitter_accounts.txt` (`username:Company` per line)
- LinkedIn: `linkedin_accounts.txt` (company page URLs)

Local `config.json` (optional for local runs):
```json
{
  "twitterapi_io_key": "...",
  "gemini_api_key": "...",
  "gemini_model": "gemini-2.0-flash",
  "slack_webhook_url": "..."
}
```

## Local Run (optional)
```bash
pip install -r requirements.txt
python twitter_monitor.py           # Twitter summary (uses twitter_accounts.txt)
python daily_complete_scan.py       # One-pass daily summary to Slack
python linkedin_monitor.py          # LinkedIn summary (uses linkedin_accounts.txt)
```

Notes
- Model is configurable via `gemini_model` (defaults to `gemini-2.0-flash`).
- Slack output groups items by category and company, uses short headlines, and deduplicates near-duplicates.
