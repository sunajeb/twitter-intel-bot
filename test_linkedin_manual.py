#!/usr/bin/env python3
"""
Manual test script for LinkedIn monitoring
Run this to test the LinkedIn monitor with specific dates
"""

import sys
from datetime import datetime, timedelta
from linkedin_monitor import LinkedInMonitor

def test_specific_date(date_str=None):
    """Test LinkedIn monitoring for a specific date"""
    monitor = LinkedInMonitor()
    
    if date_str:
        # Use provided date
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        # Use yesterday by default
        target_date = datetime.now() - timedelta(days=1)
    
    date_formatted = target_date.strftime('%Y-%m-%d')
    print(f"Testing LinkedIn monitor for date: {date_formatted}")
    print("=" * 60)
    
    # Load accounts
    accounts = monitor.load_accounts()
    print(f"Monitoring {len(accounts)} LinkedIn accounts:")
    for acc in accounts:
        print(f"  - {acc}")
    
    print("\nFetching posts...")
    
    # Fetch posts
    all_posts = []
    for account_url in accounts:
        print(f"\nFetching from {account_url}...")
        posts = monitor.get_linkedin_posts(account_url, date_formatted, date_formatted)
        print(f"  Found {len(posts)} posts")
        all_posts.extend(posts)
    
    print(f"\nTotal posts fetched: {len(all_posts)}")
    
    if all_posts:
        # Show sample posts
        print("\nSample posts:")
        for i, post in enumerate(all_posts[:3]):
            print(f"\nPost {i+1}:")
            print(f"  Company: {post.get('company_name', 'Unknown')}")
            print(f"  Text: {post['text'][:100]}...")
            print(f"  URL: {post['url']}")
    
    # Analyze with Gemini
    print("\nAnalyzing with Gemini...")
    analysis = monitor.analyze_posts_with_gemini(all_posts, date_formatted)
    
    if analysis:
        print("\nAnalysis results:")
        for category, items in analysis.items():
            if items:
                print(f"\n{category}: {len(items)} items")
                for item in items:
                    print(f"  - {item.get('company')}: {item.get('description')[:50]}...")
    
    # Format for Slack
    print("\nFormatting for Slack...")
    message = monitor.format_for_slack(analysis, date_formatted)
    
    print("\n" + "="*60)
    print("SLACK MESSAGE PREVIEW:")
    print("="*60)
    print(message)
    print("="*60)
    
    # Ask if user wants to send to Slack
    response = input("\nSend to Slack? (y/N): ")
    if response.lower() == 'y':
        monitor.send_slack_notification(message)
        print("✅ Sent to Slack!")
    else:
        print("❌ Not sent to Slack")

def main():
    """Main function"""
    print("LinkedIn Monitor - Manual Test")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Date provided as argument
        date_str = sys.argv[1]
        try:
            # Validate date format
            datetime.strptime(date_str, '%Y-%m-%d')
            test_specific_date(date_str)
        except ValueError:
            print(f"❌ Invalid date format: {date_str}")
            print("   Please use YYYY-MM-DD format (e.g., 2025-09-17)")
            sys.exit(1)
    else:
        # No date provided, use yesterday
        test_specific_date()

if __name__ == "__main__":
    main()