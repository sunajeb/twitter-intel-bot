#!/usr/bin/env python3
"""
Test TwitterAPI.io with @OpenAI to see actual tweet output
"""

from twitter_api_io_client import TwitterAPIClient

def test_openai_account():
    """Test with OpenAI account which tweets frequently"""
    api_key = "new1_3888e5e515a14b58860d269717014769"
    
    print("🧪 Testing TwitterAPI.io with @OpenAI (active account)...")
    
    client = TwitterAPIClient(api_key)
    
    # Test with OpenAI which tweets regularly
    print("🔍 Testing @OpenAI...")
    tweets = client.get_user_tweets('OpenAI', hours_back=72, max_results=10)  # 3 days to increase chances
    
    if tweets:
        print(f"✅ Success! Found {len(tweets)} tweets:")
        for i, tweet in enumerate(tweets, 1):
            print(f"   {i}. {tweet['text'][:120]}...")
            print(f"      Created: {tweet['created_at']}")
            print(f"      URL: {tweet['url']}")
            print(f"      Likes: {tweet['metrics']['like_count']}, Retweets: {tweet['metrics']['retweet_count']}")
            print()
    else:
        print("ℹ️ No tweets found")
    
    return tweets

if __name__ == "__main__":
    test_openai_account()