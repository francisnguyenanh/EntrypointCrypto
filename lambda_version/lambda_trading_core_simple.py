"""
AWS Lambda Trading Core - Simple wrapper for the complete trading bot
This maintains backward compatibility while using the full implementation
"""

import json
import logging
import sys
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def emergency_debug_response():
    """Emergency debug function to check layer mounting and imports"""
    debug_info = {
        'python_version': sys.version,
        'python_executable': sys.executable,
        'python_paths': sys.path[:10]  # Limit paths shown
    }
    
    # Check if layers are mounted
    layer_info = {
        'opt_python_exists': os.path.exists('/opt/python'),
        'opt_python_files': []
    }
    
    if layer_info['opt_python_exists']:
        try:
            layer_info['opt_python_files'] = os.listdir('/opt/python')[:10]
        except:
            layer_info['opt_python_files'] = ['Error reading directory']
    
    # Check site-packages directory
    site_packages_path = '/opt/python/lib/python3.9/site-packages'
    layer_info['site_packages_exists'] = os.path.exists(site_packages_path)
    if layer_info['site_packages_exists']:
        try:
            site_packages_files = os.listdir(site_packages_path)
            layer_info['site_packages_count'] = len(site_packages_files)
            layer_info['site_packages_files'] = [f for f in site_packages_files if 'ccxt' in f.lower()][:5]
        except:
            layer_info['site_packages_files'] = ['Error reading site-packages']
    
    # Test imports
    import_results = {}
    
    # Test CCXT
    try:
        import ccxt
        import_results['ccxt'] = {
            'status': '✅ SUCCESS',
            'version': ccxt.__version__,
            'exchanges_count': len(ccxt.exchanges)
        }
    except Exception as e:
        import_results['ccxt'] = {
            'status': '❌ FAILED',
            'error': str(e)
        }
    
    # Test pandas/numpy
    try:
        import pandas as pd
        import numpy as np
        import_results['data_analysis'] = {
            'status': '✅ SUCCESS',
            'pandas_version': pd.__version__,
            'numpy_version': np.__version__
        }
    except Exception as e:
        import_results['data_analysis'] = {
            'status': '❌ FAILED',
            'error': str(e)
        }
    
    # Test technical analysis
    try:
        from ta.trend import SMAIndicator
        import_results['technical_analysis'] = {
            'status': '✅ SUCCESS',
            'ta_available': True
        }
    except Exception as e:
        import_results['technical_analysis'] = {
            'status': '❌ FAILED',
            'error': str(e)
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'timestamp': datetime.now().isoformat(),
            'debug_info': debug_info,
            'layer_info': layer_info,
            'import_results': import_results
        }, indent=2)
    }

def lambda_handler(event, context):
    """Lambda handler that supports both debug mode and full trading"""
    try:
        logger.info(f"🚀 Lambda execution started. Request ID: {context.aws_request_id}")
        
        # Emergency debug mode
        if event.get('emergency_debug'):
            return emergency_debug_response()
        
        # Try to import and use the complete trading bot
        try:
            from lambda_trading_bot import lambda_handler as full_lambda_handler
            logger.info("✅ Using complete trading bot implementation")
            return full_lambda_handler(event, context)
            
        except ImportError as e:
            # Fallback to basic functionality if full bot is not available
            logger.warning(f"⚠️ Complete trading bot not available: {e}")
            
            # Basic test of imports
            try:
                import ccxt
                import pandas as pd
                import numpy as np
                
                # Test CCXT functionality
                binance = ccxt.binance()
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': '✅ Basic imports successful - Trading bot ready!',
                        'ccxt_version': ccxt.__version__,
                        'pandas_version': pd.__version__,
                        'numpy_version': np.__version__,
                        'available_exchanges': len(ccxt.exchanges),
                        'test_exchange': 'binance',
                        'status': 'basic_mode',
                        'next_step': 'Deploy lambda_trading_bot.py for full functionality'
                    })
                }
                
            except Exception as basic_error:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': 'Basic import test failed',
                        'details': str(basic_error),
                        'suggestion': 'Check CCXT layer installation'
                    })
                }
        
    except Exception as e:
        logger.error(f"❌ Lambda execution failed: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Lambda execution failed',
                'details': str(e),
                'request_id': context.aws_request_id,
                'timestamp': datetime.now().isoformat()
            })
        }
