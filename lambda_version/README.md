# Crypto Trading Bot - AWS Lambda Version

This is the serverless AWS Lambda version of the crypto trading bot, designed for cost-effective scheduled trading execution.

## 🏗️ Architecture

### Key Differences from EC2 Version
- **Serverless**: No continuous server costs, pay per execution
- **DynamoDB**: Replaces file-based storage for scalability
- **SNS**: Email notifications via AWS SNS instead of SMTP
- **EventBridge**: Scheduled execution instead of threading
- **5-minute limit**: Optimized for AWS Lambda execution limits

### Components
1. **lambda_handler.py** - Main Lambda entry point with event routing
2. **lambda_trading_core.py** - Optimized trading logic (no threading)
3. **lambda_config.py** - Environment-based configuration
4. **lambda_dynamodb.py** - Database operations with TTL management
5. **lambda_notifications.py** - SNS-based notification system
6. **template.yaml** - CloudFormation SAM infrastructure template
7. **deploy.sh** - Automated deployment script

## 📋 Prerequisites

1. **AWS CLI** installed and configured
   ```bash
   aws configure
   ```

2. **SAM CLI** for serverless deployment
   ```bash
   brew install aws-sam-cli  # macOS
   ```

3. **Binance API credentials** (same as EC2 version)

## 🚀 Quick Deployment

1. **Clone and navigate to Lambda version**
   ```bash
   cd lambda_version
   ```

2. **Deploy to testnet**
   ```bash
   ./deploy.sh testnet
   ```

3. **Deploy to production**
   ```bash
   ./deploy.sh production
   ```

The script will prompt for:
- Binance API Key
- Binance API Secret  
- Notification Email

## ⚙️ Configuration

### Environment Variables (set via SAM template)
```yaml
ENVIRONMENT: testnet/production
BINANCE_API_KEY: your_api_key
BINANCE_SECRET: your_secret
NOTIFICATION_SNS_TOPIC: auto-created
DYNAMODB_TABLE_PREFIX: crypto-trading-bot
```

### Trading Settings (in lambda_config.py)
```python
# Execution limits optimized for Lambda
"MAX_OHLCV_LIMIT": 1000,  # vs 5000 in EC2 version
"LAMBDA_TIMEOUT": 270,    # 4.5 minutes max execution
"QUICK_ANALYSIS": True,   # Simplified technical analysis
```

## 📊 AWS Resources Created

### DynamoDB Tables
- `{prefix}-trades` - Trade execution records (TTL: 30 days)
- `{prefix}-orders` - Active order tracking (TTL: 7 days)  
- `{prefix}-positions` - Position management (TTL: 7 days)

### Lambda Function
- **Runtime**: Python 3.9
- **Memory**: 512 MB
- **Timeout**: 5 minutes
- **Triggers**: EventBridge (scheduled) + API Gateway (manual)

### SNS Topic
- Email notifications for trades and errors
- Auto-subscribes provided email address

### CloudWatch
- Automated logging and monitoring
- Execution metrics and error tracking

## 🔄 Execution Methods

### 1. Scheduled Trading (Automatic)
- **EventBridge rule**: Every 4 minutes during market hours
- **Payload**: `{"action": "scheduled_trading"}`
- **Function**: Analyze markets and execute trades

### 2. Manual Trading (API Gateway)
```bash
# Analyze and trade
curl -X POST https://your-api-url/trading \
  -H 'Content-Type: application/json' \
  -d '{"action": "analyze_and_trade"}'

# Get account info
curl -X POST https://your-api-url/trading \
  -H 'Content-Type: application/json' \
  -d '{"action": "get_account_info"}'

# Emergency stop
curl -X POST https://your-api-url/trading \
  -H 'Content-Type: application/json' \
  -d '{"action": "emergency_stop"}'
```

### 3. Direct Lambda Invoke
```bash
# AWS CLI direct invoke
aws lambda invoke \
  --function-name crypto-trading-bot-testnet \
  --payload '{"action": "analyze_and_trade"}' \
  response.json
```

## 📈 Monitoring

### CloudWatch Logs
```bash
# Real-time log tailing
aws logs tail /aws/lambda/crypto-trading-bot-testnet --follow

# Error filtering
aws logs filter-log-events \
  --log-group-name /aws/lambda/crypto-trading-bot-testnet \
  --filter-pattern "ERROR"
```

### DynamoDB Data
```bash
# View recent trades
aws dynamodb scan \
  --table-name crypto-trading-bot-testnet-trades \
  --limit 10
```

## 💰 Cost Optimization

### Expected Costs (Testnet)
- **Lambda**: ~$1-5/month (720 executions @ 4min intervals)
- **DynamoDB**: ~$1-3/month (Read/Write units + storage)
- **SNS**: ~$0.50/month (Email notifications)
- **CloudWatch**: ~$1/month (Logs + metrics)

**Total**: ~$3-10/month vs $10-50/month for EC2

### Cost Monitoring
```bash
# Check Lambda costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

## 🛡️ Security Features

### IAM Permissions (Least Privilege)
- DynamoDB: Read/Write only to bot tables
- SNS: Publish only to notification topic
- CloudWatch: Log creation and writing
- No internet access outside AWS services

### Secrets Management
- API credentials encrypted at rest
- No hardcoded secrets in code
- Environment variable injection

## 🔧 Maintenance

### Update Deployment
```bash
# Redeploy with same settings
./deploy.sh testnet

# Update specific parameter
sam deploy \
  --parameter-overrides Environment=testnet BinanceApiKey=new_key
```

### Cleanup Resources
```bash
# Delete entire stack
aws cloudformation delete-stack \
  --stack-name crypto-trading-bot-testnet
```

### Debug Common Issues

1. **Timeout Errors**
   - Reduce OHLCV limit in config
   - Optimize technical analysis

2. **DynamoDB Throttling**
   - Increase read/write capacity
   - Check TTL cleanup

3. **SNS Delivery Issues**
   - Confirm email subscription
   - Check SNS topic permissions

## 📋 Comparison with EC2 Version

| Feature | EC2 Version | Lambda Version |
|---------|-------------|----------------|
| **Cost** | $10-50/month | $3-10/month |
| **Scaling** | Manual | Automatic |
| **Maintenance** | Server updates | Serverless |
| **Storage** | File-based | DynamoDB |
| **Execution** | Continuous | Scheduled/Event |
| **Monitoring** | Custom | CloudWatch |
| **Email** | SMTP | SNS |
| **Complexity** | Lower | Higher (AWS) |

## 🎯 Best Practices

1. **Start with testnet** for all testing
2. **Monitor costs** via AWS Billing Dashboard  
3. **Set CloudWatch alarms** for errors and costs
4. **Use emergency stop** during high volatility
5. **Review logs regularly** for optimization opportunities
6. **Test manual triggers** before relying on scheduled execution

## 🆘 Support

### Common Commands
```bash
# Get function status
aws lambda get-function --function-name crypto-trading-bot-testnet

# Update environment variables
aws lambda update-function-configuration \
  --function-name crypto-trading-bot-testnet \
  --environment Variables='{ENVIRONMENT=testnet,DEBUG=true}'

# Manual emergency stop
aws lambda invoke \
  --function-name crypto-trading-bot-testnet \
  --payload '{"action": "emergency_stop"}' \
  response.json
```

### Troubleshooting
- Check CloudWatch logs for execution details
- Verify SNS email subscription confirmation
- Ensure DynamoDB tables are created
- Confirm EventBridge rule is enabled
- Test API Gateway endpoints manually

---

**Note**: This Lambda version provides the same trading logic as the EC2 version but optimized for serverless execution with significant cost savings and automatic scaling.
