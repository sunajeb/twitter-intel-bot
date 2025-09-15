#!/usr/bin/env python3
"""
Test TwitterAPI.io API key provided by user
"""

from twitter_api_io_client import TwitterAPIClient

def test_provided_api_key():
    """Test the provided API key"""
    api_key = "new1_3888e5e515a14b58860d269717014769"
    
    print("🧪 Testing provided TwitterAPI.io API key...")
    print(f"API Key: {api_key}")
    
    client = TwitterAPIClient(api_key)
    
    # Test connection first
    print("\n1. Testing connection...")
    if not client.test_connection():
        print("❌ Connection test failed")
        return False
    
    # Test with a simple account
    print("\n2. Testing data fetch...")
    test_accounts = ['yellowdotai', 'DecagonAI']
    
    for account in test_accounts:
        print(f"\n🔍 Testing @{account}...")
        tweets = client.get_user_tweets(account, hours_back=24, max_results=5)
        
        if tweets:
            print(f"✅ Success! Found {len(tweets)} tweets:")
            for i, tweet in enumerate(tweets[:2], 1):
                print(f"   {i}. {tweet['text'][:80]}...")
                print(f"      Created: {tweet['created_at']}")
        else:
            print(f"ℹ️ No tweets found for @{account}")
    
    return True

if __name__ == "__main__":
    test_provided_api_key()