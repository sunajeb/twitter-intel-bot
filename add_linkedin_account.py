#!/usr/bin/env python3
"""
Add LinkedIn accounts to monitor
"""

import sys

def add_account(linkedin_url):
    """Add a LinkedIn account to the monitoring list"""
    # Validate URL format
    if not linkedin_url.startswith('https://www.linkedin.com/company/'):
        print("❌ Invalid LinkedIn URL format")
        print("   Expected format: https://www.linkedin.com/company/company-name/")
        return False
    
    # Load existing accounts
    try:
        with open('linkedin_accounts.txt', 'r') as f:
            accounts = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        accounts = []
    
    # Check if already exists
    if linkedin_url in accounts:
        print(f"⚠️  Account already exists: {linkedin_url}")
        return False
    
    # Add new account
    with open('linkedin_accounts.txt', 'a') as f:
        if accounts:  # Add newline if file is not empty
            f.write('\n')
        f.write(linkedin_url)
    
    print(f"✅ Added: {linkedin_url}")
    return True

def list_accounts():
    """List all monitored accounts"""
    try:
        with open('linkedin_accounts.txt', 'r') as f:
            accounts = [line.strip() for line in f if line.strip()]
        
        print(f"📋 Monitoring {len(accounts)} LinkedIn accounts:")
        for i, account in enumerate(accounts, 1):
            print(f"   {i}. {account}")
    except FileNotFoundError:
        print("❌ No accounts file found")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python add_linkedin_account.py <linkedin-url>  - Add account")
        print("  python add_linkedin_account.py list            - List accounts")
        print("\nExample:")
        print("  python add_linkedin_account.py https://www.linkedin.com/company/decagon/")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_accounts()
    else:
        add_account(command)

if __name__ == "__main__":
    main()