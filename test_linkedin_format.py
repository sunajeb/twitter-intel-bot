#!/usr/bin/env python3
"""
Test script to verify LinkedIn formatting works correctly
"""

from linkedin_monitor import LinkedInMonitor
import json

def test_formatting():
    """Test the formatting with various scenarios"""
    monitor = LinkedInMonitor()
    
    # Test Case 1: All categories populated
    print("Test Case 1: Full analysis with all categories")
    print("=" * 60)
    
    analysis1 = {
        "fund_raise": [
            {
                "company": "DRUID AI",
                "description": "Raised $31M in Series C funding led by Cipio Partners",
                "url": "https://www.linkedin.com/feed/update/urn:li:activity:7373801227446484992/"
            }
        ],
        "hiring": [
            {
                "company": "SynthflowAI",
                "description": "Welcomed Jens Gifhorn as VP Finance and Alex S. as Principal Software Engineer",
                "url": "https://www.linkedin.com/feed/update/urn:li:activity:7373685127568060416/"
            },
            {
                "company": "11x AI",
                "description": "New hire leading their Outbound AI Agent, Alice",
                "url": "https://www.linkedin.com/feed/update/urn:li:activity:7373716076313919489/"
            }
        ],
        "product": [
            {
                "company": "Regal AI",
                "description": "Expanded Simulations feature with automated Evaluations for AI agent QA",
                "url": "https://www.linkedin.com/feed/update/urn:li:activity:7373732422401617920/"
            }
        ],
        "customer_success": [],
        "partnerships": [],
        "other": []
    }
    
    message1 = monitor.format_for_slack(analysis1, "2025-09-17")
    print(message1)
    print("\n")
    
    # Test Case 2: Mixed categories with special characters
    print("Test Case 2: Special characters and formatting")
    print("=" * 60)
    
    analysis2 = {
        "fund_raise": [],
        "hiring": [],
        "customer_success": [
            {
                "company": "DRUID AI",
                "description": "Utility provider uses DRUID's Agent IOANA to reduce onboarding to 10 minutes",
                "url": "https://www.linkedin.com/feed/update/urn:li:activity:7374336401246584833/"
            },
            {
                "company": "Decagon AI",
                "description": "Whop achieves 70% ticket deflection & 50% fewer payment tickets",
                "url": "https://www.linkedin.com/feed/update/urn:li:activity:7374474121084194816/"
            }
        ],
        "product": [
            {
                "company": "Bland AI",
                "description": "Introduced Live Translate: AI speaks any language in real-time",
                "url": "https://www.linkedin.com/feed/update/urn:li:activity:7374513168133517312/"
            },
            {
                "company": "Sierra",
                "description": "Sierra's Agent Studio allows building customer-facing agents without code",
                "url": "https://www.linkedin.com/feed/update/urn:li:activity:7374513168133517313/"
            }
        ],
        "partnerships": [],
        "other": []
    }
    
    message2 = monitor.format_for_slack(analysis2, "2025-09-18")
    print(message2)
    print("\n")
    
    # Test Case 3: Empty analysis
    print("Test Case 3: No updates")
    print("=" * 60)
    
    analysis3 = {}
    message3 = monitor.format_for_slack(analysis3, "2025-09-19")
    print(message3)
    print("\n")
    
    # Test Case 4: Verify no ### headers or formatting issues
    print("Verification:")
    print("=" * 60)
    
    all_messages = [message1, message2, message3]
    issues_found = False
    
    for i, msg in enumerate(all_messages):
        print(f"\nChecking message {i+1}:")
        if "###" in msg:
            print("❌ Found ### headers")
            issues_found = True
        else:
            print("✅ No ### headers")
        
        if "linkedin_post_url" in msg or "source_url" in msg:
            print("❌ Found raw URL references")
            issues_found = True
        else:
            print("✅ No raw URL references")
        
        # Count hyperlinks
        hyperlink_count = msg.count("<https://")
        print(f"✅ Found {hyperlink_count} properly formatted hyperlinks")
    
    if not issues_found:
        print("\n✅ All formatting tests passed!")
    else:
        print("\n❌ Some formatting issues detected")

def test_gemini_parsing():
    """Test Gemini response parsing"""
    print("\n\nTest Gemini JSON Parsing")
    print("=" * 60)
    
    monitor = LinkedInMonitor()
    
    # Simulate different Gemini response formats
    test_responses = [
        # Clean JSON
        '''{"fund_raise": [{"company": "Test", "description": "Test", "url": "https://test.com"}]}''',
        
        # JSON with markdown
        '''```json
{"fund_raise": [{"company": "Test", "description": "Test", "url": "https://test.com"}]}
```''',
        
        # JSON with extra whitespace
        '''
        
        {"fund_raise": [{"company": "Test", "description": "Test", "url": "https://test.com"}]}
        
        '''
    ]
    
    for i, response in enumerate(test_responses):
        print(f"\nTest response {i+1}:")
        try:
            # Simulate the cleaning logic
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            
            parsed = json.loads(cleaned.strip())
            print("✅ Successfully parsed JSON")
            print(f"   Result: {parsed}")
        except Exception as e:
            print(f"❌ Failed to parse: {e}")

if __name__ == "__main__":
    test_formatting()
    test_gemini_parsing()