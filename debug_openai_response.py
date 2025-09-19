#!/usr/bin/env python3
"""
Debug the actual API response for OpenAI to see what's being returned
"""

import requests
import json
import os

def debug_openai_response():
    """Debug the raw API response for OpenAI"""
    api_key = os.getenv('TWITTERAPI_IO_KEY')
    if not api_key:
        raise ValueError("TWITTERAPI_IO_KEY environment variable not set")
    base_url = "https://api.twitterapi.io"
    
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    print("🔍 Debugging OpenAI API response...")
    
    # Test with OpenAI
    url = f"{base_url}/twitter/user/last_tweets"
    params = {
        'userName': 'OpenAI',
        'count': 10
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Full Response Text:")
    print(response.text)
    print()
    
    if response.status_code == 200:
        try:
            data = response.json()
            print("Parsed JSON:")
            print(json.dumps(data, indent=2))
            
            if 'tweets' in data:
                tweets = data['tweets']
                print(f"\nFound {len(tweets)} tweets in response")
                if tweets:
                    print("First tweet details:")
                    first_tweet = tweets[0]
                    for key, value in first_tweet.items():
                        print(f"  {key}: {value}")
        except Exception as e:
            print(f"Error parsing JSON: {e}")

if __name__ == "__main__":
    debug_openai_response()