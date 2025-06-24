#!/usr/bin/env python3
"""
Daily summary sender - sends accumulated intelligence from previous day at 7:30 AM IST
"""

from datetime import datetime, timedelta
from daily_summary import DailyIntelligenceTracker
from twitter_monitor import TwitterMonitor

def send_daily_summary():
    """Send daily summary of yesterday's accumulated intelligence"""
    print(f"📰 Daily summary check - {datetime.now()}")
    
    tracker = DailyIntelligenceTracker()
    monitor = TwitterMonitor()
    
    # Get yesterday's summary (since we're running at 7:30 AM)
    # Note: Individual runs now fetch 24-hour windows, so this aggregates the previous day's findings
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    summary = tracker.get_daily_summary(yesterday)
    
    if summary == "Nothing important today":
        print(f"📭 No competitive intelligence found for {yesterday}")
        # Still send a notification to confirm the system is working
        monitor.send_daily_summary_notification(
            f"📭 No significant competitive intelligence detected on {yesterday}.\n\n_Daily monitoring system is active and running._"
        )
    else:
        print(f"📤 Sending daily summary for {yesterday}")
        print(f"Summary preview: {summary[:200]}...")
        
        # Add header with date and account count
        account_count = len(summary.split('\n'))
        formatted_summary = f"**Yesterday's Competitive Intelligence Summary ({yesterday})**\n\n{summary}\n\n_Monitoring system processed {account_count} intelligence items._"
        
        monitor.send_daily_summary_notification(formatted_summary)
    
    # Cleanup old data (keep 7 days)
    tracker.cleanup_old_data()
    print("🧹 Cleaned up old data")

if __name__ == "__main__":
    send_daily_summary()