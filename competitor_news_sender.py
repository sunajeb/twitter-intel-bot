#!/usr/bin/env python3
"""
Competitor News Sender
Fetches competitor news from API and sends formatted message to Slack
Integrates with existing Twitter Intel Bot Slack channel
"""

import os
import json
import requests
from datetime import datetime
from competitor_api_formatter import get_and_format_competitor_news


def get_slack_webhook_url():
    """
    Get Slack webhook URL from environment or config file
    """
    # First try environment variable (for GitHub Actions)
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if webhook_url:
        return webhook_url
    
    # Fallback to config file (for local testing)
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config.get('slack_webhook_url')
    except FileNotFoundError:
        return None


def send_competitor_news_to_slack():
    """
    Fetch competitor news and send to Slack using existing webhook
    """
    # Get Slack webhook URL from environment or config
    webhook_url = get_slack_webhook_url()
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL not found in environment variables or config.json")
        return False
    
    try:
        # Fetch and format competitor news
        print("🔄 Fetching competitor news from API...")
        formatted_news = get_and_format_competitor_news()
        
        if not formatted_news or "No competitor news available" in formatted_news:
            print("ℹ️ No competitor news available today")
            return True
        
        # Create Slack payload with same format as Twitter monitor
        current_date = datetime.now().strftime('%Y-%m-%d')
        payload = {
            "text": f"📊 Competitor Intelligence Update - {current_date}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📊 Today's Competitor Intelligence*\n\n{formatted_news}"
                    }
                }
            ]
        }
        
        # Send to Slack
        print("📤 Sending competitor news to Slack...")
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 200:
            print("✅ Competitor news sent to Slack successfully!")
            return True
        else:
            print(f"❌ Failed to send to Slack: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending competitor news: {e}")
        return False


def send_test_competitor_news():
    """
    Send a test competitor news message to verify integration
    """
    webhook_url = get_slack_webhook_url()
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL not found in environment variables or config.json")
        return False
    
    # Test message
    test_message = """*📊 Test - Competitor Intelligence Update*

*💰 Fund Raise*
• *Test Company*: Raised $100M Series B funding round <https://example.com|🔗>

*🚀 Product*
• *Test AI*: Launched new voice AI platform <https://example.com|🔗>

_This is a test message to verify competitor news integration._"""
    
    payload = {
        "text": f"🧪 Test - Competitor Intelligence - {datetime.now().strftime('%Y-%m-%d')}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": test_message
                }
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("✅ Test competitor news sent successfully!")
            return True
        else:
            print(f"❌ Test failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🧪 Running test competitor news...")
        success = send_test_competitor_news()
    else:
        print("📊 Running daily competitor news...")
        success = send_competitor_news_to_slack()
    
    if success:
        print("🎉 Competitor news process completed successfully!")
        exit(0)
    else:
        print("💥 Competitor news process failed!")
        exit(1)

