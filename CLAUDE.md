# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Twitter & LinkedIn Intelligence Bot - A competitive intelligence monitoring system that tracks Twitter and LinkedIn accounts for important updates, analyzes them with AI, and sends notifications via Slack.

## Security Note

**IMPORTANT**: All API keys are stored as environment variables and are NOT pushed to GitHub. The following environment variables are used:
- `SCRAPIN_API` - ScrapIn API key for LinkedIn data
- `TWITTERAPI_IO_KEY` - TwitterAPI.io key for Twitter data
- `GEMINI_API_KEY` - Google Gemini API key for AI analysis
- `SLACK_WEBHOOK_URL` - Slack webhook for notifications
- `TWITTER_BEARER_TOKEN` - Twitter API bearer token

Never hardcode API keys in the source code. All keys should be loaded from environment variables or config.json (which should never be committed).

## Key Commands

### Development Setup
```bash
# Create and activate virtual environment
python3 -m venv twitter_monitor_env
source twitter_monitor_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys (copy from config.example.json)
cp config.example.json config.json
# Edit config.json with your API keys
```

### Running the Application
```bash
# Twitter Monitoring
python3 twitter_monitor.py

# LinkedIn Monitoring
python3 linkedin_monitor.py

# Start Slack bot server (port 3000)
python3 slack_bot.py

# Run daily summary
python3 daily_summary.py

# Execute daily script (activates venv automatically)
./run_daily.sh
```

### Testing Commands
```bash
# Test single account monitoring
python3 test_single_account.py

# Test API connectivity
python3 test_api_key.py

# Manual full scan of all accounts
python3 manual_full_scan.py

# Test Twitter API limits
python3 test_twitter_limits.py

# Debug OpenAI/Gemini response
python3 debug_openai_response.py

# Test LinkedIn monitoring
python3 test_linkedin_manual.py [YYYY-MM-DD]

# Test LinkedIn formatting
python3 test_linkedin_format.py

# Add LinkedIn accounts
python3 add_linkedin_account.py <linkedin-url>
python3 add_linkedin_account.py list
```

## Architecture Overview

### Core Components
1. **twitter_monitor.py** - Main orchestrator that coordinates tweet fetching, analysis, and notifications
2. **linkedin_monitor.py** - LinkedIn monitoring with ScrapIn API integration and Gemini analysis
3. **twitter_api_io_client.py** - Handles Twitter data fetching via TwitterAPI.io (bypasses rate limits)
4. **slack_bot.py** - Flask server handling Slack slash commands (`/intel`)
5. **daily_summary.py** - Accumulates daily intelligence and sends scheduled summaries
6. **competitor_api_formatter.py** - Formats API responses for Slack with hyperlinks and emojis
7. **account_rotation.py** - Manages API rate limits through account rotation

### Data Flow
```
Accounts.txt → TwitterAPI.io → Thread Grouping → Gemini AI Analysis → 
Formatting → Slack Notification → Daily Summary Accumulation
```

### Key Design Patterns
- **Configuration-driven**: All settings in `config.json`
- **Modular architecture**: Clear separation of concerns
- **Graceful degradation**: Multiple fallback mechanisms for API failures
- **State persistence**: JSON files for rotation state and daily intelligence
- **Event-driven notifications**: Immediate alerts + daily summaries

### Important Files
- `config.json` - API keys and configuration (TwitterAPI.io, Gemini, Slack)
- `twitter_accounts.txt` - Twitter accounts to monitor (one per line)
- `linkedin_accounts.txt` - LinkedIn company URLs to monitor (one per line)
  (Deprecated) `accounts_priority.txt` removed. Use `twitter_accounts.txt` only.
- `rotation_state.json` - Tracks account rotation for API limits
- `daily_intelligence.json` - Accumulates intelligence for daily summaries

### API Integrations
1. **TwitterAPI.io** - Third-party Twitter API (6-second delay for free tier)
   - Uses `TWITTERAPI_IO_KEY` environment variable
2. **ScrapIn API** - LinkedIn post fetching with company activity data
   - Uses `SCRAPIN_API` environment variable
3. **Google Gemini AI** - Analyzes posts for competitive intelligence (gemini-2.0-flash-exp)
   - Uses `GEMINI_API_KEY` environment variable
4. **Slack Webhooks** - Sends formatted notifications with hyperlinked company names
   - Uses `SLACK_WEBHOOK_URL` environment variable

### Error Handling Strategy
- Try-catch blocks at all integration points
- Rate limit detection with account skipping
- Fallback to "Nothing important today" on failures
- Connection retry with exponential backoff
- Comprehensive logging for debugging

### Development Tips
- Monitor `rotation_state.json` to debug account rotation issues
- Check `daily_intelligence.json` for accumulated data
- Use manual test scripts to verify individual components
- Slack formatting uses hyperlinked company names: `<https://company.com|Company Name>`
- AI prompts filter for: funding, product launches, partnerships, acquisitions, leadership changes
