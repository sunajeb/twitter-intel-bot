# LinkedIn Monitor Setup

## Files to Commit

Make sure these files are committed to your GitHub repository:

1. **linkedin_monitor.py** - Main monitoring script
2. **linkedin_accounts.txt** - List of LinkedIn company URLs to monitor
3. **test_linkedin_format.py** - Format testing script
4. **test_linkedin_manual.py** - Manual testing script
5. **add_linkedin_account.py** - Helper to add accounts
6. **.github/workflows/competitor-news.yml** - Updated for LinkedIn daily monitoring
7. **.github/workflows/test-linkedin-tracker.yml** - Updated for test runs

## GitHub Secrets Required

Make sure these secrets are set in your GitHub repository settings:

1. **GEMINI_API_KEY** - Your Google Gemini API key
2. **SLACK_WEBHOOK_URL** - Production Slack webhook URL
3. **TEST_SLACK_WEBHOOK_URL** - Test Slack webhook URL

## How It Works

1. **Daily Run**: The LinkedIn monitor runs automatically at 8 AM IST (2:30 AM UTC) via GitHub Actions
2. **Manual Test**: Use the "Test LinkedIn Tracker" workflow in GitHub Actions for manual testing
3. **Data Flow**:
   - Fetches posts from ScrapIn API for each company in `linkedin_accounts.txt`
   - Analyzes posts with Gemini AI to extract business intelligence
   - Formats with proper emoji categories (💰 Fund Raise, 👥 Hiring, etc.)
   - Sends to Slack with hyperlinked company names

## Adding More Companies

```bash
# Add a new company
python3 add_linkedin_account.py https://www.linkedin.com/company/decagon/

# List all companies
python3 add_linkedin_account.py list
```

## Testing Locally

```bash
# Test with yesterday's data
python3 test_linkedin_manual.py

# Test with specific date
python3 test_linkedin_manual.py 2025-09-17

# Test formatting only
python3 test_linkedin_format.py
```

## Troubleshooting

1. **Old script still running**: Make sure all files are committed and pushed to GitHub
2. **API key errors**: Check that GitHub secrets are properly set
3. **No posts found**: ScrapIn API might have delays - posts may not be immediately available
4. **Formatting issues**: The new system ensures:
   - No ### headers (uses * for bold in Slack)
   - Company names always hyperlinked as <url|Company>
   - Consistent emoji categories

## Key Improvements Over Old System

1. **Direct implementation** - No database or external API dependencies
2. **Reliable formatting** - JSON output from Gemini ensures consistency
3. **Better error handling** - Continues even if some companies fail
4. **Proper hyperlinking** - All company names contain the post URL