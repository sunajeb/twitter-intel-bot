#!/usr/bin/env python3
"""
Competitor API Response Formatter
Converts JSON response from competitor API into clean Slack-formatted text
"""

import json
import re
import requests
import time
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
            
            # Remove URL from the text AND remove any standalone URLs
            clean_text = re.sub(r'\s*\(https?://[^)]+\)', '', news_text).strip()
            # Remove standalone URLs like https://lnkd.in/xyz
            clean_text = re.sub(r'https?://\S+\.?\s*', '', clean_text).strip()
            # Clean up extra spaces and punctuation at the end
            clean_text = re.sub(r'[.\s]+$', '', clean_text).strip()
            
            # Format with hyperlinked emoji - clean and validate URL
            if url:
                # Clean URL of any trailing/leading whitespace and validate
                clean_url = url.strip()
                # Ensure URL is properly formatted
                if not clean_url.startswith(('http://', 'https://')):
                    clean_url = 'https://' + clean_url
                
                formatted_item = f"• *<{clean_url}|{company}>*: {clean_text}"
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


def parse_markdown_response(markdown_text: str) -> Dict[str, Any]:
    """
    Parse the new markdown format from competitor API
    
    Args:
        markdown_text: Markdown response from API
        
    Returns:
        Dictionary in the same format as the old JSON API
    """
    # Remove markdown code block markers
    content = extract_json_from_markdown(markdown_text)
    
    sections = {}
    current_section = None
    current_items = {}
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Check for section headers (### Section Name)
        if line.startswith('### '):
            # Save previous section if exists
            if current_section and current_items:
                sections[current_section] = current_items
                current_items = {}
            
            # Extract section name
            section_name = line[4:].strip()
            current_section = section_name
            
        # Check for list items (*   **Company:** ...)
        elif line.startswith('*   **') and ':**' in line:
            # Extract company name and content
            try:
                # Format: *   **Company:** Content (source: <url>)
                company_part = line[6:]  # Remove "*   **"
                if ':**' in company_part:
                    company, content = company_part.split(':**', 1)
                    company = company.strip()
                    content = content.strip()
                    
                    # Clean up the content
                    if content.endswith('.'):
                        content = content[:-1]
                    
                    # Store in dictionary format: {company: content}
                    current_items[company] = content
            except Exception as e:
                print(f"Error parsing line: {line} - {e}")
                continue
    
    # Add the last section
    if current_section and current_items:
        sections[current_section] = current_items
    
    return sections


def format_raw_text_as_slack(content: str) -> str:
    """
    Format raw text content for Slack with basic structure
    
    Args:
        content: Raw text content
        
    Returns:
        Formatted text for Slack
    """
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Convert markdown headers to Slack format
        if line.startswith('### '):
            section_name = line[4:].strip()
            formatted_lines.append(f"*{section_name}*")
        elif line.startswith('*   **') and ':**' in line:
            # Convert list items to Slack format with clickable company names
            try:
                company_part = line[6:]  # Remove "*   **"
                if ':**' in company_part:
                    company, content = company_part.split(':**', 1)
                    company = company.strip()
                    content = content.strip()
                    
                    # Extract LinkedIn URL from content
                    url_match = re.search(r'\[https://www\.linkedin\.com/[^\]]+\]', content)
                    url = url_match.group(0)[1:-1] if url_match else None
                    
                    # Clean up content - remove URL brackets and LinkedIn Post markers
                    if url_match:
                        content = content.replace(url_match.group(0), '')
                    content = re.sub(r'\s*\(LinkedIn Post\)', '', content)
                    content = re.sub(r'\[https?://[^\]]+\]', '', content)
                    content = re.sub(r'https?://\S+', '', content)
                    content = re.sub(r'\s+', ' ', content).strip()
                    
                    # Clean up content
                    if content.endswith('.'):
                        content = content[:-1]
                    
                    # Format with clickable company name if URL exists
                    if url:
                        formatted_lines.append(f"• *<{url}|{company}>*: {content}")
                    else:
                        formatted_lines.append(f"• *{company}*: {content}")
            except:
                # If parsing fails, just add the line as-is
                formatted_lines.append(f"• {line}")
        else:
            # Add other lines as-is
            formatted_lines.append(line)
    
    return "\n".join(formatted_lines)


def format_fallback_response(raw_response: str) -> str:
    """
    Format raw response as fallback when all parsing fails
    
    Args:
        raw_response: Raw API response
        
    Returns:
        Formatted text for Slack
    """
    # Extract content from markdown blocks if present
    content = extract_json_from_markdown(raw_response)
    
    # Truncate if too long (Slack has message limits)
    if len(content) > 3000:
        content = content[:3000] + "\n\n... (truncated)"
    
    # Add a header to indicate this is raw data
    return f"*📊 Competitor News (Raw Format)*\n\n```\n{content}\n```"


def format_competitor_news_from_raw_response(raw_response: str) -> str:
    """
    Convert raw competitor API response into clean Slack-formatted text
    Handles multiple response formats with fallback to raw response
    
    Args:
        raw_response: Raw response from competitor API
        
    Returns:
        Formatted text ready for Slack with hyperlinked emojis
    """
    if not raw_response or not raw_response.strip():
        return "No competitor news available"
    
    # Method 1: Try JSON parsing (original format)
    try:
        json_content = extract_json_from_markdown(raw_response)
        api_response = json.loads(json_content)
        if api_response:  # Check if not empty
            return format_competitor_news(api_response)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Method 2: Try markdown parsing (new format)
    try:
        api_response = parse_markdown_response(raw_response)
        if api_response:  # Check if not empty
            return format_competitor_news(api_response)
    except Exception as e:
        print(f"Markdown parsing failed: {e}")
    
    # Method 3: Handle pre-formatted text from API (clean it up)
    try:
        content = extract_json_from_markdown(raw_response)
        
        if content and len(content) > 50:
            cleaned_content = clean_pre_formatted_linkedin_content(content)
            if cleaned_content != "No competitor news available":
                return cleaned_content
            return format_raw_text_as_slack(content)
    except Exception as e:
        print(f"Text parsing failed: {e}")
    
    # Method 4: Fallback - return safe message instead of raw response
    print("⚠️ All parsing methods failed, returning safe message")
    return "No competitor news available"

def clean_pre_formatted_linkedin_content(content: str) -> str:
    """
    Clean up pre-formatted LinkedIn content from API to make it Slack-ready
    
    Args:
        content: Pre-formatted content with visible URLs and LinkedIn Post markers
        
    Returns:
        Clean Slack-formatted content with clickable links
    """
    if not content:
        return "No competitor news available"
    
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        if not line.strip():
            cleaned_lines.append(line)
            continue
            
        # Skip any explanatory header text
        if 'breakdown' in line.lower() or 'categorized as' in line.lower():
            continue
            
        # Process bullet points with company news (handle both • and * bullets, and **Company:** format)
        stripped_line = line.strip()
        
        # First check if this is a category header (like "*   **Fund Raise:**")
        # Be more specific - check that the category name is exactly what's between the **
        if ('**' in line and ':**' in line and not stripped_line.startswith('•')):
            category_line = line.strip()
            
            # Extract what's between ** and check if it's a known category
            match = re.search(r'\*\*([^*:]+):\*\*', category_line)
            if match:
                extracted_name = match.group(1).strip()
                
                # Only treat as category header if it's exactly one of our known categories
                known_categories = ['Fund Raise', 'Hiring', 'Customer Success', 'Product', 'GTM', 'Other']
                
                if extracted_name in known_categories:
                    # This is a category header
                    category_emojis = {
                        'Fund Raise': '💰',
                        'Hiring': '👥', 
                        'Customer Success': '🎯',
                        'Product': '🚀',
                        'GTM': '🎉',
                        'Other': '📰'
                    }
                    
                    emoji = category_emojis.get(extracted_name, '📋')
                    display_name = 'Events' if extracted_name == 'GTM' else extracted_name
                    formatted_line = f"*{emoji} {display_name}*"
                    cleaned_lines.append(formatted_line)
                else:
                    # Not a category header - treat as company line
                    # Process this as a company item using the same logic below
                    base_content = line.strip()
                    
                    # Extract company name first (handle format: "*   **Company:** content")
                    # Find the **Company:** part and split on it
                    if '**' in base_content and ':**' in base_content:
                        # Find where **Company:** starts and ends
                        start_idx = base_content.find('**')
                        end_idx = base_content.find(':**') + 3  # Include the :**
                        
                        if start_idx >= 0 and end_idx > start_idx:
                            # Extract company name between the ** markers
                            company_part = base_content[start_idx:end_idx]  # **Company:**
                            company_name = company_part[2:-3].strip()  # Remove ** and :**
                            
                            # Everything after :** is the content
                            content_text = base_content[end_idx:].strip()
                        else:
                            # Fallback - treat as regular line
                            company_name = None
                            content_text = base_content
                    else:
                        company_name = None
                        content_text = base_content
                        
                    if company_name:
                        # Process the company content (URL extraction, etc.)
                        # Find and extract the LinkedIn URL in the format (LinkedIn Post)[https://url]
                        linkedin_url_match = re.search(r'\(LinkedIn Post\)\[https://www\.linkedin\.com/[^\]]+\]', content_text)
                        if linkedin_url_match:
                            # Extract just the URL part
                            url_part = re.search(r'\[https://www\.linkedin\.com/[^\]]+\]', linkedin_url_match.group(0))
                            linkedin_url = url_part.group(0)[1:-1] if url_part else None
                            # Remove the entire (LinkedIn Post)[url] part
                            content_text = content_text.replace(linkedin_url_match.group(0), '')
                        else:
                            # Fallback: look for just [https://url] format
                            url_match = re.search(r'\[https://www\.linkedin\.com/[^\]]+\]', content_text)
                            linkedin_url = url_match.group(0)[1:-1] if url_match else None
                            if url_match:
                                content_text = content_text.replace(url_match.group(0), '')
                            # Remove (LinkedIn Post) markers separately
                            content_text = re.sub(r'\s*\(LinkedIn Post\)', '', content_text)
                        
                        # Clean content
                        content_text = re.sub(r'\[https?://[^\]]+\]', '', content_text)
                        content_text = re.sub(r'https?://\S+', '', content_text)
                        content_text = re.sub(r'\s+', ' ', content_text).strip()
                        content_text = re.sub(r'[:\s]+$', '', content_text)
                        
                        # Format with clickable company name if we found a LinkedIn URL
                        if linkedin_url:
                            formatted_content = f"- *<{linkedin_url}|{company_name}>*: {content_text}"
                        else:
                            formatted_content = f"- *{company_name}*: {content_text}"
                        
                        cleaned_lines.append(formatted_content)
                    else:
                        cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
        
        # Handle company lines that have indented * **Company:** format  
        elif ('**' in line and ':**' in line and not stripped_line.startswith('**')):
            # This is a company line like "    *   **ElevenLabs:** ..."
            base_content = line.strip()
            
            # Extract company name first (handle format: "*   **Company:** content")
            # Find the **Company:** part and split on it
            if '**' in base_content and ':**' in base_content:
                # Find where **Company:** starts and ends
                start_idx = base_content.find('**')
                end_idx = base_content.find(':**') + 3  # Include the :**
                
                if start_idx >= 0 and end_idx > start_idx:
                    # Extract company name between the ** markers
                    company_part = base_content[start_idx:end_idx]  # **Company:**
                    company_name = company_part[2:-3].strip()  # Remove ** and :**
                    
                    # Everything after :** is the content
                    content_text = base_content[end_idx:].strip()
                else:
                    # Fallback - treat as regular line
                    company_name = None
                    content_text = base_content
            else:
                company_name = None
                content_text = base_content
                
            if company_name:
                
                # Find and extract the LinkedIn URL in the format (LinkedIn Post)[https://url]
                linkedin_url_match = re.search(r'\(LinkedIn Post\)\[https://www\.linkedin\.com/[^\]]+\]', content_text)
                if linkedin_url_match:
                    # Extract just the URL part
                    url_part = re.search(r'\[https://www\.linkedin\.com/[^\]]+\]', linkedin_url_match.group(0))
                    linkedin_url = url_part.group(0)[1:-1] if url_part else None
                    # Remove the entire (LinkedIn Post)[url] part
                    content_text = content_text.replace(linkedin_url_match.group(0), '')
                else:
                    # Fallback: look for just [https://url] format
                    url_match = re.search(r'\[https://www\.linkedin\.com/[^\]]+\]', content_text)
                    linkedin_url = url_match.group(0)[1:-1] if url_match else None
                    if url_match:
                        content_text = content_text.replace(url_match.group(0), '')
                    # Remove (LinkedIn Post) markers separately
                    content_text = re.sub(r'\s*\(LinkedIn Post\)', '', content_text)
                
                # Remove any standalone URLs like [https://lnkd.in/xyz]
                content_text = re.sub(r'\[https?://[^\]]+\]', '', content_text)
                
                # Remove any remaining visible URLs
                content_text = re.sub(r'https?://\S+', '', content_text)
                
                # Clean up extra spaces and trailing punctuation
                content_text = re.sub(r'\s+', ' ', content_text).strip()
                content_text = re.sub(r'[:\s]+$', '', content_text)
                
                # Format with clickable company name if we found a LinkedIn URL
                if linkedin_url:
                    base_content = f"- *<{linkedin_url}|{company_name}>*: {content_text}"
                else:
                    base_content = f"- *{company_name}*: {content_text}"
            
            cleaned_lines.append(base_content)
        else:
            # Keep other lines as-is (empty lines, explanatory text, etc.)
            cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines)
    
    # Final pass: convert any remaining **text** to *text* for Slack compatibility
    result = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', result)
    
    # Convert asterisk bullet points to dashes for cleaner appearance
    result = re.sub(r'^\* \*', r'- *', result, flags=re.MULTILINE)
    
    # Add emojis to section headers (updated for dash format)
    emoji_replacements = {
        '- *Fund Raise:*': '*💰 Fund Raise*',
        '- *Hiring:*': '*👥 Hiring*', 
        '- *Customer Success:*': '*🎯 Customer Success*',
        '- *Product:*': '*🚀 Product*',
        '- *GTM:*': '*🎉 Events*',
        '- *Other:*': '*📰 Other*'
    }
    
    for old_header, new_header in emoji_replacements.items():
        result = result.replace(old_header, new_header)
    
    # If result is too empty, return fallback
    if len(result.strip()) < 50:
        return "No competitor news available"
        
    return result


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
        Formatted text ready for Slack with hyperlinked emojis, or "No competitor news available" on error
    """
    max_retries = 3
    timeout = 30
    backoff_factor = 2
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempting API call (attempt {attempt + 1}/{max_retries})")
            
            response = requests.get(
                api_url, 
                headers={'accept': 'application/json'},
                timeout=timeout
            )
            response.raise_for_status()
            
            formatted_result = format_competitor_news_from_raw_response(response.text)
            
            # Check if the result contains error messages
            if "Error parsing" in formatted_result or "Error fetching" in formatted_result:
                print(f"⚠️ API response contained errors: {formatted_result[:100]}...")
                return "No competitor news available"
            
            print("✅ Successfully fetched and formatted competitor news")
            return formatted_result
            
        except requests.Timeout as e:
            print(f"⏱️ Request timeout (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            continue
            
        except requests.HTTPError as e:
            if e.response.status_code in [502, 503, 504]:  # Gateway errors
                print(f"🚪 Gateway error (attempt {attempt + 1}/{max_retries}): {e.response.status_code}")
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    print(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                continue
            else:
                print(f"❌ HTTP error: {e}")
                return "No competitor news available"
                
        except requests.ConnectionError as e:
            print(f"🔌 Connection error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            continue
            
        except requests.RequestException as e:
            print(f"❌ Request error: {e}")
            return "No competitor news available"
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return "No competitor news available"
    
    print(f"💥 All {max_retries} attempts failed")
    return "No competitor news available"


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
