#!/usr/bin/env python3
"""
Debug TwitterAPI.io API responses to understand what's happening
"""

import requests
import json

def debug_api_calls():
    """Debug the actual API responses"""
    api_key = "new1_3888e5e515a14b58860d269717014769"
    base_url = "https://api.twitterapi.io"
    
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    print("🔍 Debugging TwitterAPI.io responses...")
    print(f"API Key: {api_key}")
    print()
    
    # Test 1: Connection test (tweets by ID)
    print("1. Testing tweets by ID endpoint:")
    url = f"{base_url}/twitter/tweets"
    params = {'tweet_ids': '1846987139428634858'}
    
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"   URL: {url}")
    print(f"   Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    print(f"   Response: {response.text[:500]}...")
    print()
    
    # Test 2: User tweets endpoint with yellowdotai
    print("2. Testing user tweets endpoint (yellowdotai):")
    url = f"{base_url}/twitter/user/last_tweets"
    params = {
        'userName': 'yellowdotai',
        'count': 5
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    print(f"   URL: {url}")
    print(f"   Params: {params}")
    print(f"   Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    print(f"   Response: {response.text}")
    print()
    
    # Test 3: User tweets endpoint with DecagonAI
    print("3. Testing user tweets endpoint (DecagonAI):")
    params = {
        'userName': 'DecagonAI',
        'count': 5
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    print(f"   URL: {url}")
    print(f"   Params: {params}")
    print(f"   Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    print(f"   Response: {response.text}")

if __name__ == "__main__":
    debug_api_calls()