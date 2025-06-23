#!/bin/bash

echo "🚀 Setting up Twitter Intelligence Bot"
echo "======================================"

# Step 1: Initialize Git and push to GitHub
echo "📁 Initializing Git repository..."
git init
git add .
git commit -m "Initial Twitter intelligence bot setup

- Daily monitoring via GitHub Actions
- Slack slash command integration  
- Vercel serverless deployment
- Competitive intelligence analysis with Gemini AI"

echo "🔗 Creating GitHub repository..."
gh repo create twitter-intel-bot --public --description "AI-powered competitive intelligence bot for Twitter monitoring"

echo "📤 Pushing to GitHub..."
git push -u origin main

# Step 2: Set GitHub Secrets
echo "🔐 Setting up GitHub secrets..."
echo "Please enter your API keys when prompted:"

read -p "Enter Twitter Bearer Token: " TWITTER_TOKEN
read -p "Enter Gemini API Key: " GEMINI_KEY  
read -p "Enter Slack Webhook URL: " SLACK_WEBHOOK
read -p "Enter Twitter accounts to monitor (comma-separated): " ACCOUNTS

gh secret set TWITTER_BEARER_TOKEN --body "$TWITTER_TOKEN"
gh secret set GEMINI_API_KEY --body "$GEMINI_KEY"
gh secret set SLACK_WEBHOOK_URL --body "$SLACK_WEBHOOK"
gh secret set TWITTER_ACCOUNTS --body "$ACCOUNTS"

echo "✅ GitHub secrets configured"

# Step 3: Deploy to Vercel
echo "🌐 Deploying to Vercel..."
vercel --prod

echo "✅ Deployment complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Go to your Vercel dashboard to get the deployment URL"
echo "2. Configure Slack slash command with: https://your-project.vercel.app/api/intel"
echo "3. Test with /intel in Slack"
echo "4. Monitor daily runs in GitHub Actions"
echo ""
echo "🎉 Your Twitter intelligence bot is ready!"