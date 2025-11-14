#!/usr/bin/env python3
"""
Daily Twitter Monitoring System for @DecagonAI and @SierraPlatform
Analyzes tweets using Gemini 2.5 Flash and sends notifications via Slack/Email
"""

import os
import json
import requests
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
import google.generativeai as genai
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


class TwitterMonitor:
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.setup_gemini()
        self.account_to_company = {}  # Will be loaded from twitter_accounts.txt
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {config_file} not found. Please create it with required API keys.")
            return {}
    
    def setup_gemini(self):
        """Initialize Gemini API"""
        genai.configure(api_key=self.config.get('gemini_api_key'))
        model_name = self.config.get('gemini_model', 'gemini-2.0-flash')
        self.model = genai.GenerativeModel(model_name)
    
    def fetch_twitter_data(self, username: str) -> List[Tweet]:
        """Fetch recent tweets from a Twitter username using TwitterAPI.io"""
        from twitter_api_io_client import TwitterAPIClient
        
        api_key = self.config.get('twitterapi_io_key')
        if not api_key:
            print("TwitterAPI.io API key not found in config - add 'twitterapi_io_key' to config.json")
            return []
        
        client = TwitterAPIClient(api_key)
        
        # Fetch tweets from last 24 hours using TwitterAPI.io
        tweets_data = client.get_user_tweets(username, hours_back=24, max_results=10)
        
        if not tweets_data:
            return []
        
        tweets = []
        for tweet_data in tweets_data:
            tweet = Tweet(
                id=tweet_data['id'],
                text=tweet_data['text'],
                created_at=tweet_data['created_at'],
                username=tweet_data['username'],
                url=tweet_data['url'],
                is_reply=tweet_data.get('is_reply', False),
                reply_to_tweet_id=tweet_data.get('reply_to_tweet_id')
            )
            tweets.append(tweet)
        
        return tweets
    
    def group_tweets_into_threads(self, tweets: List[Tweet]) -> List[Tweet]:
        """Group tweets and their replies into thread objects"""
        tweet_dict = {tweet.id: tweet for tweet in tweets}
        threads = []
        processed_ids = set()
        
        for tweet in tweets:
            if tweet.id in processed_ids:
                continue
                
            # If this is not a reply, it could be the start of a thread
            if not tweet.is_reply:
                thread_tweets = [tweet]
                processed_ids.add(tweet.id)
                
                # Find all replies to this tweet
                for other_tweet in tweets:
                    if (other_tweet.reply_to_tweet_id == tweet.id and 
                        other_tweet.username == tweet.username):
                        thread_tweets.append(other_tweet)
                        processed_ids.add(other_tweet.id)
                
                # Create a combined thread tweet if there are replies
                if len(thread_tweets) > 1:
                    # Sort by creation time
                    thread_tweets.sort(key=lambda t: t.created_at)
                    
                    # Combine text with thread markers
                    combined_text = thread_tweets[0].text
                    for i, reply in enumerate(thread_tweets[1:], 2):
                        combined_text += f"\n\n[Thread {i}/{len(thread_tweets)}] {reply.text}"
                    
                    # Create combined tweet object
                    thread_tweet = Tweet(
                        id=thread_tweets[0].id,
                        text=combined_text,
                        created_at=thread_tweets[0].created_at,
                        username=thread_tweets[0].username,
                        url=thread_tweets[0].url,
                        is_reply=False,
                        reply_to_tweet_id=None
                    )
                    threads.append(thread_tweet)
                else:
                    threads.append(tweet)
            
            # Handle orphaned replies (replies where we don't have the original tweet)
            elif tweet.is_reply and tweet.id not in processed_ids:
                threads.append(tweet)
                processed_ids.add(tweet.id)
        
        return threads

    def group_tweets_by_company(self, tweets: List[Tweet]) -> Dict[str, List[Tweet]]:
        """Group tweets by company"""
        company_tweets = {}
        for tweet in tweets:
            company = self.account_to_company.get(tweet.username, tweet.username)
            if company not in company_tweets:
                company_tweets[company] = []
            company_tweets[company].append(tweet)
        return company_tweets

    def analyze_tweets_with_gemini(self, tweets: List[Tweet]) -> str:
        """Analyze tweets and return grouped Slack-friendly text (short headlines)."""
        if not tweets:
            return "Nothing important today"

        # Group tweets (keep mapping for linking)
        threaded = self.group_tweets_into_threads(tweets)
        company_tweets = self.group_tweets_by_company(threaded)

        def normalize_headline(s: str) -> str:
            import re
            s = s.lower().strip()
            s = re.sub(r"[\s\-–—]+", " ", s)
            s = re.sub(r"[^a-z0-9 ]", "", s)
            return s

        def dedupe_items(items):
            seen = set()
            unique = []
            for it in items:
                key = normalize_headline(it.get('headline', ''))
                if key and key not in seen:
                    seen.add(key)
                    unique.append(it)
            return unique

        # Category ordering and emojis
        category_map = [
            ('fund_raise', '💰 Fund Raise'),
            ('partnerships', '🤝 Partnerships'),
            ('product', '🚀 Product'),
            ('customer_success', '🎯 Customer Success'),
            ('hiring', '👥 Hiring'),
            ('go_to_market', '📈 Go-to-Market'),
            ('other', '📰 Other')
        ]

        all_sections = []

        for company, company_list in company_tweets.items():
            if not company_list:
                continue

            # Prepare text with TWEET_ID_i markers per company
            tweets_text = "\n\n".join([
                f"TWEET_ID_{i}: @{t.username} ({t.created_at})\n{t.text}\nURL: {t.url}"
                for i, t in enumerate(company_list)
            ])

            # JSON prompt for grouped, short headlines with critical flag and strict filters
            prompt = f"""
            You are a competitive intelligence analyst. From the tweets below by {company}, extract only SHORT HEADLINES (3–8 words, no trailing period) that indicate real competitive intelligence.

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

            Return VALID JSON ONLY with this structure (no markdown):
            {{
              "fund_raise": [{{"headline": "...", "tweet_id": "TWEET_ID_X", "critical": true}}],
              "partnerships": [{{"headline": "...", "tweet_id": "TWEET_ID_X", "critical": true}}],
              "product": [{{"headline": "...", "tweet_id": "TWEET_ID_X", "critical": true}}],
              "customer_success": [{{"headline": "...", "tweet_id": "TWEET_ID_X", "critical": true}}],
              "hiring": [{{"headline": "...", "tweet_id": "TWEET_ID_X", "critical": true}}],
              "go_to_market": [{{"headline": "...", "tweet_id": "TWEET_ID_X", "critical": true}}],
              "other": [{{"headline": "...", "tweet_id": "TWEET_ID_X", "critical": true}}]
            }}

            The "critical" flag should be set to true for items that are particularly high-impact (e.g., funding/acquisition, major revenue, marquee partnerships, landmark product launches). Omit the field when not applicable.

            Tweets to analyze:
            {tweets_text}
            """

            try:
                resp = self.model.generate_content(prompt)
                result_text = (resp.text or '').strip()
                # Strip accidental code fences
                if result_text.startswith('```'):
                    result_text = result_text.strip('`\n')
                import json as _json
                parsed = _json.loads(result_text) if result_text else {}

                # Build mapping from TWEET_ID_i to URLs
                url_map = {}
                for i, t in enumerate(company_list):
                    url_map[f"TWEET_ID_{i}"] = t.url

                # Dedupe and format per category
                sections = []
                for key, title in category_map:
                    items = parsed.get(key) or []
                    if not items:
                        continue
                    items = dedupe_items(items)

                    # Company header (quoted block)
                    # Link company name to first item's URL if available
                    first_url = url_map.get(items[0].get('tweet_id', ''), company_list[0].url if company_list else '')
                    company_header = f"> <{first_url}|{company}>"

                    lines = [company_header]
                    for it in items:
                        url = url_map.get(it.get('tweet_id', ''), first_url)
                        headline = it.get('headline', '').strip().rstrip('.')
                        if not headline:
                            continue
                        prefix = "🚨 " if it.get('critical') else ""
                        lines.append(f"> • {prefix}<{url}|{headline}>")

                    if len(lines) > 1:
                        # Add category title once before first company block of that category
                        if not any(s.startswith(f"*{title}*") for s in sections):
                            sections.append(f"*{title}*")
                        sections.append("\n".join(lines))

                if sections:
                    all_sections.append("\n".join(sections))

            except Exception as e:
                print(f"Error analyzing tweets for {company}: {e}")
                continue

        if not all_sections:
            return "Nothing important today"

        return "\n\n".join(all_sections)
    
    def replace_tweet_ids_with_urls(self, headlines_text: str, tweets: List[Tweet]) -> str:
        """Replace TWEET_ID_X placeholders with hyperlinked company names like LinkedIn format"""
        if not headlines_text:
            return ""
        if not tweets:
            return headlines_text  # Return text as-is if no tweets (preserves non-TWEET_ID content)
        
        import re
        result = headlines_text
        
        # Replace each TWEET_ID_X with hyperlinked company name
        for i, tweet in enumerate(tweets):
            tweet_id_placeholder = f"TWEET_ID_{i}"
            
            # Find pattern: • Company: Description TWEET_ID_X
            # Use a more specific pattern that looks for the exact TWEET_ID_X at the end
            pattern = r'• ([^:]+): (.*?)' + re.escape(tweet_id_placeholder) + r'(?=\s*$|\s*\n|\s*\*)'
            
            def replace_match(match):
                company_name = match.group(1).strip()
                description = match.group(2).strip()
                # Create hyperlinked company name in Slack format
                hyperlinked_company = f"<{tweet.url}|{company_name}>"
                return f"• {hyperlinked_company}: {description}"
            
            result = re.sub(pattern, replace_match, result)
        
        # Fallback: If there are still entries without hyperlinks, add them based on company name
        # This handles cases where the AI didn't include TWEET_ID_X
        if tweets:
            # Create a mapping of company names to their tweet URLs
            company_url_map = {}
            for tweet in tweets:
                company = self.account_to_company.get(tweet.username, tweet.username)
                if company not in company_url_map:
                    company_url_map[company] = tweet.url
            
            # For each company, find and hyperlink entries that don't already have links
            for company, url in company_url_map.items():
                # Pattern to find lines that start with the company name but don't have hyperlinks
                fallback_pattern = r'^• ' + re.escape(company) + r': (.*)$'
                
                def fallback_replace(match):
                    description = match.group(1).strip()
                    # Use the company's tweet URL
                    hyperlinked_company = f"<{url}|{company}>"
                    return f"• {hyperlinked_company}: {description}"
                
                result = re.sub(fallback_pattern, fallback_replace, result, flags=re.MULTILINE)
        
        return result
    
    def send_slack_notification(self, message: str):
        """Send notification to Slack"""
        webhook_url = self.config.get('slack_webhook_url')
        if not webhook_url:
            print("Slack webhook URL not configured")
            return
        
        if message == "Nothing important today":
            return  # Don't send notification if nothing important
        
        payload = {
            "text": f"📰 Competitive Intelligence - {datetime.now().strftime('%Y-%m-%d')}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📰 Today's Competitive Intelligence Headlines*\n\n{message}"
                    }
                }
            ]
        }
        
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("Slack notification sent successfully")
        else:
            print(f"Failed to send Slack notification: {response.text}")
    
    def send_test_notification(self):
        """Send a test notification with sample competitive intelligence"""
        sample_analysis = """*Key Competitive Intelligence:*

• *Technology Development:* DecagonAI announced new voice synthesis capabilities with 95% accuracy in customer sentiment detection
• *Go-to-Market Strategy:* Targeting mid-market SaaS companies with $10M+ ARR, focusing on reducing support ticket volume by 40%
• *Customer Success:* Major enterprise client (Fortune 500 retailer) deployed their solution, handling 10K+ daily customer interactions
• *Product Launch:* Released multilingual support for Spanish and French markets, expanding international presence
• *Partnership:* Strategic integration with Salesforce Service Cloud announced

_Competitive Implications:_ Their focus on sentiment detection and enterprise clients suggests they're positioning as premium solution. Our voice AI should emphasize real-time response speed and SMB affordability as differentiators."""
        
        webhook_url = self.config.get('slack_webhook_url')
        if not webhook_url:
            print("Slack webhook URL not configured")
            return
        
        payload = {
            "text": f"🔍 Test - Daily Competitor Intelligence Update - {datetime.now().strftime('%Y-%m-%d')}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Test - Daily Twitter Analysis - {datetime.now().strftime('%Y-%m-%d')}*\n\n{sample_analysis}"
                    }
                }
            ]
        }
        
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("Test Slack notification sent successfully")
        else:
            print(f"Failed to send test Slack notification: {response.text}")
    
    def send_email_notification(self, message: str):
        """Send email notification as backup"""
        email_config = self.config.get('email', {})
        if not email_config.get('smtp_server'):
            print("Email configuration not found")
            return
        
        if message == "Nothing important today":
            return  # Don't send email if nothing important
        
        msg = MIMEMultipart()
        msg['From'] = email_config['from_email']
        msg['To'] = email_config['to_email']
        msg['Subject'] = f"Daily Competitor Intelligence - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
        Daily Twitter Analysis - {datetime.now().strftime('%Y-%m-%d')}
        
        {message}
        
        ---
        Automated monitoring of @DecagonAI and @SierraPlatform
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['from_email'], email_config['password'])
            text = msg.as_string()
            server.sendmail(email_config['from_email'], email_config['to_email'], text)
            server.quit()
            print("Email notification sent successfully")
        except Exception as e:
            print(f"Failed to send email: {e}")
    
    def load_accounts(self, accounts_file: str = "twitter_accounts.txt") -> List[str]:
        """Load Twitter accounts using rotation system for API limits"""
        from account_rotation import AccountRotator
        
        # Use rotator to get accounts for this run
        rotator = AccountRotator(accounts_file)
        account_tuples = rotator.get_accounts_for_this_run()
        
        # Extract accounts and build company mapping
        accounts = []
        self.account_to_company = {}
        
        for account, company in account_tuples:
            accounts.append(account)
            self.account_to_company[account] = company
        
        # Log rotation info
        rotation_info = rotator.get_rotation_info()
        print(f"🔄 {rotation_info}")
        print(f"📊 Monitoring accounts this run: {[f'@{acc}' for acc in accounts]}")
        
        return accounts
    
    def get_tracked_accounts_list(self) -> str:
        """Get formatted list of all tracked accounts"""
        try:
            with open("twitter_accounts.txt", 'r') as f:
                accounts = []
                for line in f.readlines():
                    line = line.strip()
                    if ':' in line:
                        account, company = line.split(':', 1)
                        accounts.append(f"@{account.strip()}")
                    elif line:
                        accounts.append(f"@{line.strip()}")
                return ", ".join(accounts)
        except FileNotFoundError:
            return "@DecagonAI, @SierraPlatform"
    
    def run_daily_analysis(self):
        """Main function to run the daily analysis"""
        import time
        print(f"Starting daily analysis - {datetime.now()}")
        
        all_tweets = []
        accounts = self.load_accounts()
        
        # Process accounts one by one (Free tier limit: 1 tweet fetch per 15min)
        for i, username in enumerate(accounts):
            # No delay needed since we're only processing 1 account per run
            
            tweets = self.fetch_twitter_data(username)
            all_tweets.extend(tweets)
            print(f"Fetched {len(tweets)} tweets from @{username}")
        
        # Analyze tweets
        analysis = self.analyze_tweets_with_gemini(all_tweets)
        print(f"Analysis result: {analysis[:100]}...")
        
        # Handle intelligence accumulation and notifications
        self.handle_intelligence_reporting(analysis, f"🔄 {accounts} accounts")
        
        print("Daily analysis completed")
        
    def handle_intelligence_reporting(self, analysis: str, run_info: str = ""):
        """Handle both immediate and daily accumulated intelligence reporting"""
        from daily_summary import DailyIntelligenceTracker
        
        tracker = DailyIntelligenceTracker()
        
        # Add to daily accumulation
        tracker.add_intelligence(analysis, run_info)
        
        # Send immediate notification for important news
        if analysis and analysis != "Nothing important today":
            # Send immediate Slack notification with rotation context
            self.send_immediate_slack_notification(analysis, run_info)
        
        # Check if it's time for daily summary
        if tracker.should_send_daily_summary():
            daily_summary = tracker.get_daily_summary()
            self.send_daily_summary_notification(daily_summary)
            
        # Cleanup old data weekly
        tracker.cleanup_old_data()
        
    def send_immediate_slack_notification(self, message: str, run_info: str = ""):
        """Send immediate Slack notification with clean format"""
        webhook_url = self.config.get('slack_webhook_url')
        if not webhook_url:
            print("Slack webhook URL not configured")
            return
        
        # Get list of accounts being tracked
        accounts_list = self.get_tracked_accounts_list()
        
        # Header: 📅 Sat, 8 Nov
        dt = datetime.now()
        formatted_date = dt.strftime('%a, %d %b').replace(', 0', ', ').replace(' 0', ' ')
        
        payload = {
            "text": f"📅 {formatted_date}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📅 {formatted_date}*\n\n{message}"
                    }
                }
            ]
        }
        
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("Immediate Slack notification sent successfully")
        else:
            print(f"Failed to send immediate Slack notification: {response.text}")
            
    def send_daily_summary_notification(self, summary: str):
        """Send end-of-day summary notification"""
        webhook_url = self.config.get('slack_webhook_url')
        if not webhook_url:
            print("Slack webhook URL not configured")
            return
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        accounts_list = self.get_tracked_accounts_list()
        
        payload = {
            "text": f"Daily Intelligence Summary - {current_date}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{current_date}*\n\n{summary}\n\n📊 Tracking: {accounts_list}"
                    }
                }
            ]
        }
        
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("Daily summary Slack notification sent successfully")
        else:
            print(f"Failed to send daily summary notification: {response.text}")


if __name__ == "__main__":
    monitor = TwitterMonitor()
    monitor.run_daily_analysis()
