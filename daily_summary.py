#!/usr/bin/env python3
"""
Daily intelligence accumulator - collects headlines throughout the day
and sends a summary at the end of the day
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict


class DailyIntelligenceTracker:
    def __init__(self, storage_file: str = "daily_intelligence.json"):
        self.storage_file = storage_file
        
    def add_intelligence(self, headlines: str, run_info: str = ""):
        """Add new intelligence from a monitoring run"""
        if not headlines or headlines == "Nothing important today":
            return
            
        today = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%H:%M')
        
        # Load existing data
        data = self.load_daily_data()
        
        # Add new entry
        if today not in data:
            data[today] = []
            
        entry = {
            'timestamp': timestamp,
            'headlines': headlines,
            'run_info': run_info
        }
        
        data[today].append(entry)
        
        # Save updated data
        self.save_daily_data(data)
        
    def load_daily_data(self) -> Dict:
        """Load accumulated intelligence data"""
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def save_daily_data(self, data: Dict):
        """Save accumulated intelligence data"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save daily data: {e}")
            
    def get_daily_summary(self, date: str = None) -> str:
        """Get accumulated intelligence for a specific date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        data = self.load_daily_data()
        day_data = data.get(date, [])
        
        if not day_data:
            return "Nothing important today"
            
        # Combine all headlines from the day
        all_headlines = []
        
        for entry in day_data:
            headlines = entry['headlines']
            if headlines and headlines != "Nothing important today":
                all_headlines.extend(headlines.split('\n'))
        
        # Remove duplicates while preserving order
        unique_headlines = []
        seen = set()
        
        for headline in all_headlines:
            headline = headline.strip()
            if headline and headline not in seen:
                unique_headlines.append(headline)
                seen.add(headline)
        
        if not unique_headlines:
            return "Nothing important today"
            
        return '\n'.join(unique_headlines)
        
    def should_send_daily_summary(self) -> bool:
        """Check if it's time to send daily summary (once per day at morning)"""
        from datetime import datetime
        import pytz
        
        # Convert to IST (UTC+5:30)
        ist = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist)
        current_hour = current_time_ist.hour
        current_minute = current_time_ist.minute
        
        # Send summary at 7:30 AM IST if we have content from previous day
        if current_hour == 7 and current_minute == 30:
            # Get yesterday's summary since we're sending morning summary
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            summary = self.get_daily_summary(yesterday)
            return summary != "Nothing important today"
            
        return False
        
    def cleanup_old_data(self, days_to_keep: int = 7):
        """Remove data older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        data = self.load_daily_data()
        cleaned_data = {
            date: entries for date, entries in data.items() 
            if date >= cutoff_str
        }
        
        self.save_daily_data(cleaned_data)


if __name__ == "__main__":
    tracker = DailyIntelligenceTracker()
    
    # Test the system
    print("=== DAILY INTELLIGENCE TRACKER TEST ===")
    
    # Add some test intelligence
    tracker.add_intelligence("Decagon: Raises $131M Series C funding round 🔗", "Rotation cycle 1/3: 2 accounts")
    tracker.add_intelligence("Sierra: Launches new voice AI platform 🔗", "Rotation cycle 2/3: 2 accounts")
    
    # Get summary
    summary = tracker.get_daily_summary()
    print(f"Today's summary:\n{summary}")
    
    # Check if should send
    should_send = tracker.should_send_daily_summary()
    print(f"Should send daily summary: {should_send}")