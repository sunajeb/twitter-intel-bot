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

def split_content_into_blocks(content: str, date: str, max_chars: int = 2800) -> list:
    """
    Split long LinkedIn content into multiple Slack blocks to avoid 3000 char limit
    
    Args:
        content: The formatted LinkedIn news content
        date: The formatted date for headers
        max_chars: Maximum characters per block (default 2800 for safety buffer)
        
    Returns:
        List of Slack block objects
    """
    blocks = []
    
    # Add header block
    header_text = f"*Linkedin Update: {date}*"
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": header_text
        }
    })
    
    # Split content by lines and group into blocks
    lines = content.split('\n')
    current_block_text = ""
    
    for line in lines:
        # Check if adding this line would exceed the limit
        potential_text = current_block_text + '\n' + line if current_block_text else line
        
        if len(potential_text) > max_chars and current_block_text:
            # Add current block and start new one
            blocks.append({
                "type": "section", 
                "text": {
                    "type": "mrkdwn",
                    "text": current_block_text.strip()
                }
            })
            current_block_text = line
        else:
            current_block_text = potential_text
    
    # Add final block if there's remaining content
    if current_block_text.strip():
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn", 
                "text": current_block_text.strip()
            }
        })
    
    return blocks


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
    if not webhook_url and os.environ.get('TEST_MODE') != '1':
        print("❌ SLACK_WEBHOOK_URL not found in environment variables or config.json")
        return False
    elif os.environ.get('TEST_MODE') == '1':
        webhook_url = "test_webhook_url"  # Dummy URL for testing
    
    try:
        # Fetch and format competitor news
        print("🔄 Fetching competitor news from API...")
        formatted_news = get_and_format_competitor_news()
        
        # Check if we got a valid response (not an error message)
        if not formatted_news or "No competitor news available" in formatted_news or "Error parsing" in formatted_news or "Error fetching" in formatted_news:
            print("ℹ️ No competitor news available today or API error occurred")
            return True
        
        # Create Slack payload with simplified format to avoid blocks issues
        current_date = datetime.now().strftime('%Y-%m-%d')
        formatted_date = datetime.now().strftime('%d %b')  # 08 Sep format
        
        # Use blocks format with smart splitting to handle long content
        blocks = split_content_into_blocks(formatted_news, formatted_date)
        
        payload = {
            "text": f"Linkedin Update: {formatted_date}",
            "blocks": blocks
        }
        
        # Send to Slack (skip if testing)
        if os.environ.get('TEST_MODE') == '1':
            print("🧪 TEST MODE: Would send to Slack:")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            return True
        
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

