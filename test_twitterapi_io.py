#!/usr/bin/env python3
"""
Test TwitterAPI.io integration with the twitter monitor
"""

import json
from twitter_monitor import TwitterMonitor

def test_integration():
    """Test TwitterAPI.io integration with existing monitor"""
    print("🧪 Testing TwitterAPI.io integration...")
    
    # Check if config.json exists
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found. Please create it with your TwitterAPI.io key:")
        print("   {")
        print('     "twitterapi_io_key": "YOUR_API_KEY_HERE",')
        print('     "gemini_api_key": "YOUR_GEMINI_KEY_HERE",')
        print('     "slack_webhook_url": "YOUR_SLACK_WEBHOOK_HERE"')
        print("   }")
        return
    
    if not config.get('twitterapi_io_key'):
        print("❌ twitterapi_io_key not found in config.json")
        print("   Please add your TwitterAPI.io API key to config.json")
        return
    
    # Test with monitor
    monitor = TwitterMonitor()
    
    # Test fetching data for one account
    test_account = 'DecagonAI'
    print(f"🔍 Testing data fetch for @{test_account}...")
    
    tweets = monitor.fetch_twitter_data(test_account)
    
    if tweets:
        print(f"✅ Successfully fetched {len(tweets)} tweets:")
        for i, tweet in enumerate(tweets[:3], 1):
            print(f"   {i}. {tweet.text[:80]}...")
            print(f"      Created: {tweet.created_at}")
            print(f"      URL: {tweet.url}")
            print()
    else:
        print("ℹ️ No tweets found or API error")

if __name__ == "__main__":
    test_integration()