#!/usr/bin/env python3
"""
Twitter tracking using twitterapi.io as alternative to official API
No authentication required, much higher rate limits
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict

class TwitterAlternativeScraper:
    def __init__(self):
        self.base_url = "https://api.twitterapi.io/api/v1"
        # No API key required for basic usage
        
    def get_user_tweets(self, username: str, days_back: int = 1, max_results: int = 10) -> List[Dict]:
        """
        Fetch recent tweets for a username
        
        Args:
            username: Twitter username without @
            days_back: How many days back to fetch
            max_results: Maximum number of tweets to return
            
        Returns:
            List of tweet dictionaries
        """
        # Calculate date filter
        since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # twitterapi.io endpoint for user tweets
        url = f"{self.base_url}/tweets"
        params = {
            'username': username,
            'count': max_results,
            'since': since_date,
            'exclude': 'replies,retweets'  # Focus on original tweets
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                tweets = []
                
                for tweet_data in data.get('data', []):
                    tweet = {
                        'id': tweet_data.get('id'),
                        'text': tweet_data.get('text'),
                        'created_at': tweet_data.get('created_at'),
                        'username': username,
                        'url': f"https://twitter.com/{username}/status/{tweet_data.get('id')}",
                        'metrics': {
                            'retweets': tweet_data.get('public_metrics', {}).get('retweet_count', 0),
                            'likes': tweet_data.get('public_metrics', {}).get('like_count', 0),
                            'replies': tweet_data.get('public_metrics', {}).get('reply_count', 0)
                        }
                    }
                    tweets.append(tweet)
                
                print(f"✅ Fetched {len(tweets)} tweets for @{username}")
                return tweets
                
            else:
                print(f"❌ Error fetching tweets for @{username}: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Exception fetching tweets for @{username}: {e}")
            return []
    
    def get_multiple_users_tweets(self, usernames: List[str], days_back: int = 1) -> Dict[str, List[Dict]]:
        """
        Fetch tweets for multiple users
        
        Args:
            usernames: List of Twitter usernames
            days_back: How many days back to fetch
            
        Returns:
            Dictionary with username as key and tweets as value
        """
        all_tweets = {}
        
        for username in usernames:
            print(f"🔍 Fetching tweets for @{username}...")
            tweets = self.get_user_tweets(username, days_back)
            all_tweets[username] = tweets
            
            # Small delay to be respectful
            import time
            time.sleep(1)
        
        return all_tweets

def test_twitter_alternative():
    """Test the alternative Twitter scraper"""
    scraper = TwitterAlternativeScraper()
    
    # Test with a few accounts from your list
    test_accounts = ['DecagonAI', 'SierraPlatform']
    
    print("🧪 Testing alternative Twitter scraper...")
    results = scraper.get_multiple_users_tweets(test_accounts, days_back=3)
    
    for username, tweets in results.items():
        print(f"\n📊 @{username}: {len(tweets)} tweets")
        for tweet in tweets[:2]:  # Show first 2 tweets
            print(f"   - {tweet['text'][:100]}...")

if __name__ == "__main__":
    test_twitter_alternative()