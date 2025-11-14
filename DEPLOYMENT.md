# GitHub Actions + Serverless Deployment Guide

## Quick Setup Steps

### 1. Push to GitHub Repository
```bash
git init
git add .
git commit -m "Initial Twitter monitoring setup"
git remote add origin https://github.com/YOUR_USERNAME/twitter-intel-bot.git
git push -u origin main
```

### 2. Configure GitHub Secrets
Go to your repository → Settings → Secrets and variables → Actions

Add these secrets:
- `GEMINI_API_KEY`: Your Google Gemini API key  
- `SLACK_WEBHOOK_URL`: Your Slack webhook URL

### 3. Deploy Webhook Handler

#### Option A: Railway (Easiest)
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Deploy automatically
4. Your URL will be: `https://your-app-name.railway.app/intel`

#### Option B: Vercel
1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Add a `vercel.json` file (see below)
4. Your URL will be: `https://your-project.vercel.app/api/intel`
5. Ensure `twitter_accounts.txt` and `linkedin_accounts.txt` are present in the repo root; handlers read from these master files.

#### Option C: AWS Lambda
1. Create Lambda function from the GitHub Actions workflow
2. Set up API Gateway trigger
3. Your URL will be: `https://api-id.execute-api.region.amazonaws.com/prod/intel`

### 4. Configure Slack Slash Command

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create new app → "From scratch"
3. Go to "Slash Commands" → "Create New Command"
4. Set:
   - Command: `/intel`
   - Request URL: Your deployed webhook URL (from step 3)
   - Short Description: "Get competitive intelligence"
5. Install app to your workspace

## Files Created

- `.github/workflows/daily-monitor.yml` - Daily automation
- `.github/workflows/deploy-webhook.yml` - Webhook deployment  
- `slack_webhook_handler.py` - Handles `/intel` commands
- `requirements.txt` - Updated dependencies

## Vercel Configuration (if using Vercel)

Create `vercel.json`:
```json
{
  "functions": {
    "slack_webhook_handler.py": {
      "runtime": "python3.9"
    }
  },
  "routes": [
    {
      "src": "/api/intel",
      "dest": "/slack_webhook_handler.py"
    }
  ]
}
```

## Testing

### Test Daily Monitor
- Go to Actions tab in GitHub
- Run "Daily Twitter Intelligence Monitor" manually
- Check run logs

### Test Slash Command  
- Type `/intel` in any Slack channel
- Should receive latest competitive intelligence

## Monitoring

- Daily runs appear in GitHub Actions
- Logs stored as artifacts (7-day retention)
- Slack notifications only sent when important intelligence found
