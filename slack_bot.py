#!/usr/bin/env python3
"""
Slack Bot for On-Demand Twitter Analysis
Provides slash command /intel for instant competitive intelligence updates
"""

import os
import json
from flask import Flask, request, jsonify
from twitter_monitor import TwitterMonitor
import threading

app = Flask(__name__)

@app.route('/intel', methods=['POST'])
def intel_command():
    """Handle /intel slash command from Slack"""
    # Verify the request is from Slack (optional but recommended)
    if request.form.get('token') != os.environ.get('SLACK_VERIFICATION_TOKEN'):
        return jsonify({'text': 'Invalid token'}), 403
    
    # Send immediate response to avoid timeout
    threading.Thread(target=run_analysis_async, args=(request.form.get('response_url'),)).start()
    
    return jsonify({
        'response_type': 'in_channel',
        'text': '🔍 Fetching latest competitive intelligence... This may take a moment.'
    })

def run_analysis_async(response_url):
    """Run analysis in background and send result to Slack"""
    import requests
    
    try:
        monitor = TwitterMonitor()
        
        # Run analysis
        all_tweets = []
        accounts = monitor.load_accounts()
        
        for username in accounts:
            tweets = monitor.fetch_twitter_data(username)
            all_tweets.extend(tweets)
        
        analysis = monitor.analyze_tweets_with_gemini(all_tweets)
        
        if analysis == "Nothing important today":
            message = "No significant competitive intelligence found in recent tweets."
        else:
            message = f"*Latest Competitive Intelligence Update*\n\n{analysis}"
        
        # Send follow-up message
        payload = {
            'response_type': 'in_channel',
            'text': message
        }
        
        requests.post(response_url, json=payload)
        
    except Exception as e:
        error_payload = {
            'response_type': 'in_channel',
            'text': f'❌ Error fetching intelligence: {str(e)}'
        }
        requests.post(response_url, json=error_payload)

if __name__ == '__main__':
    # For development - use ngrok for public URL
    app.run(debug=True, port=3000)