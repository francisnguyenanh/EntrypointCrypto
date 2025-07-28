"""
Lambda Configuration - Tối ưu cho AWS Lambda environment
"""

import os

# =============================================================================
# BINANCE API CONFIGURATION
# =============================================================================
BINANCE_CONFIG = {
    'apiKey': os.environ.get('BINANCE_API_KEY', 'Jsk0G44imJ2iuOukTdWgh2AcsDinHmvsZQ4TaQtT5f1DS2euFqpdaShYfAfZSnRa'),
    'secret': os.environ.get('BINANCE_SECRET', 'aVPzEXAwpqiMTY7EZa2BeCTSGnh8aSJcrRkJns0PhUr2KZRNDXvG5QDWSTAQ7q3a'),
    'sandbox': os.environ.get('BINANCE_SANDBOX', 'False').lower() == 'true',  # Set via environment
    'enableRateLimit': True,
    'timeout': 15000,  # Giảm timeout cho Lambda
    'options': {
        'defaultType': 'spot',
        'recvWindow': 30000,  # Giảm recvWindow
    }
}

# =============================================================================
# LAMBDA TRADING CONFIGURATION
# =============================================================================
LAMBDA_CONFIG = {
    # Trading settings tối ưu cho Lambda
    'enabled': True,
    'max_execution_time': 270,  # 4.5 phút (Lambda max 5 phút)
    'max_recommendations': 3,   # Giới hạn để tránh timeout
    
    # Symbols để phân tích (giới hạn để tăng tốc độ)
    'symbols_to_analyze': [
        'ADA/JPY', 'XRP/JPY', 'XLM/JPY', 'SUI/JPY'
    ],
    
    # Risk management
    'max_trades_per_session': 3,
    'allocation_percentage': 0.95,  # 95% balance
    'min_order_value_jpy': 1000,
    'max_order_value_jpy': 2000000,
    
    # Stop loss và take profit
    'default_stop_loss_percent': 3.0,    # 3%
    'default_tp1_percent': 2.0,          # 2%
    'default_tp2_percent': 5.0,          # 5%
    
    # DynamoDB settings
    'dynamodb_table_prefix': os.environ.get('DYNAMODB_PREFIX', 'crypto-trading'),
    'aws_region': os.environ.get('AWS_REGION', 'ap-southeast-1'),
    
    # Notification settings
    'sns_topic_arn': os.environ.get('SNS_TOPIC_ARN', ''),
    'send_notifications': True,
    
    # Emergency stop
    'emergency_stop_on_error_count': 5,
    'max_daily_loss_percent': 10.0,
    
    # Market data limits (tối ưu cho Lambda)
    'ohlcv_limit': 1000,        # Giảm từ 5000
    'orderbook_limit': 10,      # Giảm từ 20
    'analysis_timeout': 30,     # 30 giây per symbol
    
    # Performance monitoring
    'log_performance_metrics': True,
    'cloudwatch_namespace': 'CryptoTrading/Lambda'
}

# =============================================================================
# DYNAMODB TABLE CONFIGURATIONS
# =============================================================================
DYNAMODB_TABLES = {
    'trades': f"{LAMBDA_CONFIG['dynamodb_table_prefix']}-trades",
    'orders': f"{LAMBDA_CONFIG['dynamodb_table_prefix']}-orders", 
    'analysis': f"{LAMBDA_CONFIG['dynamodb_table_prefix']}-analysis",
    'system_status': f"{LAMBDA_CONFIG['dynamodb_table_prefix']}-system-status",
    'account_snapshots': f"{LAMBDA_CONFIG['dynamodb_table_prefix']}-account-snapshots"
}

# =============================================================================
# ENVIRONMENT VALIDATION
# =============================================================================
def validate_lambda_environment():
    """Kiểm tra environment variables cần thiết"""
    required_vars = [
        'BINANCE_API_KEY',
        'BINANCE_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    return True

# =============================================================================
# AWS LAMBDA SPECIFIC SETTINGS
# =============================================================================
LAMBDA_RUNTIME_CONFIG = {
    # Memory và timeout limits
    'memory_mb': int(os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE', '512')),
    'timeout_seconds': int(os.environ.get('AWS_LAMBDA_FUNCTION_TIMEOUT', '300')),
    
    # Concurrent execution
    'reserved_concurrency': 2,  # Tránh spam API
    
    # CloudWatch logs
    'log_retention_days': 7,
    'log_level': os.environ.get('LOG_LEVEL', 'INFO'),
    
    # X-Ray tracing
    'enable_xray': os.environ.get('ENABLE_XRAY', 'false').lower() == 'true'
}

# =============================================================================
# MONITORING AND ALERTING
# =============================================================================
MONITORING_CONFIG = {
    # CloudWatch metrics
    'custom_metrics': [
        'TradingSignals',
        'SuccessfulTrades', 
        'FailedTrades',
        'ExecutionDuration',
        'ErrorCount'
    ],
    
    # Alerts
    'alert_on_error_rate': 20,  # Alert if error rate > 20%
    'alert_on_execution_time': 240,  # Alert if execution > 4 minutes
    
    # SNS topics
    'error_notifications_topic': os.environ.get('ERROR_SNS_TOPIC', ''),
    'trade_notifications_topic': os.environ.get('TRADE_SNS_TOPIC', '')
}

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
SECURITY_CONFIG = {
    # API rate limiting
    'binance_rate_limit_buffer': 0.8,  # Use 80% of rate limit
    
    # Encryption
    'encrypt_sensitive_data': True,
    'kms_key_id': os.environ.get('KMS_KEY_ID', ''),
    
    # VPC settings (if needed)
    'vpc_enabled': os.environ.get('VPC_ENABLED', 'false').lower() == 'true',
    
    # IAM permissions - minimum required
    'required_permissions': [
        'dynamodb:GetItem',
        'dynamodb:PutItem', 
        'dynamodb:UpdateItem',
        'dynamodb:Query',
        'dynamodb:Scan',
        'sns:Publish',
        'cloudwatch:PutMetricData',
        'logs:CreateLogGroup',
        'logs:CreateLogStream',
        'logs:PutLogEvents'
    ]
}
