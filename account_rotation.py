#!/usr/bin/env python3
"""
Account rotation system for Twitter Free tier API limits
Handles multiple accounts by rotating through them across multiple runs
"""

import json
import os
from datetime import datetime
from typing import List, Tuple


class AccountRotator:
    def __init__(self, accounts_file: str = "accounts.txt", state_file: str = "rotation_state.json", api_tier: str = "free"):
        self.accounts_file = accounts_file
        self.state_file = state_file
        
        # Set max accounts based on API tier limits from Twitter docs
        # Free tier: user lookup=3/15min, tweets=1/15min PER APP
        # With perfect caching, we can only fetch 1 account's tweets per 15min cycle
        tier_limits = {
            'free': 1,      # Free: Only 1 tweet fetch per 15min (bottleneck)
            'basic': 5,     # Basic: 10 tweet requests per 15min 
            'pro': 25       # Pro: Much higher limits
        }
        
        self.max_accounts_per_run = tier_limits.get(api_tier.lower(), 2)
        self.api_tier = api_tier
        
    def load_all_accounts(self) -> List[Tuple[str, str]]:
        """Load all accounts from accounts.txt"""
        accounts = []
        try:
            with open(self.accounts_file, 'r') as f:
                for line in f.readlines():
                    line = line.strip()
                    if not line:
                        continue
                    
                    if ':' in line:
                        account, company = line.split(':', 1)
                        accounts.append((account.strip(), company.strip()))
                    else:
                        account = line.strip()
                        accounts.append((account, account))
                        
            return accounts
        except FileNotFoundError:
            print(f"Accounts file {self.accounts_file} not found")
            return [('DecagonAI', 'Decagon'), ('SierraPlatform', 'Sierra')]
    
    def load_rotation_state(self) -> dict:
        """Load current rotation state"""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'last_index': 0,
                'last_run': None,
                'total_accounts': 0
            }
    
    def save_rotation_state(self, state: dict):
        """Save rotation state"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save rotation state: {e}")
    
    def get_accounts_for_this_run(self) -> List[Tuple[str, str]]:
        """Get the accounts to monitor in this run"""
        all_accounts = self.load_all_accounts()
        total_accounts = len(all_accounts)
        
        if total_accounts <= self.max_accounts_per_run:
            # If we have fewer accounts than max, return all
            return all_accounts
        
        # Load rotation state
        state = self.load_rotation_state()
        last_index = state.get('last_index', 0)
        
        # Calculate accounts for this run
        start_index = last_index
        end_index = min(start_index + self.max_accounts_per_run, total_accounts)
        
        current_accounts = all_accounts[start_index:end_index]
        
        # Update rotation state
        next_index = end_index
        if next_index >= total_accounts:
            next_index = 0  # Wrap around to start
        
        new_state = {
            'last_index': next_index,
            'last_run': datetime.now().isoformat(),
            'total_accounts': total_accounts,
            'current_cycle_accounts': [f"{acc}:{comp}" for acc, comp in current_accounts]
        }
        
        self.save_rotation_state(new_state)
        
        return current_accounts
    
    def get_rotation_info(self) -> str:
        """Get human-readable rotation information"""
        all_accounts = self.load_all_accounts()
        state = self.load_rotation_state()
        
        total = len(all_accounts)
        current_accounts = state.get('current_cycle_accounts', [])
        
        if total <= self.max_accounts_per_run:
            return f"Monitoring all {total} accounts (within API limits)"
        
        cycle_length = (total + self.max_accounts_per_run - 1) // self.max_accounts_per_run  # Ceiling division
        current_cycle = (state.get('last_index', 0) // self.max_accounts_per_run) + 1
        
        return f"Rotation cycle {current_cycle}/{cycle_length}: {len(current_accounts)} accounts this run"


if __name__ == "__main__":
    rotator = AccountRotator()
    accounts = rotator.get_accounts_for_this_run()
    
    print("=== ACCOUNT ROTATION TEST ===")
    print(f"Accounts for this run: {accounts}")
    print(f"Rotation info: {rotator.get_rotation_info()}")
    
    # Show next few rotations
    print("\nNext few rotations:")
    for i in range(5):
        next_accounts = rotator.get_accounts_for_this_run()
        print(f"  Run {i+1}: {[acc for acc, _ in next_accounts]}")