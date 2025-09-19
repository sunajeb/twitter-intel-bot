#!/usr/bin/env python3
"""
Debug what's happening with yellowdotai specifically
"""

import os
import requests
import json
from datetime import datetime, timezone, timedelta

def debug_yellowdotai():
    """Debug yellowdotai API response and time filtering"""
    api_key = os.getenv('TWITTERAPI_IO_KEY')
    if not api_key:
        raise ValueError("TWITTERAPI_IO_KEY environment variable not set")
    base_url = "https://api.twitterapi.io"
    
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    print("🔍 Debugging yellowdotai tweets...")
    
    # Get raw response
    url = f"{base_url}/twitter/user/last_tweets"
    params = {
        'userName': 'yellowdotai',
        'count': 20
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    data = response.json()
    tweets_data = data.get('data', {}).get('tweets', [])
    
    print(f"Found {len(tweets_data)} total tweets from API")
    
    # Check time filtering
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    print(f"Cutoff time (24h ago): {cutoff_time}")
    print(f"Current time: {datetime.now(timezone.utc)}")
    
    recent_tweets = 0
    for i, tweet_data in enumerate(tweets_data):
        created_at = tweet_data.get('createdAt', '')
        tweet_text = tweet_data.get('text', '')
        
        try:
            # TwitterAPI.io uses Twitter's format: "Wed Sep 10 08:40:21 +0000 2025"
            tweet_time = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
            is_recent = tweet_time >= cutoff_time
            recent_tweets += 1 if is_recent else 0
            
            print(f"{i+1:2d}. {'✅' if is_recent else '❌'} {created_at} - {tweet_text[:60]}...")
            
        except Exception as e:
            print(f"{i+1:2d}. ⚠️  Could not parse time: {created_at} - {tweet_text[:60]}...")
    
    print(f"\n📊 Summary:")
    print(f"Total tweets from API: {len(tweets_data)}")
    print(f"Tweets in last 24h: {recent_tweets}")

if __name__ == "__main__":
    debug_yellowdotai()