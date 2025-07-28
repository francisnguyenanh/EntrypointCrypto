# 🚀 Hướng dẫn Deploy AWS Lambda - Crypto Trading Bot

## 📋 Mục lục
1. [Chuẩn bị môi trường](#chuẩn-bị-môi-trường)
2. [Cấu hình AWS](#cấu-hình-aws)
3. [Deploy từ GitHub](#deploy-từ-github)
4. [Deploy thủ công](#deploy-thủ-công)
5. [CI/CD với GitHub Actions](#cicd-với-github-actions)
6. [Monitoring và Debug](#monitoring-và-debug)

---

## 🛠️ Chuẩn bị môi trường

### 1. Cài đặt AWS CLI
```bash
# macOS
brew install awscli

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install awscli

# Windows
# Download từ: https://aws.amazon.com/cli/
```

### 2. Cài đặt SAM CLI
```bash
# macOS
brew install aws-sam-cli

# Ubuntu/Debian
pip install aws-sam-cli

# Windows
# Download từ: https://aws.amazon.com/serverless/sam/
```

### 3. Cài đặt Git
```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git
```

---

## 🔐 Cấu hình AWS

### 1. Tạo IAM User
1. Đăng nhập AWS Console
2. Vào **IAM** → **Users** → **Create User**
3. Tên user: `crypto-bot-deployer`
4. Attach policies:
   - `AWSLambdaFullAccess`
   - `IAMFullAccess`
   - `AmazonDynamoDBFullAccess`
   - `AmazonSNSFullAccess`
   - `CloudFormationFullAccess`
   - `AmazonAPIGatewayAdministrator`

### 2. Tạo Access Key
1. Vào user vừa tạo → **Security credentials**
2. **Create access key** → **CLI**
3. Lưu lại `Access Key ID` và `Secret Access Key`

### 3. Cấu hình AWS CLI
```bash
aws configure
# AWS Access Key ID: [Nhập access key]
# AWS Secret Access Key: [Nhập secret key]
# Default region name: ap-southeast-1
# Default output format: json
```

### 4. Verify cấu hình
```bash
aws sts get-caller-identity
# Phải trả về thông tin user của bạn
```

---

## 🐙 Deploy từ GitHub

### Phương pháp 1: Clone và Deploy Local

#### 1. Clone repository
```bash
# Clone repository
git clone https://github.com/francisnguyenanh/EntrypointCrypto.git
cd EntrypointCrypto/lambda_version

# Hoặc download ZIP từ GitHub
```

#### 2. Setup môi trường Python
```bash
# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Cài đặt dependencies
./setup.sh
```

#### 3. Cấu hình trading parameters
```bash
# Edit file lambda_config.py
nano lambda_config.py

# Hoặc dùng environment variables
export BINANCE_API_KEY="your_api_key"
export BINANCE_SECRET="your_secret"
export NOTIFICATION_EMAIL="your_email@example.com"
```

#### 4. Deploy lên AWS
```bash
# Deploy testnet
./deploy.sh testnet

# Deploy production
./deploy.sh production
```

### Phương pháp 2: AWS CodeStar/CodeCommit

#### 1. Tạo CodeCommit Repository
```bash
# Tạo repository trên AWS
aws codecommit create-repository --repository-name crypto-trading-bot

# Clone và push code
git clone https://git-codecommit.ap-southeast-1.amazonaws.com/v1/repos/crypto-trading-bot
cd crypto-trading-bot

# Copy lambda_version files vào đây
cp -r /path/to/EntrypointCrypto/lambda_version/* .

# Push to CodeCommit
git add .
git commit -m "Initial commit"
git push origin main
```

#### 2. Tạo Build Pipeline
Tạo file `buildspec.yml`:
```yaml
version: 0.2
phases:
  install:
    runtime-versions:
      python: 3.9
    commands:
      - pip install aws-sam-cli
  build:
    commands:
      - sam build
      - sam deploy --no-confirm-changeset --stack-name crypto-trading-bot-${ENV:-testnet}
artifacts:
  files:
    - '**/*'
```

---

## 🔧 Deploy thủ công từ máy local

### 1. Chuẩn bị code
```bash
# Tạo thư mục project
mkdir crypto-bot-lambda
cd crypto-bot-lambda

# Download code từ GitHub
curl -L https://github.com/francisnguyenanh/EntrypointCrypto/archive/main.zip -o code.zip
unzip code.zip
cp -r EntrypointCrypto-main/lambda_version/* .
rm -rf EntrypointCrypto-main code.zip
```

### 2. Cấu hình SAM template
Đảm bảo file `template.yaml` có đúng parameters:
```yaml
Parameters:
  Environment:
    Type: String
    Default: testnet
    AllowedValues: [testnet, production]
  
  BinanceApiKey:
    Type: String
    NoEcho: true
    Description: Binance API Key
  
  BinanceSecret:
    Type: String
    NoEcho: true
    Description: Binance API Secret
  
  NotificationEmail:
    Type: String
    Description: Email for notifications
```

### 3. Build và Deploy
```bash
# Build
sam build --use-container

# Deploy với guided mode (lần đầu)
sam deploy --guided

# Deploy với parameters cụ thể
sam deploy \
  --stack-name crypto-trading-bot-testnet \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    Environment=testnet \
    BinanceApiKey=your_api_key \
    BinanceSecret=your_secret \
    NotificationEmail=your_email@example.com
```

---

## 🔄 CI/CD với GitHub Actions

### 1. Tạo GitHub Secrets
Vào repository GitHub → **Settings** → **Secrets and variables** → **Actions**

Thêm secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `BINANCE_API_KEY`
- `BINANCE_SECRET`
- `NOTIFICATION_EMAIL`

### 2. Tạo workflow file
Tạo `.github/workflows/deploy-lambda.yml`:

```yaml
name: Deploy to AWS Lambda

on:
  push:
    branches: [main]
    paths: ['lambda_version/**']
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'testnet'
        type: choice
        options:
        - testnet
        - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Setup SAM CLI
      uses: aws-actions/setup-sam@v2
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ap-southeast-1
    
    - name: Build Lambda package
      run: |
        cd lambda_version
        sam build --use-container
    
    - name: Deploy to AWS
      run: |
        cd lambda_version
        ENV=${{ github.event.inputs.environment || 'testnet' }}
        sam deploy \
          --stack-name crypto-trading-bot-$ENV \
          --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
          --parameter-overrides \
            Environment=$ENV \
            BinanceApiKey=${{ secrets.BINANCE_API_KEY }} \
            BinanceSecret=${{ secrets.BINANCE_SECRET }} \
            NotificationEmail=${{ secrets.NOTIFICATION_EMAIL }} \
          --no-confirm-changeset
    
    - name: Test deployment
      run: |
        cd lambda_version
        aws lambda invoke \
          --function-name crypto-trading-bot-${{ github.event.inputs.environment || 'testnet' }} \
          --payload '{"action":"get_account_info"}' \
          response.json
        cat response.json
```

### 3. Manual deployment trigger
```bash
# Trigger deployment via GitHub CLI
gh workflow run deploy-lambda.yml -f environment=testnet

# Hoặc trigger via API
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/francisnguyenanh/EntrypointCrypto/actions/workflows/deploy-lambda.yml/dispatches \
  -d '{"ref":"main","inputs":{"environment":"testnet"}}'
```

---

## 🔍 Monitoring và Debug

### 1. CloudWatch Logs
```bash
# Xem logs real-time
aws logs tail /aws/lambda/crypto-trading-bot-testnet --follow

# Filter errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/crypto-trading-bot-testnet \
  --filter-pattern "ERROR"

# Specific time range
aws logs filter-log-events \
  --log-group-name /aws/lambda/crypto-trading-bot-testnet \
  --start-time $(date -d '1 hour ago' +%s)000
```

### 2. Test Lambda function
```bash
# Test function
aws lambda invoke \
  --function-name crypto-trading-bot-testnet \
  --payload '{"action":"get_account_info"}' \
  response.json

# View response
cat response.json | python -m json.tool
```

### 3. Update function code
```bash
# Quick code update (không rebuild infrastructure)
sam deploy --no-confirm-changeset

# Update với new parameters
sam deploy \
  --parameter-overrides Environment=testnet NewParam=value \
  --no-confirm-changeset
```

### 4. Debug common issues
```bash
# Check function configuration
aws lambda get-function --function-name crypto-trading-bot-testnet

# Check CloudFormation stack
aws cloudformation describe-stacks --stack-name crypto-trading-bot-testnet

# Check DynamoDB tables
aws dynamodb list-tables | grep crypto-trading

# Check SNS topics
aws sns list-topics | grep crypto-trading
```

---

## 🎯 Quick Commands

### Development
```bash
# Setup local environment
./setup.sh

# Test locally
python test_local.py

# Test dependencies
python test_dependencies.py
```

### Deployment
```bash
# Deploy testnet
./deploy.sh testnet

# Deploy production
./deploy.sh production

# Manual SAM deploy
sam deploy --guided
```

### Management
```bash
# View logs
aws logs tail /aws/lambda/crypto-trading-bot-testnet --follow

# Invoke function
aws lambda invoke --function-name crypto-trading-bot-testnet --payload '{"action":"analyze_and_trade"}' response.json

# Emergency stop
aws lambda invoke --function-name crypto-trading-bot-testnet --payload '{"action":"emergency_stop"}' response.json

# Delete stack
aws cloudformation delete-stack --stack-name crypto-trading-bot-testnet
```

---

## ⚠️ Lưu ý quan trọng

1. **Environment variables**: Luôn dùng AWS Secrets Manager hoặc Parameter Store cho production
2. **API limits**: Binance có rate limits, monitor carefully
3. **Costs**: Lambda + DynamoDB + SNS có thể tốn phí, set up billing alerts
4. **Security**: Không commit API keys vào GitHub
5. **Testing**: Luôn test với testnet trước khi deploy production
6. **Backup**: Backup DynamoDB data thường xuyên

---

🎉 **Chúc bạn deploy thành công!** 🎉
