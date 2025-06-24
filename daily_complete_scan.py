#!/usr/bin/env python3
"""
Daily complete intelligence scan - scans all accounts once and sends one complete summary
Starts at 5 AM IST, processes all accounts with rate limit delays, sends final compiled result
"""

import time
import sys
from datetime import datetime
from twitter_monitor import TwitterMonitor

def daily_complete_scan():
    """Scan all accounts once and send complete summary"""
    print(f"🌅 Starting daily complete scan - {datetime.now()}")
    
    monitor = TwitterMonitor()
    
    # Load all accounts
    all_accounts = []
    account_to_company = {}
    
    try:
        with open("accounts.txt", 'r') as f:
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
        print("❌ accounts.txt not found")
        return
    
    monitor.account_to_company = account_to_company
    
    print(f"📊 Daily scan: {len(all_accounts)} accounts to process")
    print(f"📋 Accounts: {[f'@{acc}' for acc in all_accounts]}")
    
    all_intelligence = []
    successful_accounts = 0
    
    # Process each account with delays to respect rate limits
    for i, username in enumerate(all_accounts):
        print(f"\n--- Processing @{username} ({i+1}/{len(all_accounts)}) ---")
        
        # Add delay between accounts (except first) to respect 15-min rate limits
        if i > 0:
            delay = 60 if len(all_accounts) > 10 else 30  # Longer delay for many accounts
            print(f"⏱️ Waiting {delay} seconds between accounts...")
            time.sleep(delay)
        
        try:
            # Fetch tweets for this account
            tweets = monitor.fetch_twitter_data(username)
            
            if not tweets:
                print(f"📭 No tweets found for @{username} in last 24 hours")
                continue
            
            print(f"📝 Found {len(tweets)} tweets from @{username}")
            
            # Analyze tweets for this account
            analysis = monitor.analyze_tweets_with_gemini(tweets)
            
            if analysis and analysis != "Nothing important today":
                print(f"🔍 Intelligence found: {analysis[:100]}...")
                all_intelligence.append(analysis)
                successful_accounts += 1
            else:
                print(f"📰 No significant intelligence from @{username}")
                
        except Exception as e:
            print(f"❌ Error processing @{username}: {e}")
    
    # Send final complete summary
    print(f"\n🏁 Daily scan completed!")
    print(f"✅ Intelligence found from: {successful_accounts}/{len(all_accounts)} accounts")
    
    if all_intelligence:
        # Combine all intelligence into one message
        combined_intelligence = "\n\n".join(all_intelligence)
        
        monitor.send_immediate_slack_notification(combined_intelligence)
        print("📤 Sent complete daily intelligence summary to Slack")
    else:
        # Send "not much happened" message
        monitor.send_immediate_slack_notification("Not much happened today")
        print("📤 Sent 'not much happened today' message to Slack")

if __name__ == "__main__":
    daily_complete_scan()