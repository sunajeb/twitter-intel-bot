#!/usr/bin/env python3
"""
Test the new hyperlink formatting
"""

import re
from dataclasses import dataclass

@dataclass
class Tweet:
    id: str
    text: str
    created_at: str
    username: str
    url: str
    is_reply: bool = False
    reply_to_tweet_id: str = None

def replace_tweet_ids_with_urls(headlines_text: str, tweets) -> str:
    """Replace TWEET_ID_X placeholders with hyperlinked company names like LinkedIn format"""
    if not headlines_text:
        return ""
    if not tweets:
        return headlines_text
    
    result = headlines_text
    
    # Replace each TWEET_ID_X with hyperlinked company name
    for i, tweet in enumerate(tweets):
        tweet_id_placeholder = f"TWEET_ID_{i}"
        
        # Find pattern: • Company: Description TWEET_ID_X
        # Use a more specific pattern that looks for the exact TWEET_ID_X at the end
        pattern = r'• ([^:]+): (.*?)' + re.escape(tweet_id_placeholder) + r'(?:\s|$)'
        
        def replace_match(match):
            company_name = match.group(1).strip()
            description = match.group(2).strip()
            # Create hyperlinked company name in Slack format
            hyperlinked_company = f"<{tweet.url}|{company_name}>"
            return f"• {hyperlinked_company}: {description}"
        
        result = re.sub(pattern, replace_match, result)
    
    return result

def test_format():
    """Test the formatting"""
    
    # Sample input (what Gemini would return)
    sample_input = """*💰 Fund Raise*
• Decagon: Raises $131M Series C funding round TWEET_ID_0

*🚀 Product*
• Sierra: Launches new voice AI platform for enterprise customers TWEET_ID_1"""
    
    # Sample tweets
    tweets = [
        Tweet(
            id="1234567890",
            text="We're excited to announce...",
            created_at="Mon Sep 15 17:09:29 +0000 2025", 
            username="DecagonAI",
            url="https://twitter.com/DecagonAI/status/1234567890"
        ),
        Tweet(
            id="1234567891",
            text="Introducing our new platform...",
            created_at="Mon Sep 15 16:09:29 +0000 2025",
            username="SierraPlatform", 
            url="https://twitter.com/SierraPlatform/status/1234567891"
        )
    ]
    
    print("📝 Original format:")
    print(sample_input)
    print()
    
    print("✅ New hyperlinked format:")
    result = replace_tweet_ids_with_urls(sample_input, tweets)
    print(result)
    print()
    
    print("🔗 Raw Slack format (what actually gets sent):")
    print(repr(result))

if __name__ == "__main__":
    test_format()