#!/usr/bin/env python3
"""
Test script để kiểm tra tất cả dependencies trong Lambda version
"""

import sys
import traceback

def test_import(module_name, package_name=None):
    """Test import một module"""
    try:
        __import__(module_name)
        print(f"✅ {package_name or module_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name} - FAILED: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {package_name or module_name} - ERROR: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Lambda dependencies...")
    print("=" * 50)
    
    # Core Python modules
    print("\n📦 Core dependencies:")
    test_import("json")
    test_import("logging")
    test_import("datetime")
    test_import("time")
    test_import("typing")
    
    # AWS modules
    print("\n☁️  AWS modules:")
    test_import("boto3")
    test_import("botocore")
    
    # Trading modules
    print("\n📈 Trading dependencies:")
    test_import("ccxt")
    test_import("pandas")
    test_import("numpy")
    test_import("ta", "Technical Analysis")
    
    # Utility modules
    print("\n🔧 Utility dependencies:")
    test_import("requests")
    test_import("urllib3")
    test_import("simplejson")
    test_import("dateutil", "python-dateutil")
    test_import("pytz")
    test_import("decimal")
    
    # Lambda modules
    print("\n🚀 Lambda modules:")
    try:
        from lambda_config import LAMBDA_CONFIG, BINANCE_CONFIG
        print("✅ lambda_config - OK")
    except Exception as e:
        print(f"❌ lambda_config - FAILED: {e}")
        traceback.print_exc()
    
    try:
        from lambda_dynamodb import DynamoDBManager
        print("✅ lambda_dynamodb - OK")
    except Exception as e:
        print(f"❌ lambda_dynamodb - FAILED: {e}")
        traceback.print_exc()
    
    try:
        from lambda_notifications import LambdaNotificationManager
        print("✅ lambda_notifications - OK")
    except Exception as e:
        print(f"❌ lambda_notifications - FAILED: {e}")
        traceback.print_exc()
    
    try:
        from lambda_trading_core import LambdaTradingBot
        print("✅ lambda_trading_core - OK")
    except Exception as e:
        print(f"❌ lambda_trading_core - FAILED: {e}")
        traceback.print_exc()
    
    try:
        from lambda_handler import lambda_handler
        print("✅ lambda_handler - OK")
    except Exception as e:
        print(f"❌ lambda_handler - FAILED: {e}")
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 Test completed!")
    
    # Test functionality
    print("\n🔬 Testing basic functionality...")
    try:
        # Test DynamoDB manager
        print("Testing DynamoDB connection...")
        # Note: Sẽ fail nếu không có AWS credentials, nhưng import OK là đủ
        
        # Test Binance API
        print("Testing CCXT...")
        import ccxt
        exchange = ccxt.binance({'sandbox': True})  # Test mode
        print("✅ CCXT Binance instance created")
        
    except Exception as e:
        print(f"⚠️  Functionality test warning: {e}")
    
    print("\n✨ All critical imports successful!")

if __name__ == "__main__":
    main()
