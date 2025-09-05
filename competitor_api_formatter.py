#!/usr/bin/env python3
"""
Competitor API Response Formatter
Converts JSON response from competitor API into clean Slack-formatted text
"""

import json
import re
import requests
from typing import Dict, Any


def format_competitor_news(api_response: Dict[str, Any]) -> str:
    """
    Convert competitor API response into clean Slack-formatted text
    
    Args:
        api_response: JSON response from competitor API
        
    Returns:
        Formatted text ready for Slack with hyperlinked emojis
    """
    if not api_response:
        return "No competitor news available"
    
    formatted_sections = []
    
    # Define section headers mapping
    section_headers = {
        "Fund Raise": "💰 Fund Raise",
        "Customer Success": "🎯 Customer Success", 
        "Product": "🚀 Product",
        "GTM": "📈 Go-to-Market",
        "Hiring": "👥 Hiring",
        "Other": "📰 Other"
    }
    
    for section_key, section_data in api_response.items():
        if not section_data:
            continue
            
        # Get formatted section header
        header = section_headers.get(section_key, f"📋 {section_key}")
        formatted_sections.append(f"*{header}*")
        
        # Process each company in the section
        for company, news_text in section_data.items():
            # Extract URL from the text (assuming it's at the end in parentheses)
            url_match = re.search(r'\(https?://[^)]+\)', news_text)
            url = url_match.group(0)[1:-1] if url_match else None
            
            # Remove URL from the text
            clean_text = re.sub(r'\s*\(https?://[^)]+\)', '', news_text).strip()
            
            # Format with hyperlinked emoji
            if url:
                formatted_item = f"• *{company}*: {clean_text} <{url}|🔗>"
            else:
                formatted_item = f"• *{company}*: {clean_text}"
                
            formatted_sections.append(formatted_item)
        
        formatted_sections.append("")  # Add spacing between sections
    
    return "\n".join(formatted_sections)


def extract_json_from_markdown(markdown_text: str) -> str:
    """
    Extract JSON content from markdown code blocks
    
    Args:
        markdown_text: Raw response that may contain markdown formatting
        
    Returns:
        Clean JSON string
    """
    # Remove markdown code block markers
    json_content = re.sub(r'^```markdown\s*', '', markdown_text, flags=re.MULTILINE)
    json_content = re.sub(r'\s*```$', '', json_content, flags=re.MULTILINE)
    return json_content.strip()


def format_competitor_news_from_raw_response(raw_response: str) -> str:
    """
    Convert raw competitor API response (with markdown) into clean Slack-formatted text
    
    Args:
        raw_response: Raw response from competitor API (may include markdown)
        
    Returns:
        Formatted text ready for Slack with hyperlinked emojis
    """
    try:
        # Extract JSON from markdown if present
        json_content = extract_json_from_markdown(raw_response)
        
        # Parse and format
        api_response = json.loads(json_content)
        return format_competitor_news(api_response)
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {e}"


def format_competitor_news_from_json_string(json_string: str) -> str:
    """
    Convert competitor API response from JSON string into clean Slack-formatted text
    
    Args:
        json_string: JSON string response from competitor API
        
    Returns:
        Formatted text ready for Slack with hyperlinked emojis
    """
    try:
        api_response = json.loads(json_string)
        return format_competitor_news(api_response)
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {e}"


def get_and_format_competitor_news(api_url: str = "https://playground-server.dev.nurixlabs.tech/get_competitor_news") -> str:
    """
    Fetch competitor news from API and format it for Slack in one step
    
    Args:
        api_url: URL of the competitor news API
        
    Returns:
        Formatted text ready for Slack with hyperlinked emojis
    """
    try:
        response = requests.get(api_url, headers={'accept': 'application/json'})
        response.raise_for_status()
        return format_competitor_news_from_raw_response(response.text)
    except requests.RequestException as e:
        return f"Error fetching competitor news: {e}"


# Example usage and testing
if __name__ == "__main__":
    print("Testing competitor API formatter...")
    print("=" * 60)
    
    # Method 1: One-step function (recommended)
    print("Method 1: Direct API call and formatting")
    print("-" * 40)
    slack_output = get_and_format_competitor_news()
    print(slack_output)
    
    print("\n" + "=" * 60)
    print("Method 2: Manual curl + formatting")
    print("-" * 40)
    
    # Method 2: Manual curl response formatting
    import subprocess
    try:
        curl_result = subprocess.run([
            'curl', '-X', 'GET', 
            'https://playground-server.dev.nurixlabs.tech/get_competitor_news',
            '-H', 'accept: application/json', '-s'
        ], capture_output=True, text=True)
        
        if curl_result.returncode == 0:
            formatted_output = format_competitor_news_from_raw_response(curl_result.stdout)
            print(formatted_output)
        else:
            print(f"Curl failed: {curl_result.stderr}")
    except Exception as e:
        print(f"Error running curl: {e}")
