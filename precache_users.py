#!/usr/bin/env python3
"""
Pre-cache user IDs to maximize Twitter Free tier efficiency
Uses the 3 user lookup requests per 15min to cache IDs for future tweet fetches
"""

import json
import time
from user_cache import UserIDCache
from twitter_monitor import TwitterMonitor

def precache_user_ids():
    """Use the 3 user lookup API calls to cache user IDs for accounts without cache"""
    monitor = TwitterMonitor()
    cache = UserIDCache()
    bearer_token = monitor.config.get('twitter_bearer_token')
    
    if not bearer_token:
        print("❌ Twitter Bearer Token not found")
        return
    
    # Load all accounts
    accounts = []
    try:
        with open("accounts.txt", 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if ':' in line:
                    account, _ = line.split(':', 1)
                    accounts.append(account.strip())
                elif line:
                    accounts.append(line.strip())
    except FileNotFoundError:
        print("❌ accounts.txt not found")
        return
    
    # Check which accounts need caching
    cached_data = cache.load_cache()
    uncached_accounts = []
    
    for account in accounts:
        if account not in cached_data or not cache.is_cache_valid(cached_data.get(account, {})):
            uncached_accounts.append(account)
    
    if not uncached_accounts:
        print("✅ All accounts already cached")
        return
    
    print(f"📋 Found {len(uncached_accounts)} accounts needing cache: {uncached_accounts}")
    
    # Cache up to 3 accounts (API limit)
    accounts_to_cache = uncached_accounts[:3]
    
    print(f"🔄 Pre-caching {len(accounts_to_cache)} user IDs...")
    
    for i, account in enumerate(accounts_to_cache):
        if i > 0:
            print("⏱️ Waiting 5 seconds between requests...")
            time.sleep(5)
        
        user_id = cache.get_user_id(account, bearer_token)
        if user_id:
            print(f"✅ Cached @{account} -> {user_id}")
        else:
            print(f"❌ Failed to cache @{account}")
    
    remaining = len(uncached_accounts) - len(accounts_to_cache)
    if remaining > 0:
        print(f"⏳ {remaining} accounts still need caching - will cache in next cycles")

if __name__ == "__main__":
    precache_user_ids()