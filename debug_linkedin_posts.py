#!/usr/bin/env python3
"""
Debug script to fetch and display LinkedIn posts without AI analysis
Usage: python debug_linkedin_posts.py [YYYY-MM-DD]
"""

import requests
from datetime import datetime, timedelta
import json
import sys
import time

def load_accounts():
    """Load LinkedIn accounts to monitor"""
    try:
        with open('linkedin_accounts.txt', 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error loading accounts: {e}")
        return []

def extract_company_name(linkedin_url: str) -> str:
    """Extract company name from LinkedIn URL"""
    parts = linkedin_url.strip('/').split('/')
    if 'company' in parts:
        idx = parts.index('company')
        if idx + 1 < len(parts):
            return parts[idx + 1].replace('-', ' ').title()
    return "Unknown Company"

def get_linkedin_posts(linkedin_url: str, date: str):
    """Fetch LinkedIn posts for a specific date"""
    scrapin_api_key = "sk_ccdfbe96fcb3815a7801ae40d0c3449e2817e28b"
    scrapin_url = "https://api.scrapin.io/v1/enrichment/companies/activities/posts"
    
    querystring = {
        "apikey": scrapin_api_key,
        "linkedInUrl": linkedin_url
    }
    
    try:
        response = requests.get(scrapin_url, params=querystring, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('success'):
            print(f"  ❌ API request failed for {linkedin_url}")
            return []
        
        # Filter posts by date
        target_date = datetime.strptime(date, '%Y-%m-%d')
        filtered_posts = []
        
        for post in data.get('posts', []):
            try:
                post_date = datetime.fromisoformat(post['activityDate'].replace('Z', '+00:00'))
                post_date = post_date.replace(tzinfo=None).date()
                
                if post_date == target_date.date():
                    filtered_posts.append(post)
            except Exception as e:
                continue
        
        return filtered_posts
    
    except Exception as e:
        print(f"  ❌ Error fetching posts: {e}")
        return []

def main():
    # Get date from command line or use yesterday
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"🔍 Fetching LinkedIn posts for: {date_str}")
    print("=" * 80)
    
    accounts = load_accounts()
    print(f"📋 Found {len(accounts)} accounts to monitor\n")
    
    total_posts = 0
    company_posts = {}
    
    for i, account_url in enumerate(accounts, 1):
        company_name = extract_company_name(account_url)
        print(f"[{i}/{len(accounts)}] Checking {company_name}...")
        
        posts = get_linkedin_posts(account_url, date_str)
        if posts:
            company_posts[company_name] = posts
            total_posts += len(posts)
            print(f"  ✅ Found {len(posts)} post(s)")
        else:
            print(f"  ⚪ No posts found")
        
        # Small delay between requests
        if i < len(accounts):
            time.sleep(1)
    
    print("\n" + "=" * 80)
    print(f"📊 SUMMARY: Found {total_posts} total posts from {len(company_posts)} companies")
    
    if company_posts:
        print("\n" + "=" * 80)
        print("📝 POST DETAILS:\n")
        
        for company_name, posts in company_posts.items():
            print(f"🏢 {company_name} ({len(posts)} posts)")
            print("-" * 40)
            
            for j, post in enumerate(posts, 1):
                print(f"\nPost {j}:")
                print(f"📅 Date: {post.get('activityDate', 'Unknown')}")
                print(f"🔗 URL: {post.get('activityUrl', 'No URL')}")
                print(f"💬 Text:")
                text = post.get('text', 'No text')
                # Show first 500 chars
                if len(text) > 500:
                    print(f"{text[:500]}...")
                    print(f"[... {len(text) - 500} more characters]")
                else:
                    print(text)
                print()
            
            print("=" * 80)
    
    # Save raw data for further analysis
    if company_posts:
        filename = f"linkedin_debug_{date_str}.json"
        with open(filename, 'w') as f:
            json.dump(company_posts, f, indent=2)
        print(f"\n💾 Saved raw data to: {filename}")

if __name__ == "__main__":
    main()