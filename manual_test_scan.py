#!/usr/bin/env python3
"""
Manual test scan - scans only the first account in twitter_accounts.txt for testing
Sends immediate response to Slack
"""

from datetime import datetime
from twitter_monitor import TwitterMonitor

def manual_test_scan():
    """Test scan of first account only"""
    print(f"🧪 Manual test scan - {datetime.now()}")
    
    monitor = TwitterMonitor()
    
    # Load only the first account
    try:
        with open("twitter_accounts.txt", 'r') as f:
            first_line = f.readline().strip()
            if not first_line:
                print("❌ No accounts found in twitter_accounts.txt")
                return
                
            if ':' in first_line:
                account, company = first_line.split(':', 1)
                username = account.strip()
                company_name = company.strip()
            else:
                username = first_line.strip()
                company_name = username
                
    except FileNotFoundError:
        print("❌ twitter_accounts.txt not found")
        return
    
    monitor.account_to_company = {username: company_name}
    
    print(f"🎯 Testing first account: @{username} ({company_name})")
    
    try:
        # Fetch tweets for this account
        tweets = monitor.fetch_twitter_data(username)
        
        if not tweets:
            print(f"📭 No tweets found for @{username} in last 24 hours")
            monitor.send_immediate_slack_notification(
                f"Test scan: No tweets found for @{username} in last 24 hours"
            )
            return
        
        print(f"📝 Found {len(tweets)} tweets from @{username}")
        
        # Analyze tweets
        analysis = monitor.analyze_tweets_with_gemini(tweets)
        
        if analysis and analysis != "Nothing important today":
            print(f"🔍 Analysis: {analysis}")
            monitor.send_immediate_slack_notification(analysis)
            print(f"✅ Sent test results to Slack")
        else:
            print(f"📰 No significant intelligence from @{username}")
            monitor.send_immediate_slack_notification(
                f"Test scan: No significant intelligence found for @{username} today"
            )
            print(f"✅ Sent 'no intelligence' message to Slack")
            
    except Exception as e:
        print(f"❌ Error in test scan: {e}")
        monitor.send_immediate_slack_notification(
            f"Test scan error: {str(e)[:200]}"
        )

if __name__ == "__main__":
    manual_test_scan()
