#!/usr/bin/env python3
"""
Production simulation - shows exactly how the system works in production
Uses mock data to demonstrate the complete workflow
"""

from datetime import datetime
from twitter_monitor import TwitterMonitor, Tweet

def simulate_production_run():
    """Simulate a production run with mock DecagonAI tweets"""
    print("🎯 PRODUCTION SIMULATION - DecagonAI Only")
    print("=" * 50)
    
    monitor = TwitterMonitor()
    monitor.account_to_company = {"DecagonAI": "Decagon"}
    
    # Simulate finding tweets (what would happen if rate limits weren't hit)
    print("🕐 Simulating: Fetching tweets from DecagonAI since last 24 hours...")
    
    # Mock tweets that could be found
    mock_tweets = [
        Tweet(
            id="1234567890123456789",
            text="Excited to announce Decagon's new AI agent platform! We're revolutionizing customer support with voice-first AI that understands context and delivers 95% accuracy in sentiment detection. Game changer for enterprise customers. 🚀",
            created_at="2025-06-24T15:30:00Z",
            username="DecagonAI",
            url="https://twitter.com/DecagonAI/status/1234567890123456789"
        ),
        Tweet(
            id="1234567890123456790",
            text="We're hiring! Looking for senior ML engineers to join our voice AI team. If you're passionate about building the future of conversational AI, let's chat. Remote-friendly, competitive equity package. #hiring #AI",
            created_at="2025-06-24T14:15:00Z",
            username="DecagonAI",
            url="https://twitter.com/DecagonAI/status/1234567890123456790"
        )
    ]
    
    print(f"📝 Found {len(mock_tweets)} tweets from @DecagonAI")
    for i, tweet in enumerate(mock_tweets):
        print(f"  Tweet {i+1}: {tweet.text[:80]}...")
    
    # Run analysis
    print("\n🤖 Running Gemini AI analysis...")
    analysis = monitor.analyze_tweets_with_gemini(mock_tweets)
    
    if analysis and analysis != "Nothing important today":
        print(f"🔍 Analysis result: {analysis}")
        
        # This is exactly what would be sent to Slack in production
        print("\n📤 Sending to Slack exactly as it would appear in production:")
        monitor.send_immediate_slack_notification(analysis)
        
        # Add to daily intelligence tracker
        from daily_summary import DailyIntelligenceTracker
        tracker = DailyIntelligenceTracker()
        tracker.add_intelligence(analysis, "Production run: @DecagonAI")
        print("✅ Added to daily intelligence accumulator")
        
    else:
        print("📰 No significant competitive intelligence found")
        # Still send a notification showing the system is working
        monitor.send_immediate_slack_notification(
            "No significant competitive intelligence detected in today's monitoring cycle."
        )
    
    print("\n🏁 Production simulation completed!")
    print("Check Slack to see the exact format you'll receive tomorrow.")

if __name__ == "__main__":
    simulate_production_run()