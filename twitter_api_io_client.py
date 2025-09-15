#!/usr/bin/env python3
"""
TwitterAPI.io client for fetching Twitter data
Replaces official Twitter API to avoid rate limits
"""

import requests
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import time

class TwitterAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twitterapi.io/v2"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_user_tweets(self, username: str, hours_back: int = 24, max_results: int = 10) -> List[Dict]:
        """
        Fetch recent tweets for a username from last N hours
        
        Args:
            username: Twitter username without @
            hours_back: How many hours back to fetch (default 24)
            max_results: Maximum number of tweets to return
            
        Returns:
            List of tweet dictionaries compatible with existing Tweet class
        """
        try:
            # Calculate time filter
            utc_now = datetime.now(timezone.utc)
            start_time = (utc_now - timedelta(hours=hours_back)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            print(f"🕐 Fetching tweets from @{username} since: {start_time} (UTC) [Last {hours_back} hours]")
            
            # TwitterAPI.io endpoint for user tweets
            url = f"{self.base_url}/users/by/username/{username}/tweets"
            params = {
                'max_results': min(max_results, 100),  # API limit is usually 100
                'start_time': start_time,
                'exclude': 'retweets',
                'tweet.fields': 'created_at,public_metrics,in_reply_to_user_id,referenced_tweets'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 429:
                print(f"⚠️ Rate limit hit for @{username} - skipping for now")
                return []
            elif response.status_code == 401:
                print(f"❌ Authentication failed - check your TwitterAPI.io API key")
                return []
            elif response.status_code != 200:
                print(f"❌ Error fetching tweets for @{username}: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            tweets_data = data.get('data', [])
            
            if not tweets_data:
                print(f"ℹ️ No tweets found for @{username} in the last {hours_back} hours")
                return []
            
            tweets = []
            for tweet_data in tweets_data:
                # Check if this is a reply
                is_reply = tweet_data.get('in_reply_to_user_id') is not None
                reply_to_tweet_id = None
                
                # Get the original tweet ID if this is a reply
                if 'referenced_tweets' in tweet_data:
                    for ref in tweet_data['referenced_tweets']:
                        if ref['type'] == 'replied_to':
                            reply_to_tweet_id = ref['id']
                            break
                
                # Format tweet data to match existing Tweet class structure
                tweet = {
                    'id': tweet_data['id'],
                    'text': tweet_data['text'],
                    'created_at': tweet_data['created_at'],
                    'username': username,
                    'url': f"https://twitter.com/{username}/status/{tweet_data['id']}",
                    'is_reply': is_reply,
                    'reply_to_tweet_id': reply_to_tweet_id,
                    'metrics': tweet_data.get('public_metrics', {})
                }
                tweets.append(tweet)
            
            print(f"✅ Fetched {len(tweets)} tweets for @{username}")
            return tweets
            
        except Exception as e:
            print(f"❌ Exception fetching tweets for @{username}: {str(e)}")
            return []
    
    def get_multiple_users_tweets(self, usernames: List[str], hours_back: int = 24) -> Dict[str, List[Dict]]:
        """
        Fetch tweets for multiple users with rate limit management
        
        Args:
            usernames: List of Twitter usernames
            hours_back: How many hours back to fetch
            
        Returns:
            Dictionary with username as key and tweets as value
        """
        all_tweets = {}
        
        for i, username in enumerate(usernames):
            print(f"🔍 Processing {i+1}/{len(usernames)}: @{username}")
            
            tweets = self.get_user_tweets(username, hours_back)
            all_tweets[username] = tweets
            
            # Add delay between requests to be respectful to the API
            if i < len(usernames) - 1:  # Don't wait after the last request
                print("⏳ Waiting 2 seconds before next request...")
                time.sleep(2)
        
        return all_tweets
    
    def test_connection(self) -> bool:
        """Test if the API key and connection are working"""
        try:
            # Test with a simple request
            url = f"{self.base_url}/users/by/username/twitter"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                print("✅ TwitterAPI.io connection successful!")
                return True
            elif response.status_code == 401:
                print("❌ Authentication failed - check your API key")
                return False
            else:
                print(f"⚠️ Connection test returned: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Connection test failed: {str(e)}")
            return False


if __name__ == "__main__":
    # Test the TwitterAPI.io client
    print("🧪 Testing TwitterAPI.io client...")
    
    # You'll need to set your API key
    api_key = input("Enter your TwitterAPI.io API key: ").strip()
    if not api_key:
        print("❌ No API key provided")
        exit(1)
    
    client = TwitterAPIClient(api_key)
    
    # Test connection
    if not client.test_connection():
        print("❌ Connection test failed")
        exit(1)
    
    # Test with a few accounts
    test_accounts = ['DecagonAI', 'SierraPlatform']
    results = client.get_multiple_users_tweets(test_accounts, hours_back=24)
    
    print(f"\n📊 Results:")
    for username, tweets in results.items():
        print(f"@{username}: {len(tweets)} tweets")
        for tweet in tweets[:2]:  # Show first 2 tweets
            print(f"   - {tweet['text'][:100]}...")