"""
AWS Lambda Handler cho Crypto Trading Bot
- Serverless version của trading bot
- Tối ưu cho thời gian thực thi ngắn
- Sử dụng DynamoDB thay vì file local
"""

import json
import os
import boto3
import logging
from datetime import datetime, timedelta
import time

# Import trading modules
from lambda_trading_core import LambdaTradingBot
from lambda_config import LAMBDA_CONFIG, BINANCE_CONFIG
from lambda_dynamodb import DynamoDBManager

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main Lambda handler function
    
    Event types:
    - scheduled: Định kỳ chạy trading analysis
    - manual: Chạy manual từ API Gateway
    - monitor: Kiểm tra orders
    """
    
    try:
        # Parse event
        event_type = event.get('source', 'manual')
        action = event.get('action', 'analyze_and_trade')
        
        logger.info(f"Lambda triggered - Type: {event_type}, Action: {action}")
        
        # Initialize trading bot
        bot = LambdaTradingBot()
        
        # Route to appropriate function
        if action == 'analyze_and_trade':
            result = handle_trading_analysis(bot, event)
        elif action == 'monitor_orders':
            result = handle_order_monitoring(bot, event)
        elif action == 'get_account_info':
            result = handle_account_info(bot, event)
        elif action == 'emergency_stop':
            result = handle_emergency_stop(bot, event)
        else:
            result = {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown action: {action}'})
            }
        
        logger.info(f"Lambda execution completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

def handle_trading_analysis(bot, event):
    """Xử lý phân tích và trading"""
    try:
        # Kiểm tra emergency stop
        if bot.check_emergency_stop():
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Trading stopped - Emergency stop activated',
                    'timestamp': datetime.now().isoformat()
                })
            }
        
        # Lấy thông tin tài khoản
        account_info = bot.get_account_info()
        if not account_info:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Cannot get account info'})
            }
        
        # Phân tích thị trường
        analysis_result = bot.analyze_market()
        
        if not analysis_result.get('recommendations'):
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No trading opportunities found',
                    'analysis': analysis_result,
                    'timestamp': datetime.now().isoformat()
                })
            }
        
        # Thực hiện trading
        trading_result = bot.execute_trading(analysis_result['recommendations'])
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Trading analysis completed',
                'account_info': account_info,
                'analysis': analysis_result,
                'trading_result': trading_result,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Trading analysis failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_order_monitoring(bot, event):
    """Xử lý monitoring orders"""
    try:
        monitoring_result = bot.monitor_orders()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Order monitoring completed',
                'result': monitoring_result,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Order monitoring failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_account_info(bot, event):
    """Lấy thông tin tài khoản"""
    try:
        account_info = bot.get_account_info()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'account_info': account_info,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Get account info failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_emergency_stop(bot, event):
    """Kích hoạt emergency stop"""
    try:
        stop_result = bot.activate_emergency_stop()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Emergency stop activated',
                'result': stop_result,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Emergency stop failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
