#!/usr/bin/env python3
"""
GitHub-hosted Slack webhook handler for Twitter monitoring slash commands
Handles /intel command to provide on-demand competitive intelligence
"""

import json
import os
from typing import Dict, Any
from twitter_monitor import TwitterMonitor
from urllib.parse import parse_qs


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Slack slash commands
    Can be adapted for other serverless platforms
    """
    try:
        # Parse the incoming Slack request
        if event.get('httpMethod') == 'POST':
            body = event.get('body', '')
            if event.get('isBase64Encoded'):
                import base64
                body = base64.b64decode(body).decode('utf-8')
            
            # Parse form data from Slack
            parsed_data = parse_qs(body)
            
            # Extract Slack parameters
            command = parsed_data.get('command', [''])[0]
            user_name = parsed_data.get('user_name', [''])[0]
            channel_name = parsed_data.get('channel_name', [''])[0]
            
            # Verify it's the expected command
            if command != '/intel':
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'text': 'Unknown command. Use `/intel` to get latest competitive intelligence.'
                    })
                }
            
            # Initialize monitor with environment variables
            config = {
                'twitter_bearer_token': os.environ.get('TWITTER_BEARER_TOKEN'),
                'gemini_api_key': os.environ.get('GEMINI_API_KEY'),
                'slack_webhook_url': os.environ.get('SLACK_WEBHOOK_URL')
            }
            
            # Validate required environment variables
            missing_vars = [k for k, v in config.items() if not v]
            if missing_vars:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'text': f'Configuration error: Missing environment variables: {", ".join(missing_vars)}'
                    })
                }
            
            # Create monitor instance
            monitor = TwitterMonitor()
            monitor.config = config
            monitor.setup_gemini()
            
            # Load accounts (you may want to store this in environment or database)
            accounts = os.environ.get('TWITTER_ACCOUNTS', 'DecagonAI,SierraPlatform').split(',')
            
            # Fetch and analyze recent tweets
            all_tweets = []
            for username in accounts:
                tweets = monitor.fetch_twitter_data(username.strip())
                all_tweets.extend(tweets)
            
            # Analyze tweets
            analysis = monitor.analyze_tweets_with_gemini(all_tweets)
            
            # Format response for Slack
            if analysis == "Nothing important today":
                response_text = "📊 *Latest Competitive Intelligence*\n\nNo significant developments detected in the last 24 hours from monitored accounts."
            else:
                response_text = f"📊 *Latest Competitive Intelligence*\n\n{analysis}"
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'in_channel',  # Make response visible to channel
                    'text': response_text
                })
            }
        
        else:
            return {
                'statusCode': 405,
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'text': f'Error processing request: {str(e)}'
            })
        }


def flask_handler():
    """
    Flask handler for development/testing
    Run locally with: python slack_webhook_handler.py
    """
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    @app.route('/intel', methods=['POST'])
    def handle_intel_command():
        try:
            # Get form data from Slack
            command = request.form.get('command')
            user_name = request.form.get('user_name')
            channel_name = request.form.get('channel_name')
            
            # Verify command
            if command != '/intel':
                return jsonify({
                    'text': 'Unknown command. Use `/intel` to get latest competitive intelligence.'
                })
            
            # Load config from file (for local development)
            config_file = 'config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                # Fallback to environment variables
                config = {
                    'twitter_bearer_token': os.environ.get('TWITTER_BEARER_TOKEN'),
                    'gemini_api_key': os.environ.get('GEMINI_API_KEY'),
                    'slack_webhook_url': os.environ.get('SLACK_WEBHOOK_URL')
                }
            
            # Create monitor instance
            monitor = TwitterMonitor()
            monitor.config = config
            monitor.setup_gemini()
            
            # Load accounts
            accounts_file = 'accounts.txt'
            if os.path.exists(accounts_file):
                accounts = monitor.load_accounts(accounts_file)
            else:
                accounts = ['DecagonAI', 'SierraPlatform']
            
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
            })
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy'})
    
    return app


if __name__ == '__main__':
    # Run Flask app for local development
    app = flask_handler()
    app.run(host='0.0.0.0', port=3000, debug=True)