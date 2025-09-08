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
        self.account_to_company = {}  # Will be loaded from accounts.txt
        
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
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def fetch_twitter_data(self, username: str) -> List[Tweet]:
        """Fetch recent tweets from a Twitter username using Twitter API v2 with caching"""
        from user_cache import UserIDCache
        
        bearer_token = self.config.get('twitter_bearer_token')
        if not bearer_token:
            print("Twitter Bearer Token not found in config")
            return []
        
        # Calculate last 24 hours for filtering
        from datetime import timezone, timedelta
        utc_now = datetime.now(timezone.utc)
        last_24h_start = (utc_now - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f"🕐 Fetching tweets from {username} since: {last_24h_start} (UTC) [Last 24 hours]")
        
        # Get user ID using cache (saves API calls!)
        cache = UserIDCache()
        user_id = cache.get_user_id(username, bearer_token)
        
        if not user_id:
            print(f"Could not get user ID for {username}")
            return []
        
        # Fetch recent tweets from last 24 hours
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        params = {
            'max_results': 10,  # Reduced from 20 to minimize data usage
            'start_time': last_24h_start,
            'tweet.fields': 'created_at,in_reply_to_user_id,referenced_tweets',  # Removed public_metrics to reduce payload
            'exclude': 'retweets'  # Include replies but exclude retweets
        }
        
        response = requests.get(tweets_url, headers=headers, params=params)
        if response.status_code == 429:
            print(f"⚠️ Rate limit hit for @{username} tweet fetch - skipping this account for now")
            return []
        elif response.status_code != 200:
            print(f"Error fetching tweets for {username}: {response.text}")
            return []
        
        tweets_data = response.json().get('data', [])
        tweets = []
        
        for tweet_data in tweets_data:
            # Check if this is a reply
            is_reply = 'in_reply_to_user_id' in tweet_data
            reply_to_tweet_id = None
            
            # Get the original tweet ID if this is a reply
            if 'referenced_tweets' in tweet_data:
                for ref in tweet_data['referenced_tweets']:
                    if ref['type'] == 'replied_to':
                        reply_to_tweet_id = ref['id']
                        break
            
            tweet = Tweet(
                id=tweet_data['id'],
                text=tweet_data['text'],
                created_at=tweet_data['created_at'],
                username=username,
                url=f"https://twitter.com/{username}/status/{tweet_data['id']}",
                is_reply=is_reply,
                reply_to_tweet_id=reply_to_tweet_id
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
        """Analyze tweets using Gemini 2.5 Flash for headline generation"""
        if not tweets:
            return "Nothing important today"
        
        # First, group tweets into threads to capture complete context
        threaded_tweets = self.group_tweets_into_threads(tweets)
        
        # Then group by company for analysis
        company_tweets = self.group_tweets_by_company(threaded_tweets)
        
        headlines = []
        
        for company, company_tweet_list in company_tweets.items():
            if not company_tweet_list:
                continue
                
            tweets_text = "\n\n".join([
                f"TWEET_ID_{i}: @{tweet.username} ({tweet.created_at}):\n{tweet.text}\nURL: {tweet.url}"
                for i, tweet in enumerate(company_tweet_list)
            ])
            
            prompt = f"""
            You are a competitive intelligence analyst. Analyze the following tweets from {company} and create concise headlines for any significant business developments posted TODAY.

            ONLY generate headlines for tweets that contain:
            1. Funding announcements or business milestones
            2. Product launches or major feature releases  
            3. Significant partnership announcements
            4. Major customer wins or case studies
            5. Technology breakthroughs or innovations
            6. Key executive hires or team changes
            7. Market expansion or new business lines

            IGNORE:
            - General marketing content
            - Routine product updates
            - Generic industry commentary
            - Personal opinions or thoughts
            - Event announcements (unless major partnership/product launch)

            Organize your output into these categories with appropriate emojis:
            💰 Fund Raise
            👥 Hiring  
            🎯 Customer Success
            🚀 Product
            📈 Go-to-Market
            📰 Other

            For each category that has relevant information, use this format:
            *💰 Fund Raise*
            • Company: Headline description TWEET_ID_X

            *👥 Hiring*
            • Company: Headline description TWEET_ID_X

            Example output:
            *💰 Fund Raise*
            • Decagon: Raises $131M Series C funding round TWEET_ID_0

            *🚀 Product*  
            • Sierra: Launches new voice AI platform for enterprise customers TWEET_ID_1

            IMPORTANT: 
            - Only include categories that have actual information
            - Use the TWEET_ID_X that corresponds to the specific tweet you analyzed for each headline
            - If no tweets contain significant business developments, respond with exactly "Nothing significant today"

            Today's tweets from {company}:
            {tweets_text}
            """
            
            try:
                response = self.model.generate_content(prompt)
                result = response.text.strip()
                
                if result and result != "Nothing significant today":
                    # Process the result to replace TWEET_IDs with actual URLs
                    formatted_headlines = self.replace_tweet_ids_with_urls(result, company_tweet_list)
                    if formatted_headlines:
                        headlines.append(formatted_headlines)
                    
            except Exception as e:
                print(f"Error analyzing tweets for {company}: {e}")
                continue
        
        if not headlines:
            return "Nothing important today"
        
        # Combine all headlines
        return "\n".join(headlines)
    
    def replace_tweet_ids_with_urls(self, headlines_text: str, tweets: List[Tweet]) -> str:
        """Replace TWEET_ID_X placeholders with actual clickable Slack links"""
        if not headlines_text or not tweets:
            return ""
        
        result = headlines_text
        
        # Replace each TWEET_ID_X with the corresponding tweet URL
        for i, tweet in enumerate(tweets):
            tweet_id_placeholder = f"TWEET_ID_{i}"
            slack_link = f"<{tweet.url}|🔗>"
            result = result.replace(tweet_id_placeholder, slack_link)
        
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
    
    def load_accounts(self, accounts_file: str = "accounts.txt") -> List[str]:
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
            with open("accounts.txt", 'r') as f:
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
        
        formatted_date = datetime.now().strftime('%d %b')  # 08 Sep format
        
        payload = {
            "text": f"Twitter Update: {formatted_date}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Twitter Update: {formatted_date}*\n\n{message}"
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