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

#### Note
This project currently uses GitHub Actions only (daily and test trackers). Serverless handlers and Vercel deployment are not required.

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
- `requirements.txt` - Dependencies

## Serverless
Not used in the current setup. You can add serverless endpoints later if needed.

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
