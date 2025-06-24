#!/usr/bin/env python3
"""
Test script to process only Decagon account locally
"""

from datetime import datetime
from twitter_monitor import TwitterMonitor

def test_decagon():
    """Test processing Decagon account only"""
    print(f"🧪 Testing Decagon account - {datetime.now()}")
    
    monitor = TwitterMonitor()
    
    # Set up company mapping for Decagon
    monitor.account_to_company = {"DecagonAI": "Decagon"}
    
    username = "DecagonAI"
    print(f"📊 Testing @{username}")
    
    try:
        # Fetch tweets for Decagon (now uses 24-hour window)
        tweets = monitor.fetch_twitter_data(username)
        
        if not tweets:
            print(f"📭 No tweets found for @{username} today")
            # Send test notification anyway
            monitor.send_immediate_slack_notification(
                "🧪 **Test Alert**: No tweets found for @DecagonAI today, but system is working!",
                "Local test run"
            )
            return
        
        print(f"📝 Found {len(tweets)} tweets from @{username}")
        for i, tweet in enumerate(tweets[:3]):  # Show first 3
            print(f"  Tweet {i+1}: {tweet.text[:100]}...")
        
        # Analyze tweets
        analysis = monitor.analyze_tweets_with_gemini(tweets)
        
        if analysis and analysis != "Nothing important today":
            print(f"🔍 Analysis: {analysis}")
            
            # Send notification
            monitor.send_immediate_slack_notification(
                analysis, 
                "🧪 Local test run: @DecagonAI"
            )
            print(f"✅ Sent Slack notification")
        else:
            print(f"📰 No significant news from @{username} today")
            # Send test notification
            monitor.send_immediate_slack_notification(
                "🧪 **Test Alert**: @DecagonAI processed successfully, but no significant news found today.",
                "Local test run"
            )
            print(f"✅ Sent 'no news' test notification")
            
    except Exception as e:
        print(f"❌ Error processing @{username}: {e}")
        # Send error notification
        monitor.send_immediate_slack_notification(
            f"🧪 **Test Alert**: Error processing @DecagonAI: {str(e)[:200]}",
            "Local test run - Error"
        )

if __name__ == "__main__":
    test_decagon()