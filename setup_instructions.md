# Twitter Intelligence Monitor - Complete Setup Guide

## 1. Daily 8 AM Execution

### Option A: Cron Job (Recommended)
```bash
# Open crontab editor
crontab -e

# Add this line for 8 AM daily execution:
0 8 * * * /Users/sunaje/Downloads/run_daily.sh

# Save and exit
```

### Option B: macOS LaunchAgent (Alternative)
```bash
# Create LaunchAgent directory if it doesn't exist
mkdir -p ~/Library/LaunchAgents

# Create plist file
cat > ~/Library/LaunchAgents/com.twittermonitor.daily.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.twittermonitor.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/sunaje/Downloads/run_daily.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/sunaje/Downloads/monitor.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/sunaje/Downloads/monitor.log</string>
</dict>
</plist>
EOF

# Load the LaunchAgent
launchctl load ~/Library/LaunchAgents/com.twittermonitor.daily.plist
```

## 2. Slack Slash Command Setup

### Step 1: Create Slack App
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "Intel Bot", select your workspace

### Step 2: Create Slash Command
1. In your app settings, go to "Slash Commands"
2. Click "Create New Command"
3. Command: `/intel`
4. Request URL: `YOUR_NGROK_URL/intel` (see Step 3)
5. Short Description: "Get latest competitive intelligence"
6. Usage Hint: (leave empty)

### Step 3: Set up Public URL (for development)
```bash
# Install ngrok if you don't have it
brew install ngrok

# In one terminal, start the Slack bot
cd /Users/sunaje/Downloads
source twitter_monitor_env/bin/activate
pip install flask==2.3.3
python3 slack_bot.py

# In another terminal, expose it publicly
ngrok http 3000

# Copy the https URL (e.g., https://abc123.ngrok.io) and use it in Step 2
```

### Step 4: Install App to Workspace
1. Go to "Install App" in your Slack app settings
2. Click "Install to Workspace"
3. Authorize the app

### Step 5: Get Verification Token (Optional Security)
1. In "Basic Information", copy "Verification Token"
2. Set environment variable:
```bash
export SLACK_VERIFICATION_TOKEN="your_token_here"
```

## 3. Adding More Twitter Accounts

Simply edit the `twitter_accounts.txt` file:
```bash
nano twitter_accounts.txt

# Add one account per line (without @):
DecagonAI
SierraPlatform
OpenAI
AnthropicAI
PerplexityAI
```

The system will automatically scan all accounts in this file.

## 4. Usage

### Daily Automatic Updates
- Runs every day at 8 AM automatically
- Only sends notifications when important intelligence is found
- Logs stored in `monitor.log`

### On-Demand Updates
- Type `/intel` in any Slack channel
- Gets instant analysis of latest tweets from all monitored accounts

## 5. Monitoring & Troubleshooting

### Check if cron job is running:
```bash
# View cron log (on macOS)
tail -f /var/log/system.log | grep cron

# Check monitor log
tail -f /Users/sunaje/Downloads/monitor.log
```

### Test manually:
```bash
cd /Users/sunaje/Downloads
source twitter_monitor_env/bin/activate
python3 twitter_monitor.py
```

## 6. File Structure
```
/Users/sunaje/Downloads/
├── twitter_monitor.py      # Main monitoring script
├── slack_bot.py           # Slack slash command handler
├── config.json            # API keys and settings
├── twitter_accounts.txt   # Twitter accounts to monitor
├── requirements.txt       # Python dependencies
├── run_daily.sh          # Daily execution script
├── twitter_monitor_env/  # Python virtual environment
└── monitor.log           # Execution logs
```
