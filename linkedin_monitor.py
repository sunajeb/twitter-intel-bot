#!/usr/bin/env python3
"""
LinkedIn Monitor - Direct implementation without API/database dependencies
Fetches LinkedIn posts from ScrapIn, analyzes with Gemini, and sends to Slack
"""

import requests
from datetime import datetime, timedelta, timezone
import json
import os
import time
import random
import google.generativeai as genai
from typing import List, Dict, Optional
import re

class LinkedInMonitor:
    def __init__(self):
        # Load configuration
        self.config = self.load_config()
        
        # Check for GitHub Actions environment
        if os.getenv('GITHUB_ACTIONS'):
            print("Running in GitHub Actions environment")
        
        # Configure Gemini
        gemini_key = self.config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            raise ValueError("Gemini API key not found in config or environment")
        genai.configure(api_key=gemini_key)
        model_name = self.config.get('gemini_model') or os.getenv('GEMINI_MODEL') or 'gemini-2.0-flash'
        self.model = genai.GenerativeModel(model_name)
        
        # ScrapIn API configuration
        self.scrapin_api_key = self.config.get('scrapin_api_key') or os.getenv('SCRAPIN_API')
        if not self.scrapin_api_key:
            raise ValueError("ScrapIn API key not found in config or environment")
        self.scrapin_url = "https://api.scrapin.io/v1/enrichment/companies/activities/posts"
    
    def load_config(self) -> dict:
        """Load configuration from file"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def load_accounts(self) -> List[str]:
        """Load LinkedIn accounts to monitor"""
        try:
            with open('linkedin_accounts.txt', 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error loading accounts: {e}")
            return []
    
    def retry_with_backoff(self, func, max_retries=3, base_delay=1, max_delay=60):
        """Retry a function with exponential backoff"""
        for attempt in range(max_retries + 1):
            try:
                return func()
            except requests.exceptions.RequestException as e:
                if attempt == max_retries:
                    raise e
                
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
    
    def get_linkedin_posts(self, linkedin_url: str, start_date: str, end_date: str) -> List[Dict]:
        """Fetch LinkedIn posts for a company within a date range"""
        querystring = {
            "apikey": self.scrapin_api_key,
            "linkedInUrl": linkedin_url
        }
        
        def make_request():
            response = requests.get(self.scrapin_url, params=querystring, timeout=30)
            response.raise_for_status()
            return response.json()
        
        try:
            # Use retry logic for the API call
            data = self.retry_with_backoff(make_request)
            
            if not data.get('success'):
                raise ValueError(f"API request failed: {data}")
            
            # Filter posts by date range
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            
            filtered_posts = []
            for post in data.get('posts', []):
                try:
                    post_date = datetime.fromisoformat(post['activityDate'].replace('Z', '+00:00'))
                    post_date = post_date.replace(tzinfo=None)
                    
                    if start_datetime <= post_date <= end_datetime:
                        filtered_posts.append({
                            "text": post['text'],
                            "url": post['activityUrl'],
                            "date": post['activityDate'],
                            "company_name": self.extract_company_name(linkedin_url)
                        })
                except (KeyError, ValueError) as e:
                    print(f"Error processing post: {e}")
                    continue
            
            return filtered_posts
        
        except Exception as e:
            print(f"Failed to fetch LinkedIn posts for {linkedin_url}: {str(e)}")
            return []
    
    def extract_company_name(self, linkedin_url: str) -> str:
        """Extract company name from LinkedIn URL"""
        # Extract from URL pattern: /company/company-name/
        parts = linkedin_url.strip('/').split('/')
        if 'company' in parts:
            idx = parts.index('company')
            if idx + 1 < len(parts):
                return parts[idx + 1].title()
        return "Unknown Company"
    
    def analyze_posts_with_gemini(self, all_posts: List[Dict], date: str) -> Dict:
        """Analyze posts using Gemini and return structured data"""
        if not all_posts:
            return {}
        
        # Group posts by company
        company_posts = {}
        for post in all_posts:
            company = post['company_name']
            if company not in company_posts:
                company_posts[company] = []
            company_posts[company].append(post)
        
        # Create posts text for Gemini
        posts_text = ""
        for company, posts in company_posts.items():
            posts_text += f"\n\nPosts from {company}:\n"
            for i, post in enumerate(posts):
                posts_text += f"\nPost {i+1}:\n{post['text']}\nURL: {post['url']}\n"
        
        prompt = f"""
        Analyze the following LinkedIn posts from {date} and categorize them into relevant business intelligence categories. Use SHORT HEADLINES (3–8 words, no trailing period).

        STRICTLY INCLUDE ONLY:
        - Funding rounds or material financial milestones
        - Product launches or major feature releases
        - Significant partnerships/integrations
        - Major customer wins/case studies
        - Material technology breakthroughs
        - Key executive hires or org changes
        - Market expansion/new business lines

        STRICTLY EXCLUDE (mark as noise, do not output):
        - Awards, shortlists, nominations, anniversaries, generic celebrations
        - Routine marketing content, webinars, events (unless tied to a launch/partnership)
        - Generic industry commentary or thought leadership
        - Reshares/reposts of the same announcement (deduplicate similar messages)
        
        Return the analysis as a valid JSON object with the following structure:
        {{
            "fund_raise": [
                {{
                    "company": "Company Name",
                    "headline": "Short headline",
                    "url": "post URL",
                    "critical": true
                }}
            ],
            "hiring": [
                {{
                    "company": "Company Name", 
                    "headline": "Short headline",
                    "url": "post URL",
                    "critical": true
                }}
            ],
            "customer_success": [
                {{
                    "company": "Company Name",
                    "headline": "Short headline",
                    "url": "post URL",
                    "critical": true
                }}
            ],
            "product": [
                {{
                    "company": "Company Name",
                    "headline": "Short headline",
                    "url": "post URL",
                    "critical": true
                }}
            ],
            "partnerships": [
                {{
                    "company": "Company Name",
                    "headline": "Short headline",
                    "url": "post URL",
                    "critical": true
                }}
            ],
            "other": [
                {{
                    "company": "Company Name",
                    "headline": "Short headline",
                    "url": "post URL",
                    "critical": true
                }}
            ]
        }}
        
        IMPORTANT:
        - Only include categories that have actual information
        - Use short, headline-style phrases (no full sentences)
        - Focus on business-relevant information
        - Use the exact URL from the post
        - Return ONLY valid JSON, no markdown formatting or extra text
        - If no significant updates, return an empty JSON object: {{}}
        - CRITICAL FLAG: Set "critical": true for high‑impact items (funding, acquisition, major revenue, marquee partnerships, landmark product launches, IPO/exits). Omit when not applicable.
        
        Posts to analyze:
        {posts_text}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up the response - remove markdown code blocks if present
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            # Additional cleanup: remove any remaining markdown or extra formatting
            result_text = result_text.strip()
            
            # Remove any trailing commas before closing braces/brackets (common JSON error)
            result_text = re.sub(r',\s*}', '}', result_text)
            result_text = re.sub(r',\s*]', ']', result_text)
            
            # Log the cleaned response for debugging
            print(f"\n=== GEMINI RESPONSE (cleaned) ===\n{result_text[:500]}...\n" if len(result_text) > 500 else f"\n=== GEMINI RESPONSE (cleaned) ===\n{result_text}\n")
            
            # Parse JSON with better error handling
            try:
                return json.loads(result_text)
            except json.JSONDecodeError as je:
                print(f"JSON parse error: {je}")
                print(f"Error at position {je.pos} in response")
                # Try to extract valid JSON portion if possible
                try:
                    # Find the first { and last } to extract JSON object
                    start = result_text.find('{')
                    end = result_text.rfind('}')
                    if start >= 0 and end > start:
                        json_portion = result_text[start:end+1]
                        return json.loads(json_portion)
                except:
                    pass
                # If all else fails, return empty dict
                return {}
        
        except Exception as e:
            print(f"Error analyzing posts with Gemini: {e}")
            return {}
    
    def format_for_slack(self, analysis: Dict, date: str) -> str:
        """Format as grouped, quoted blocks with per‑item links."""
        # Convert date format from YYYY-MM-DD to '16 Sep' format
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%a, %d %b').replace(', 0', ', ').replace(' 0', ' ')
        except:
            formatted_date = date  # fallback to original if parsing fails
            
        if not analysis or all(len(items) == 0 for items in analysis.values()):
            return f"*:date: {formatted_date}: Linkedin*\n\nNo significant updates today."
        
        # Emoji mapping for categories
        emoji_map = {
            'fund_raise': '💰',
            'hiring': '👥',
            'customer_success': '🎯',
            'product': '🚀',
            'partnerships': '🤝',
            'other': '📰'
        }
        
        # Category display names
        category_names = {
            'fund_raise': 'Fund Raise',
            'hiring': 'Hiring',
            'customer_success': 'Customer Success',
            'product': 'Product',
            'partnerships': 'Partnerships',
            'other': 'Other'
        }
        
        def normalize_headline(s: str) -> str:
            import re
            s = s.lower().strip()
            s = re.sub(r"[\s\-–—]+", " ", s)
            s = re.sub(r"[^a-z0-9 ]", "", s)
            return s

        message = f"*:date: {formatted_date}: Linkedin*\n"
        
        # Stable category ordering like Twitter
        category_order = ['fund_raise','partnerships','product','customer_success','hiring','other']
        for category in category_order:
            items = analysis.get(category) or []
            if items and len(items) > 0:
                emoji = emoji_map.get(category, '📋')
                name = category_names.get(category, category.replace('_', ' ').title())
                
                # Add category header with emoji
                message += f"\n*{emoji} {name}:*\n"
                
                # Group items by company and dedupe similar headlines
                company_map = {}
                for item in items:
                    comp = item.get('company', 'Unknown')
                    company_map.setdefault(comp, []).append(item)

                for comp, comp_items in company_map.items():
                    # Dedupe by normalized headline
                    seen = set()
                    unique = []
                    for it in comp_items:
                        key = normalize_headline(it.get('headline') or it.get('description',''))
                        if key and key not in seen:
                            seen.add(key)
                            unique.append(it)

                    # Company header quoted
                    first_url = (unique[0].get('url') if unique and unique[0].get('url') else '')
                    # Company header — no link on company name
                    message += f"> {comp}\n"

                    for it in unique:
                        url = it.get('url','')
                        headline = (it.get('headline') or it.get('description','')).strip().rstrip('.')
                        # Siren only for funding or acquisitions
                        hl = headline.lower()
                        is_siren = (category == 'fund_raise') or ('acquisition' in hl or 'acquires' in hl or 'acquired' in hl or 'merger' in hl or 'acquire' in hl)
                        prefix = "🚨 " if is_siren else ""
                        if url:
                            message += f"> • {prefix}{headline} <{url}|↗>\n"
                        else:
                            message += f"> • {prefix}{headline}\n"

        return message
    
    def send_slack_notification(self, message: str):
        """Send notification to Slack"""
        webhook_url = self.config.get('slack_webhook_url') or os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            print("Slack webhook URL not configured")
            return
        
        payload = {
            "text": message,
            "unfurl_links": False,
            "unfurl_media": False
        }
        
        try:
            response = requests.post(webhook_url, json=payload)
            if response.status_code == 200:
                print("Slack notification sent successfully")
            else:
                print(f"Failed to send Slack notification: {response.text}")
        except Exception as e:
            print(f"Error sending Slack notification: {e}")
    
    def run_daily_analysis(self):
        """Run the daily LinkedIn analysis"""
        # Get yesterday's date (or today for testing)
        # Allow override via command line argument or environment variable
        import sys
        if len(sys.argv) > 1:
            date_str = sys.argv[1]
            print(f"Using provided date: {date_str}")
        else:
            # Use today's date by default so Slack message reflects current date
            today = datetime.now()
            date_str = today.strftime('%Y-%m-%d')
        
        print(f"Running LinkedIn analysis for {date_str}")
        
        # Load accounts
        accounts = self.load_accounts()
        if not accounts:
            print("No LinkedIn accounts to monitor")
            return
        
        # Fetch posts from all accounts
        all_posts = []
        for account_url in accounts:
            print(f"Fetching posts from {account_url}")
            posts = self.get_linkedin_posts(account_url, date_str, date_str)
            all_posts.extend(posts)
            
            # Small delay between requests
            if len(accounts) > 1:
                time.sleep(2)
        
        print(f"Fetched {len(all_posts)} posts total")
        
        # Log all fetched posts for debugging
        if all_posts:
            print("\n=== FETCHED POSTS ===\n")
            for i, post in enumerate(all_posts, 1):
                print(f"Post {i} - {post['company_name']}:")
                print(f"  Date: {post['date']}")
                print(f"  URL: {post['url']}")
                print(f"  Text preview: {post['text'][:200]}..." if len(post['text']) > 200 else f"  Text: {post['text']}")
                print()
        else:
            print("No posts found for the specified date range.")
        
        # Analyze with Gemini
        analysis = self.analyze_posts_with_gemini(all_posts, date_str)
        
        # Format for Slack
        slack_message = self.format_for_slack(analysis, date_str)
        
        # Send to Slack
        self.send_slack_notification(slack_message)
        
        print("Daily LinkedIn analysis completed")

if __name__ == "__main__":
    monitor = LinkedInMonitor()
    monitor.run_daily_analysis()
