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
        self.base_url = "https://api.twitterapi.io"
        self.headers = {
            'X-API-Key': api_key,
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
            print(f"🕐 Fetching tweets from @{username} [Last {hours_back} hours]")
            
            # TwitterAPI.io endpoint for user tweets
            url = f"{self.base_url}/twitter/user/last_tweets"
            params = {
                'userName': username,
                'count': min(max_results, 20)  # TwitterAPI.io returns up to 20 tweets per page
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
            
            if data.get('status') != 'success':
                print(f"❌ API returned error for @{username}: {data.get('message', 'Unknown error')}")
                return []
            
            tweets_data = data.get('data', {}).get('tweets', [])
            
            if not tweets_data:
                print(f"ℹ️ No tweets found for @{username}")
                return []
            
            # Filter tweets by time (TwitterAPI.io doesn't have time filtering in API)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            tweets = []
            for tweet_data in tweets_data:
                # Parse created_at time
                try:
                    tweet_time_str = tweet_data.get('createdAt', '')
                    # TwitterAPI.io uses ISO format, try parsing it
                    tweet_time = datetime.fromisoformat(tweet_time_str.replace('Z', '+00:00'))
                    
                    # Skip tweets older than our cutoff
                    if tweet_time < cutoff_time:
                        continue
                        
                except (ValueError, TypeError):
                    # If we can't parse the time, include the tweet
                    pass
                
                # Check if this is a reply
                is_reply = tweet_data.get('isReply', False)
                reply_to_tweet_id = tweet_data.get('inReplyToId')
                
                # Format tweet data to match existing Tweet class structure
                tweet = {
                    'id': tweet_data.get('id', ''),
                    'text': tweet_data.get('text', ''),
                    'created_at': tweet_data.get('createdAt', ''),
                    'username': username,
                    'url': tweet_data.get('url', f"https://twitter.com/{username}/status/{tweet_data.get('id', '')}"),
                    'is_reply': is_reply,
                    'reply_to_tweet_id': reply_to_tweet_id,
                    'metrics': {
                        'retweet_count': tweet_data.get('retweetCount', 0),
                        'like_count': tweet_data.get('likeCount', 0),
                        'reply_count': tweet_data.get('replyCount', 0),
                        'quote_count': tweet_data.get('quoteCount', 0)
                    }
                }
                tweets.append(tweet)
            
            print(f"✅ Fetched {len(tweets)} tweets for @{username} (last {hours_back}h)")
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
            
            # Add delay between requests (TwitterAPI.io free tier: 1 request per 5 seconds)
            if i < len(usernames) - 1:  # Don't wait after the last request
                print("⏳ Waiting 6 seconds before next request (free tier limit)...")
                time.sleep(6)
        
        return all_tweets
    
    def test_connection(self) -> bool:
        """Test if the API key and connection are working"""
        try:
            # Test with a simple request to get tweets by IDs (using known tweet IDs)
            url = f"{self.base_url}/twitter/tweets"
            params = {
                'tweet_ids': '1846987139428634858'  # Use a known tweet ID for testing
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    print("✅ TwitterAPI.io connection successful!")
                    return True
                else:
                    print(f"❌ API error: {data.get('message', 'Unknown error')}")
                    return False
            elif response.status_code == 401:
                print("❌ Authentication failed - check your API key")
                return False
            else:
                print(f"⚠️ Connection test returned: {response.status_code} - {response.text}")
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