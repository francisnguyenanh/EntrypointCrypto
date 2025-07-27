#!/usr/bin/env python3
"""
Test script để kiểm tra các functions trong app.py
"""

def test_function_definitions():
    """Test xem các functions quan trọng có được define không"""
    print("🧪 Testing function definitions...")
    
    try:
        # Import app module
        import app
        
        # Check required functions
        required_functions = [
            'print_results',
            'run_bot_continuously', 
            'startup_bot_with_error_handling',
            'monitor_active_orders',
            'system_error_handler',
            'handle_system_error',
            'cleanup_old_logs'
        ]
        
        print(f"📝 Checking {len(required_functions)} required functions:")
        
        all_good = True
        for func_name in required_functions:
            if hasattr(app, func_name):
                func = getattr(app, func_name)
                if callable(func):
                    print(f"  ✅ {func_name}: OK")
                else:
                    print(f"  ❌ {func_name}: Not callable")
                    all_good = False
            else:
                print(f"  ❌ {func_name}: Not found")
                all_good = False
        
        if all_good:
            print("\n🎉 All required functions found and callable!")
            return True
        else:
            print("\n🚨 Some functions are missing or not callable")
            return False
            
    except ImportError as e:
        print(f"🚨 Import error: {e}")
        return False
    except Exception as e:
        print(f"🚨 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_globals_check():
    """Test globals() function check"""
    print("\n🔍 Testing globals() function check...")
    
    # Simulate the check that's in run_bot_continuously
    def test_print_results():
        print("This is a test print_results function")
    
    # Add to globals
    globals()['test_print_results'] = test_print_results
    
    # Test check
    if 'test_print_results' in globals():
        print("✅ globals() check works correctly")
        globals()['test_print_results']()
    else:
        print("❌ globals() check failed")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 FUNCTION DEFINITION TEST")
    print("=" * 60)
    
    success = test_function_definitions()
    test_globals_check()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - Functions should work correctly")
    else:
        print("❌ SOME TESTS FAILED - Check function definitions")
    print("=" * 60)
