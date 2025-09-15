#!/usr/bin/env python3
"""
Test TwitterAPI.io with a single account to verify it works
"""

from twitter_api_io_client import TwitterAPIClient

def test_single_account():
    """Test with just one account to avoid rate limits"""
    api_key = "new1_3888e5e515a14b58860d269717014769"
    
    print("🧪 Testing TwitterAPI.io with single account...")
    
    client = TwitterAPIClient(api_key)
    
    # Test with just DecagonAI
    print("🔍 Testing @DecagonAI...")
    tweets = client.get_user_tweets('DecagonAI', hours_back=24, max_results=5)
    
    if tweets:
        print(f"✅ Success! Found {len(tweets)} tweets:")
        for i, tweet in enumerate(tweets, 1):
            print(f"   {i}. {tweet['text'][:80]}...")
            print(f"      Created: {tweet['created_at']}")
            print(f"      URL: {tweet['url']}")
            print()
    else:
        print("ℹ️ No tweets found")

if __name__ == "__main__":
    test_single_account()