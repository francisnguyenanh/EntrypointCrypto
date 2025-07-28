#!/usr/bin/env python3
"""
Local testing script cho Lambda function
Simulate Lambda environment locally
"""

import json
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_lambda_locally():
    """Test Lambda function locally"""
    print("🧪 Testing Lambda function locally...")
    print("=" * 50)
    
    try:
        # Import Lambda handler
        from lambda_handler import lambda_handler
        
        # Test events
        test_events = [
            {
                "name": "Get Account Info",
                "event": {"action": "get_account_info"}
            },
            {
                "name": "Scheduled Trading",
                "event": {"action": "scheduled_trading"}
            },
            {
                "name": "Analyze Market",
                "event": {"action": "analyze_and_trade"}
            },
            {
                "name": "Monitor Orders",
                "event": {"action": "monitor_orders"}
            }
        ]
        
        # Mock context
        class MockContext:
            function_name = "crypto-trading-bot-test"
            function_version = "$LATEST"
            invoked_function_arn = "arn:aws:lambda:test"
            memory_limit_in_mb = 512
            remaining_time_in_millis = 270000  # 4.5 minutes
            aws_request_id = "test-request-id"
            
            def get_remaining_time_in_millis(self):
                return self.remaining_time_in_millis
        
        context = MockContext()
        
        # Test each event
        for test_case in test_events:
            print(f"\n🔄 Testing: {test_case['name']}")
            print("-" * 30)
            
            try:
                # Call Lambda handler
                response = lambda_handler(test_case['event'], context)
                
                print(f"✅ Status: {response.get('statusCode', 200)}")
                
                # Parse response body
                if 'body' in response:
                    body = json.loads(response['body']) if isinstance(response['body'], str) else response['body']
                    print(f"📊 Response: {json.dumps(body, indent=2)[:200]}...")
                else:
                    print(f"📊 Response: {json.dumps(response, indent=2)[:200]}...")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 50)
        print("✨ Local testing completed!")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

def test_individual_components():
    """Test individual components"""
    print("\n🔬 Testing individual components...")
    print("=" * 50)
    
    try:
        # Test DynamoDB
        print("\n📊 Testing DynamoDB...")
        from lambda_dynamodb import DynamoDBManager
        db = DynamoDBManager()
        print("✅ DynamoDB manager created")
        
        # Test Notifications
        print("\n📧 Testing Notifications...")
        from lambda_notifications import LambdaNotificationManager
        notifications = LambdaNotificationManager()
        print("✅ Notification manager created")
        
        # Test Trading Core
        print("\n📈 Testing Trading Core...")
        from lambda_trading_core import LambdaTradingBot
        bot = LambdaTradingBot()
        print("✅ Trading bot created")
        
    except Exception as e:
        print(f"❌ Component test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Lambda Local Testing Tool")
    print(f"🕐 Started at: {datetime.now().isoformat()}")
    
    # Test components first
    test_individual_components()
    
    # Then test full Lambda function
    test_lambda_locally()
    
    print(f"\n🏁 Completed at: {datetime.now().isoformat()}")
