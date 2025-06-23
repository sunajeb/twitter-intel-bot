#!/usr/bin/env python3
"""
Vercel API endpoint for Slack slash commands
Handles /intel command to provide on-demand competitive intelligence
"""

import json
import os
import sys
from typing import Dict, Any
from urllib.parse import parse_qs

# Add parent directory to path to import twitter_monitor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from twitter_monitor import TwitterMonitor
except ImportError:
    # Fallback if import fails
    class TwitterMonitor:
        def __init__(self):
            self.config = {}
        
        def setup_gemini(self):
            pass
        
        def fetch_twitter_data(self, username):
            return []
        
        def analyze_tweets_with_gemini(self, tweets):
            return "Service temporarily unavailable"


def handler(request, response):
    """
    Vercel handler for Slack slash commands
    """
    try:
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            response.status = 200
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return ''

        if request.method != 'POST':
            response.status = 405
            return json.dumps({'error': 'Method not allowed'})

        # Parse form data from Slack
        content_type = request.headers.get('content-type', '')
        if 'application/x-www-form-urlencoded' in content_type:
            body = request.get_data(as_text=True)
            parsed_data = parse_qs(body)
        else:
            response.status = 400
            return json.dumps({'error': 'Invalid content type'})

        # Extract Slack parameters
        command = parsed_data.get('command', [''])[0]
        user_name = parsed_data.get('user_name', [''])[0]
        channel_name = parsed_data.get('channel_name', [''])[0]

        # Verify it's the expected command
        if command != '/intel':
            response.status = 200
            response.headers['Content-Type'] = 'application/json'
            return json.dumps({
                'text': 'Unknown command. Use `/intel` to get latest competitive intelligence.'
            })

        # Get configuration from environment variables
        config = {
            'twitter_bearer_token': os.environ.get('TWITTER_BEARER_TOKEN'),
            'gemini_api_key': os.environ.get('GEMINI_API_KEY'),
            'slack_webhook_url': os.environ.get('SLACK_WEBHOOK_URL')
        }

        # Validate required environment variables
        missing_vars = [k for k, v in config.items() if not v]
        if missing_vars:
            response.status = 200
            response.headers['Content-Type'] = 'application/json'
            return json.dumps({
                'text': f'Configuration error: Missing environment variables: {", ".join(missing_vars)}'
            })

        # Create monitor instance
        monitor = TwitterMonitor()
        monitor.config = config
        monitor.setup_gemini()

        # Load accounts from environment variable
        accounts_str = os.environ.get('TWITTER_ACCOUNTS', 'DecagonAI,SierraPlatform')
        accounts = [acc.strip() for acc in accounts_str.split(',') if acc.strip()]

        # Fetch and analyze recent tweets
        all_tweets = []
        for username in accounts:
            tweets = monitor.fetch_twitter_data(username)
            all_tweets.extend(tweets)

        # Analyze tweets
        analysis = monitor.analyze_tweets_with_gemini(all_tweets)

        # Format response for Slack
        if analysis == "Nothing important today" or analysis == "Service temporarily unavailable":
            if analysis == "Service temporarily unavailable":
                response_text = "⚠️ *Service Issue*\n\nThere was a temporary issue accessing the monitoring services. Please try again in a few minutes."
            else:
                response_text = "📊 *Latest Competitive Intelligence*\n\nNo significant developments detected in the last 24 hours from monitored accounts."
        else:
            response_text = f"📊 *Latest Competitive Intelligence*\n\n{analysis}"

        response.status = 200
        response.headers['Content-Type'] = 'application/json'
        return json.dumps({
            'response_type': 'in_channel',  # Make response visible to channel
            'text': response_text
        })

    except Exception as e:
        print(f"Error processing request: {e}")
        response.status = 500
        response.headers['Content-Type'] = 'application/json'
        return json.dumps({
            'text': f'Error processing request: {str(e)}'
        })


# Alternative function-based handler for newer Vercel runtime
def intel_handler(request):
    """
    Alternative handler format for Vercel
    """
    from flask import Flask, request as flask_request, jsonify
    
    app = Flask(__name__)
    
    with app.test_request_context(
        path='/api/intel',
        method=request.method,
        headers=dict(request.headers),
        data=request.body
    ):
        try:
            # Parse form data from Slack
            if flask_request.method != 'POST':
                return jsonify({'error': 'Method not allowed'}), 405

            command = flask_request.form.get('command')
            user_name = flask_request.form.get('user_name')
            channel_name = flask_request.form.get('channel_name')

            # Verify command
            if command != '/intel':
                return jsonify({
                    'text': 'Unknown command. Use `/intel` to get latest competitive intelligence.'
                })

            # Get configuration from environment variables
            config = {
                'twitter_bearer_token': os.environ.get('TWITTER_BEARER_TOKEN'),
                'gemini_api_key': os.environ.get('GEMINI_API_KEY'),
                'slack_webhook_url': os.environ.get('SLACK_WEBHOOK_URL')
            }

            # Validate required environment variables
            missing_vars = [k for k, v in config.items() if not v]
            if missing_vars:
                return jsonify({
                    'text': f'Configuration error: Missing environment variables: {", ".join(missing_vars)}'
                })

            # Create monitor instance
            monitor = TwitterMonitor()
            monitor.config = config
            monitor.setup_gemini()

            # Load accounts
            accounts_str = os.environ.get('TWITTER_ACCOUNTS', 'DecagonAI,SierraPlatform')
            accounts = [acc.strip() for acc in accounts_str.split(',') if acc.strip()]

            # Fetch and analyze tweets
            all_tweets = []
            for username in accounts:
                tweets = monitor.fetch_twitter_data(username)
                all_tweets.extend(tweets)

            analysis = monitor.analyze_tweets_with_gemini(all_tweets)

            # Format response
            if analysis == "Nothing important today":
                response_text = "📊 *Latest Competitive Intelligence*\n\nNo significant developments detected in the last 24 hours from monitored accounts."
            else:
                response_text = f"📊 *Latest Competitive Intelligence*\n\n{analysis}"

            return jsonify({
                'response_type': 'in_channel',
                'text': response_text
            })

        except Exception as e:
            print(f"Error processing request: {e}")
            return jsonify({
                'text': f'Error processing request: {str(e)}'
            }), 500


# Export for Vercel
def handler_wrapper(request):
    """Wrapper to handle both old and new Vercel formats"""
    return intel_handler(request)