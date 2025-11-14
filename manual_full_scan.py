#!/usr/bin/env python3
"""
Manual full scan of all accounts - processes each account with real-time notifications
Respects Twitter API limits by processing 1 account per minute with immediate notifications
"""

import time
import sys
from datetime import datetime
from twitter_monitor import TwitterMonitor
from user_cache import UserIDCache

def manual_full_scan():
    """Process all accounts manually with real-time notifications"""
    print(f"🚀 Starting manual full scan - {datetime.now()}")
    
    monitor = TwitterMonitor()
    
    # Load all accounts (not just rotation subset)
    all_accounts = []
    account_to_company = {}
    
    try:
        with open("twitter_accounts.txt", 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if not line:
                    continue
                    
                if ':' in line:
                    account, company = line.split(':', 1)
                    all_accounts.append(account.strip())
                    account_to_company[account.strip()] = company.strip()
                else:
                    account = line.strip()
                    all_accounts.append(account)
                    account_to_company[account] = account
    except FileNotFoundError:
        print("❌ twitter_accounts.txt not found")
        return
    
    monitor.account_to_company = account_to_company
    
    print(f"📊 Manual scan: {len(all_accounts)} accounts")
    print(f"📋 Accounts: {[f'@{acc}' for acc in all_accounts]}")
    
    total_headlines = []
    successful_accounts = 0
    rate_limited_accounts = 0
    
    # Process each account with delays to respect rate limits
    for i, username in enumerate(all_accounts):
        print(f"\n--- Processing @{username} ({i+1}/{len(all_accounts)}) ---")
        
        # Add delay between accounts (except first)
        if i > 0:
            print("⏱️ Waiting 60 seconds between accounts to respect API limits...")
            time.sleep(60)
        
        try:
            # Fetch tweets for this account
            tweets = monitor.fetch_twitter_data(username)
            
            if not tweets:
                print(f"📭 No tweets found for @{username} today")
                continue
            
            print(f"📝 Found {len(tweets)} tweets from @{username}")
            
            # Analyze tweets for this account
            analysis = monitor.analyze_tweets_with_gemini(tweets)
            
            if analysis and analysis != "Nothing important today":
                print(f"🔍 Analysis: {analysis[:100]}...")
                
                # Send immediate notification for this account
                monitor.send_immediate_slack_notification(
                    analysis, 
                    f"Manual scan: @{username} ({i+1}/{len(all_accounts)})"
                )
                
                total_headlines.append(analysis)
                successful_accounts += 1
                print(f"✅ Sent immediate notification for @{username}")
            else:
                print(f"📰 No significant news from @{username} today")
                
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                print(f"⚠️ Rate limit hit for @{username} - continuing with other accounts")
                rate_limited_accounts += 1
            else:
                print(f"❌ Error processing @{username}: {e}")
    
    # Send final summary
    print(f"\n🏁 Manual scan completed!")
    print(f"✅ Successfully processed: {successful_accounts} accounts")
    print(f"⚠️ Rate limited: {rate_limited_accounts} accounts")
    
    if total_headlines:
        combined_summary = "\n".join(total_headlines)
        monitor.send_immediate_slack_notification(
            f"📋 **Manual Scan Summary**\n\n{combined_summary}",
            f"Complete manual scan: {successful_accounts}/{len(all_accounts)} accounts processed"
        )
        print("📤 Sent final summary notification")
    else:
        monitor.send_immediate_slack_notification(
            "📋 **Manual Scan Complete**\n\nNo significant competitive intelligence found today across all monitored accounts.",
            f"Manual scan: {len(all_accounts)} accounts checked"
        )
        print("📤 Sent 'no news' summary")

if __name__ == "__main__":
    manual_full_scan()
