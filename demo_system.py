#!/usr/bin/env python3
"""
Demo script showing exactly how the system works in production
Simulates the complete workflow without hitting API limits
"""

from datetime import datetime
from twitter_monitor import TwitterMonitor

def demo_system_workflow():
    """Demonstrate the complete competitive intelligence system"""
    print("🚀 COMPETITIVE INTELLIGENCE SYSTEM DEMO")
    print("=" * 50)
    
    monitor = TwitterMonitor()
    
    # Show current accounts being monitored
    print("\n📋 ACCOUNTS CONFIGURATION:")
    try:
        with open("accounts.txt", 'r') as f:
            accounts = []
            for line_num, line in enumerate(f.readlines(), 1):
                line = line.strip()
                if line:
                    print(f"  {line_num}. {line}")
                    if ':' in line:
                        account, company = line.split(':', 1)
                        accounts.append((account.strip(), company.strip()))
                    else:
                        accounts.append((line.strip(), line.strip()))
        
        total_accounts = len(accounts)
        cycle_time = total_accounts * 15  # 15 minutes per account
        print(f"\n📊 MONITORING STATS:")
        print(f"  • Total accounts: {total_accounts}")
        print(f"  • Full cycle time: {cycle_time} minutes ({cycle_time//60}h {cycle_time%60}m)")
        print(f"  • Each account monitored every {cycle_time} minutes")
        
    except FileNotFoundError:
        print("  ❌ accounts.txt not found")
        return
    
    # Simulate how notifications work
    print(f"\n🔔 NOTIFICATION EXAMPLES:")
    print("  When significant news is found, immediate alerts like:")
    
    # Example 1: Product launch
    example1 = "Decagon: Launches new voice AI platform for enterprise customers 🔗"
    monitor.send_immediate_slack_notification(
        example1,
        "🎬 DEMO: Real-time alert example"
    )
    print(f"  ✅ Sent: {example1}")
    
    # Example 2: Funding news  
    example2 = "Sierra: Announces $50M Series B funding round 🔗\nPerplexity: Expands to European markets with new data centers 🔗"
    monitor.send_immediate_slack_notification(
        example2,
        "🎬 DEMO: Multiple headlines example"
    )
    print(f"  ✅ Sent: Multiple company updates")
    
    # Show daily workflow
    print(f"\n⏰ DAILY WORKFLOW:")
    print("  🌅 Every 15 minutes: Rotate through 1 account")
    print("     • Fetch last 24 hours of tweets")
    print("     • Analyze with Gemini AI") 
    print("     • Send immediate alert if significant news")
    print("     • Accumulate in daily summary")
    print("  🌄 7:30 AM IST: Send daily summary of yesterday's intelligence")
    print("  🔧 Manual trigger: Process ALL accounts immediately (60s delays)")
    
    # Show timeline example
    print(f"\n📅 EXAMPLE TIMELINE (with {total_accounts} accounts):")
    from datetime import datetime, timedelta
    
    current_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for i, (account, company) in enumerate(accounts[:6]):  # Show first 6
        run_time = current_time + timedelta(minutes=i*15)
        print(f"  {run_time.strftime('%H:%M')} - Monitor @{account} ({company})")
    
    if total_accounts > 6:
        print(f"  ... (continues for all {total_accounts} accounts)")
    
    # Send final demo summary
    demo_summary = f"""🎬 **SYSTEM DEMO COMPLETE**

📊 **Configuration:**
• {total_accounts} accounts monitored
• {cycle_time//60}h {cycle_time%60}m full cycle time
• 24-hour tweet windows
• Real-time AI analysis

🔔 **Notifications:**
• Immediate alerts when news breaks
• Daily summary at 7:30 AM IST
• Manual full-scan option available

✅ **System ready for production!**"""
    
    monitor.send_immediate_slack_notification(
        demo_summary,
        "🎬 DEMO: System overview"
    )
    print(f"\n✅ Demo complete! Check Slack for all notification examples.")

if __name__ == "__main__":
    demo_system_workflow()