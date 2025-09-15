#!/usr/bin/env python3
"""
Test Twitter API limits and bearer token status
"""

import json
import requests

def test_twitter_api():
    # Load config from environment or config file
    bearer_token = None
    
    # First try environment variable
    import os
    bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
    
    if not bearer_token:
        # Try config file
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            bearer_token = config.get('twitter_bearer_token')
        except FileNotFoundError:
            pass
    
    if not bearer_token:
        print("❌ No Twitter bearer token found in environment variables or config.json")
        print("   Set TWITTER_BEARER_TOKEN environment variable or create config.json")
        return

    # Test API access with rate limit headers
    print("🔍 Testing Twitter API access and rate limits...")
    
    headers = {"Authorization": f"Bearer {bearer_token}"}
    
    # Test 1: Check rate limit status
    print("\n1. Checking rate limit status:")
    url = "https://api.twitter.com/1.1/application/rate_limit_status.json"
    response = requests.get(url, headers=headers)
    
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        # Check user lookup limits
        user_lookup = data['resources']['users']['/users/by/username/:username']
        tweets_lookup = data['resources']['tweets']['/2/users/:id/tweets']
        
        print(f"   User Lookup: {user_lookup['remaining']}/{user_lookup['limit']} remaining")
        print(f"   User Tweets: {tweets_lookup['remaining']}/{tweets_lookup['limit']} remaining")
        print(f"   Reset time: {user_lookup['reset']}")
    else:
        print(f"   Error: {response.text}")
        return
    
    # Test 2: Try a simple user lookup
    print("\n2. Testing user lookup (DecagonAI):")
    url = "https://api.twitter.com/2/users/by/username/DecagonAI"
    response = requests.get(url, headers=headers)
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Rate Limit Remaining: {response.headers.get('x-rate-limit-remaining', 'N/A')}")
    print(f"   Rate Limit Reset: {response.headers.get('x-rate-limit-reset', 'N/A')}")
    
    if response.status_code == 429:
        print("   ⚠️  RATE LIMITED!")
    elif response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success: Found user ID {data['data']['id']}")
    else:
        print(f"   ❌ Error: {response.text}")

if __name__ == "__main__":
    test_twitter_api()