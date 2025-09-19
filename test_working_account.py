#!/usr/bin/env python3
"""
Test with an account that tweets frequently to verify filtering works
"""

import os
from twitter_api_io_client import TwitterAPIClient

def test_working_account():
    """Test with OpenAI which tweets frequently"""
    api_key = os.getenv('TWITTERAPI_IO_KEY')
    if not api_key:
        raise ValueError("TWITTERAPI_IO_KEY environment variable not set")
    
    print("🧪 Testing with @OpenAI (active account)...")
    
    client = TwitterAPIClient(api_key)
    
    # Test with OpenAI
    print("🔍 Testing @OpenAI last 24h...")
    tweets_24h = client.get_user_tweets('OpenAI', hours_back=24, max_results=10)
    
    print("🔍 Testing @OpenAI last 7 days...")
    tweets_7d = client.get_user_tweets('OpenAI', hours_back=168, max_results=10)  # 7 days
    
    print(f"📊 Results:")
    print(f"Last 24 hours: {len(tweets_24h)} tweets")
    print(f"Last 7 days: {len(tweets_7d)} tweets")
    
    if tweets_24h:
        print("\n📝 Recent tweets (24h):")
        for i, tweet in enumerate(tweets_24h[:3], 1):
            print(f"   {i}. {tweet['text'][:80]}...")
            print(f"      Created: {tweet['created_at']}")

if __name__ == "__main__":
    test_working_account()