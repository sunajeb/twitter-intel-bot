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


class TwitterMonitor:
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.setup_gemini()
        
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
        """Fetch recent tweets from a Twitter username using Twitter API v2"""
        bearer_token = self.config.get('twitter_bearer_token')
        if not bearer_token:
            print("Twitter Bearer Token not found in config")
            return []
        
        # Calculate yesterday's date for filtering
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        url = f"https://api.twitter.com/2/users/by/username/{username}"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        
        # Get user ID first
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching user ID for {username}: {response.text}")
            return []
        
        user_id = response.json()['data']['id']
        
        # Fetch recent tweets
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {
            'max_results': 10,
            'start_time': yesterday,
            'tweet.fields': 'created_at,public_metrics',
            'exclude': 'retweets'
        }
        
        response = requests.get(tweets_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching tweets for {username}: {response.text}")
            return []
        
        tweets_data = response.json().get('data', [])
        tweets = []
        
        for tweet_data in tweets_data:
            tweet = Tweet(
                id=tweet_data['id'],
                text=tweet_data['text'],
                created_at=tweet_data['created_at'],
                username=username,
                url=f"https://twitter.com/{username}/status/{tweet_data['id']}"
            )
            tweets.append(tweet)
        
        return tweets
    
    def analyze_tweets_with_gemini(self, tweets: List[Tweet]) -> str:
        """Analyze tweets using Gemini 2.5 Flash"""
        if not tweets:
            return "Nothing important today"
        
        tweets_text = "\n\n".join([
            f"@{tweet.username} ({tweet.created_at}):\n{tweet.text}\nURL: {tweet.url}"
            for tweet in tweets
        ])
        
        prompt = f"""
        Analyze the following tweets from @DecagonAI and @SierraPlatform from the perspective of a voice AI customer support company competitor. 

        Focus on identifying important information about:
        1. Technology developments and innovations
        2. Go-to-market strategies and customer acquisition 
        3. Customer success stories, case studies, or testimonials
        4. Funding announcements or business milestones
        5. Product launches or feature releases
        6. Partnership announcements
        7. Team growth or key hires
        8. Market positioning or competitive messaging

        If there is no important competitive intelligence in these tweets, respond with exactly "Nothing important today".

        If there is important information, provide a concise analysis highlighting the key insights and their potential competitive implications.

        Format your response using Slack markdown syntax:
        - Use *text* for bold
        - Use _text_ for italics  
        - Use bullet points with • or -
        - Use numbered lists
        - Keep formatting simple and readable

        Tweets to analyze:
        {tweets_text}
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error analyzing tweets with Gemini: {e}")
            return "Error analyzing tweets"
    
    def send_slack_notification(self, message: str):
        """Send notification to Slack"""
        webhook_url = self.config.get('slack_webhook_url')
        if not webhook_url:
            print("Slack webhook URL not configured")
            return
        
        if message == "Nothing important today":
            return  # Don't send notification if nothing important
        
        payload = {
            "text": f"🔍 Daily Competitor Intelligence Update - {datetime.now().strftime('%Y-%m-%d')}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Daily Twitter Analysis - {datetime.now().strftime('%Y-%m-%d')}*\n\n{message}"
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
        """Load Twitter accounts from file"""
        try:
            with open(accounts_file, 'r') as f:
                accounts = [line.strip() for line in f.readlines() if line.strip()]
                return accounts
        except FileNotFoundError:
            print(f"Accounts file {accounts_file} not found. Using default accounts.")
            return ['DecagonAI', 'SierraPlatform']
    
    def run_daily_analysis(self):
        """Main function to run the daily analysis"""
        print(f"Starting daily analysis - {datetime.now()}")
        
        all_tweets = []
        accounts = self.load_accounts()
        
        # Fetch tweets from all accounts
        for username in accounts:
            tweets = self.fetch_twitter_data(username)
            all_tweets.extend(tweets)
            print(f"Fetched {len(tweets)} tweets from @{username}")
        
        # Analyze tweets
        analysis = self.analyze_tweets_with_gemini(all_tweets)
        print(f"Analysis result: {analysis[:100]}...")
        
        # Send notifications
        self.send_slack_notification(analysis)
        
        print("Daily analysis completed")


if __name__ == "__main__":
    monitor = TwitterMonitor()
    monitor.run_daily_analysis()