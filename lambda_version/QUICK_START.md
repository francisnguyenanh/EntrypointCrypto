# 🚀 Quick Start - Deploy to AWS Lambda

## ⚡ One-Click Deployment (Recommended)

```bash
# Download and run the one-click deployment script
curl -L https://raw.githubusercontent.com/francisnguyenanh/EntrypointCrypto/main/lambda_version/one-click-deploy.sh | bash
```

**What it does:**
- ✅ Checks and installs prerequisites (AWS CLI, SAM CLI)
- ✅ Configures AWS credentials
- ✅ Downloads latest code from GitHub
- ✅ Builds and deploys to AWS Lambda
- ✅ Tests the deployment

## 🛠️ Manual Deployment

### 1. Prerequisites
```bash
# Install AWS CLI
brew install awscli  # macOS
# sudo apt-get install awscli  # Ubuntu

# Install SAM CLI
brew install aws-sam-cli  # macOS

# Configure AWS
aws configure
```

### 2. Clone and Deploy
```bash
# Clone repository
git clone https://github.com/francisnguyenanh/EntrypointCrypto.git
cd EntrypointCrypto/lambda_version

# Deploy directly
./deploy.sh testnet

# Or deploy from GitHub
./github-deploy.sh testnet
```

## 🔄 GitHub Actions (CI/CD)

### Setup GitHub Secrets
1. Go to repository → **Settings** → **Secrets and variables** → **Actions**
2. Add secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY` 
   - `BINANCE_API_KEY`
   - `BINANCE_SECRET`
   - `NOTIFICATION_EMAIL`

### Trigger Deployment
```bash
# Manual trigger via GitHub web interface
# Go to Actions → Deploy Crypto Trading Bot → Run workflow

# Or via GitHub CLI
gh workflow run deploy-lambda.yml -f environment=testnet
```

## 📊 Management Commands

```bash
# View logs
aws logs tail /aws/lambda/crypto-trading-bot-testnet --follow

# Manual trading
aws lambda invoke --function-name crypto-trading-bot-testnet --payload '{"action":"analyze_and_trade"}' response.json

# Emergency stop
aws lambda invoke --function-name crypto-trading-bot-testnet --payload '{"action":"emergency_stop"}' response.json

# Check account
aws lambda invoke --function-name crypto-trading-bot-testnet --payload '{"action":"get_account_info"}' response.json
```

## 🎯 Deployment Options

| Method | Best For | Complexity | Auto-Updates |
|--------|----------|------------|--------------|
| **One-Click Script** | Beginners | ⭐ Easy | ❌ Manual |
| **Manual Local** | Developers | ⭐⭐ Medium | ❌ Manual |
| **GitHub Actions** | Teams | ⭐⭐⭐ Advanced | ✅ Automatic |

## 💰 Cost Estimate

- **Lambda**: ~$1-5/month
- **DynamoDB**: ~$1-3/month  
- **SNS**: ~$0.50/month
- **CloudWatch**: ~$1/month
- **Total**: ~$3-10/month

## 🆘 Quick Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'boto3'"**
   ```bash
   # Use requirements-local.txt for local development
   pip install -r requirements-local.txt
   ```

2. **AWS credentials not configured**
   ```bash
   aws configure
   # Enter your Access Key ID and Secret
   ```

3. **Deployment fails**
   ```bash
   # Check CloudFormation events
   aws cloudformation describe-stack-events --stack-name crypto-trading-bot-testnet
   
   # Check Lambda logs
   aws logs describe-log-groups | grep crypto-trading
   ```

4. **Function timeout**
   ```bash
   # Check function configuration
   aws lambda get-function-configuration --function-name crypto-trading-bot-testnet
   ```

### Test Dependencies
```bash
cd lambda_version
python test_dependencies.py
```

### Local Testing
```bash
cd lambda_version
python test_local.py
```

## 📚 Full Documentation

For detailed documentation, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

⚠️ **Important**: Always test with `testnet` environment first before deploying to `production`!
