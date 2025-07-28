#!/bin/bash

# Script để pull code từ GitHub và deploy lên AWS Lambda
# Usage: ./github-deploy.sh [testnet|production] [branch_name]

set -e

ENVIRONMENT=${1:-testnet}
BRANCH=${2:-main}
REPO_URL="https://github.com/francisnguyenanh/EntrypointCrypto.git"
TEMP_DIR="/tmp/crypto-bot-deploy-$(date +%s)"

echo "🐙 GitHub to AWS Lambda Deployment Script"
echo "=========================================="
echo "Repository: $REPO_URL"
echo "Branch: $BRANCH"
echo "Environment: $ENVIRONMENT"
echo "Temp directory: $TEMP_DIR"
echo ""

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(testnet|production)$ ]]; then
    echo "❌ Error: Environment must be 'testnet' or 'production'"
    exit 1
fi

# Check required tools
echo "🔍 Checking required tools..."
command -v git >/dev/null 2>&1 || { echo "❌ Git is required but not installed." >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI is required but not installed." >&2; exit 1; }
command -v sam >/dev/null 2>&1 || { echo "❌ SAM CLI is required but not installed." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 is required but not installed." >&2; exit 1; }

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
aws sts get-caller-identity >/dev/null 2>&1 || { 
    echo "❌ AWS credentials not configured. Run 'aws configure' first." >&2
    exit 1
}

# Create temp directory
echo "📁 Creating temporary directory..."
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Clone repository
echo "📥 Cloning repository from GitHub..."
git clone "$REPO_URL" .
git checkout "$BRANCH"

# Verify lambda_version exists
if [ ! -d "lambda_version" ]; then
    echo "❌ Error: lambda_version directory not found in repository"
    exit 1
fi

cd lambda_version

# Get API credentials if not set in environment
if [ -z "$BINANCE_API_KEY" ]; then
    echo "🔑 Enter Binance API Key:"
    read -r BINANCE_API_KEY
fi

if [ -z "$BINANCE_SECRET" ]; then
    echo "🔑 Enter Binance API Secret:"
    read -rs BINANCE_SECRET
fi

if [ -z "$NOTIFICATION_EMAIL" ]; then
    echo "📧 Enter notification email:"
    read -r NOTIFICATION_EMAIL
fi

# Validate inputs
if [ -z "$BINANCE_API_KEY" ] || [ -z "$BINANCE_SECRET" ] || [ -z "$NOTIFICATION_EMAIL" ]; then
    echo "❌ Missing required parameters"
    exit 1
fi

# Setup Python environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies for local validation
echo "📦 Installing dependencies..."
pip install -r requirements-local.txt

# Test dependencies
echo "🧪 Testing dependencies..."
python test_dependencies.py

# Validate SAM template
echo "📋 Validating SAM template..."
sam validate

# Build Lambda package
echo "🏗️ Building Lambda package..."
rm -rf .aws-sam/
sam build --use-container

# Deploy to AWS
echo "🚀 Deploying to AWS Lambda..."
STACK_NAME="crypto-trading-bot-${ENVIRONMENT}"

sam deploy \
    --stack-name "$STACK_NAME" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --region "${AWS_REGION:-ap-southeast-1}" \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        BinanceApiKey="$BINANCE_API_KEY" \
        BinanceSecret="$BINANCE_SECRET" \
        NotificationEmail="$NOTIFICATION_EMAIL" \
    --confirm-changeset

# Get deployment outputs
echo "📋 Getting deployment information..."
REGION="${AWS_REGION:-ap-southeast-1}"

FUNCTION_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`TradingBotFunctionArn`].OutputValue' \
    --output text)

API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

echo ""
echo "✅ Deployment successful!"
echo "🔗 Function ARN: $FUNCTION_ARN"
echo "🌐 API Gateway URL: $API_URL"

# Test deployment
echo ""
echo "🧪 Testing deployment..."
LAMBDA_FUNCTION_NAME="crypto-trading-bot-${ENVIRONMENT}"

aws lambda invoke \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$REGION" \
    --payload '{"action":"get_account_info"}' \
    --cli-binary-format raw-in-base64-out \
    response.json

if [ $? -eq 0 ]; then
    echo "✅ Lambda function test successful"
    echo "📊 Response:"
    cat response.json | python -m json.tool | head -20
else
    echo "❌ Lambda function test failed"
fi

# Cleanup
echo ""
echo "🧹 Cleaning up..."
deactivate
cd /
rm -rf "$TEMP_DIR"

echo ""
echo "🎉 GitHub to Lambda deployment completed!"
echo ""
echo "📝 Management commands:"
echo "• View logs: aws logs tail /aws/lambda/$LAMBDA_FUNCTION_NAME --follow"
echo "• Manual invoke: aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME --payload '{\"action\":\"analyze_and_trade\"}' response.json"
echo "• Emergency stop: aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME --payload '{\"action\":\"emergency_stop\"}' response.json"
echo ""
echo "⚠️  Remember to:"
echo "• Confirm SNS email subscription in your inbox"
echo "• Monitor CloudWatch logs for scheduled executions"
echo "• Set up CloudWatch alarms for cost and error monitoring"
