# Lambda Environment Variables Configuration

## 🔧 Required Environment Variables

### **Binance API Configuration**
```bash
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_TESTNET=true  # Set to 'false' for live trading
```

### **Email Notification Configuration (Optional)**
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password  # Gmail App Password
RECIPIENT_EMAIL=trading_alerts@gmail.com
```

### **AWS SNS Configuration (Optional)**
```bash
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:trading-alerts
```

## 🎯 Trading Mode Control

### **Test Mode (Default)**
```bash
BINANCE_TESTNET=true
```
- Uses Binance Testnet
- Safe for testing
- No real money

### **Live Trading Mode**
```bash
BINANCE_TESTNET=false
```
- ⚠️ **WARNING**: Uses real money
- Only use after thorough testing
- Ensure proper risk management

## 📧 Email vs SNS Notifications

### **Email Only (Like app.py)**
```bash
# Set email settings only
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_password
RECIPIENT_EMAIL=alerts@gmail.com
# Don't set SNS_TOPIC_ARN
```

### **SNS Only**
```bash
# Set SNS only
SNS_TOPIC_ARN=arn:aws:sns:region:account:topic
# Don't set email settings
```

### **Both Email + SNS**
```bash
# Set both email and SNS settings
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_password
RECIPIENT_EMAIL=alerts@gmail.com
SNS_TOPIC_ARN=arn:aws:sns:region:account:topic
```

## 🚀 AWS Lambda Deployment

### **Set Environment Variables in Lambda Console:**
1. Go to Lambda Function → Configuration → Environment variables
2. Add all required variables
3. Save configuration

### **Using AWS CLI:**
```bash
aws lambda update-function-configuration \
    --function-name crypto-trading-bot \
    --environment Variables='{
        "BINANCE_API_KEY":"your_api_key",
        "BINANCE_SECRET_KEY":"your_secret_key",
        "BINANCE_TESTNET":"true",
        "SENDER_EMAIL":"your_email@gmail.com",
        "SENDER_PASSWORD":"your_app_password",
        "RECIPIENT_EMAIL":"alerts@gmail.com"
    }'
```

## 🛡️ Security Best Practices

1. **Never hardcode API keys** in source code
2. **Use AWS Secrets Manager** for production
3. **Enable Lambda encryption** at rest
4. **Use IAM roles** with minimum permissions
5. **Rotate API keys** regularly

## 📋 Checklist

- [ ] Binance API keys configured
- [ ] Test mode enabled initially  
- [ ] Email settings configured (optional)
- [ ] SNS topic created (optional)
- [ ] All environment variables set
- [ ] Lambda function tested with test payloads

---
*No DynamoDB required - Lambda is stateless and cost-effective!*
