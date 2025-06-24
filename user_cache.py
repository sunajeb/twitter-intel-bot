#!/usr/bin/env python3
"""
User ID caching to reduce API calls
Cache user lookups to avoid repeated calls for the same users
"""

import json
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional


class UserIDCache:
    def __init__(self, cache_file: str = "user_id_cache.json"):
        self.cache_file = cache_file
        self.cache_duration_days = 30  # Cache user IDs for 30 days
        
    def load_cache(self) -> Dict:
        """Load cached user IDs"""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def save_cache(self, cache: Dict):
        """Save user ID cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save user cache: {e}")
            
    def is_cache_valid(self, cached_entry: Dict) -> bool:
        """Check if cached entry is still valid"""
        if 'cached_at' not in cached_entry:
            return False
            
        cached_time = datetime.fromisoformat(cached_entry['cached_at'])
        expiry_time = cached_time + timedelta(days=self.cache_duration_days)
        
        return datetime.now() < expiry_time
        
    def get_user_id(self, username: str, bearer_token: str) -> Optional[str]:
        """Get user ID from cache or API"""
        cache = self.load_cache()
        
        # Check cache first
        if username in cache:
            cached_entry = cache[username]
            if self.is_cache_valid(cached_entry):
                print(f"📋 Using cached user ID for @{username}")
                return cached_entry['user_id']
            else:
                print(f"🔄 Cache expired for @{username}, fetching from API")
        
        # Fetch from API
        url = f"https://api.twitter.com/2/users/by/username/{username}"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            print(f"⚠️ Rate limit hit for @{username} user lookup - will retry next cycle")
            return None
        elif response.status_code != 200:
            print(f"Error fetching user ID for {username}: {response.text}")
            return None
            
        user_data = response.json()
        if 'data' not in user_data:
            print(f"No user data found for {username}")
            return None
            
        user_id = user_data['data']['id']
        
        # Cache the result
        cache[username] = {
            'user_id': user_id,
            'cached_at': datetime.now().isoformat()
        }
        
        self.save_cache(cache)
        print(f"💾 Cached user ID for @{username}")
        
        return user_id
        
    def cleanup_expired_cache(self):
        """Remove expired entries from cache"""
        cache = self.load_cache()
        cleaned_cache = {}
        
        for username, entry in cache.items():
            if self.is_cache_valid(entry):
                cleaned_cache[username] = entry
                
        if len(cleaned_cache) != len(cache):
            self.save_cache(cleaned_cache)
            removed_count = len(cache) - len(cleaned_cache)
            print(f"🧹 Cleaned up {removed_count} expired cache entries")


if __name__ == "__main__":
    # Test the cache system
    cache = UserIDCache()
    print("=== USER ID CACHE TEST ===")
    
    # This would normally require your actual bearer token
    # cache.get_user_id("DecagonAI", "your_token_here")
    
    cache.cleanup_expired_cache()
    print("Cache test completed")