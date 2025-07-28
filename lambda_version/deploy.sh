#!/bin/bash

# Deployment script for Crypto Trading Bot Lambda version
# Usage: ./deploy.sh [testnet|production]

set -e

ENVIRONMENT=${1:-testnet}
REGION=${AWS_REGION:-ap-southeast-1}
STACK_NAME="crypto-trading-bot-${ENVIRONMENT}"

echo "🚀 Deploying Crypto Trading Bot to AWS Lambda"
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"
echo "Stack: ${STACK_NAME}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(testnet|production)$ ]]; then
    echo "❌ Error: Environment must be 'testnet' or 'production'"
    exit 1
fi

# Check required tools
echo "🔍 Checking required tools..."
command -v sam >/dev/null 2>&1 || { echo "❌ SAM CLI is required but not installed. Aborting." >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI is required but not installed. Aborting." >&2; exit 1; }

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
aws sts get-caller-identity >/dev/null 2>&1 || { echo "❌ AWS credentials not configured. Run 'aws configure' first." >&2; exit 1; }

# Get API credentials (prompt if not set)
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

# Build and deploy
echo "🏗️ Building Lambda package..."

# Create deployment package
rm -rf .aws-sam/

# Use requirements.txt for deployment (without boto3)
# boto3 is already available in AWS Lambda runtime
sam build --use-container

echo "📦 Deploying to AWS..."

# Deploy with parameters
sam deploy \
    --stack-name "$STACK_NAME" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --region "$REGION" \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        BinanceApiKey="$BINANCE_API_KEY" \
        BinanceSecret="$BINANCE_SECRET" \
        NotificationEmail="$NOTIFICATION_EMAIL" \
    --confirm-changeset

# Get outputs
echo "📋 Deployment completed! Getting stack outputs..."

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
echo ""

# Test the deployment
echo "🧪 Testing deployment..."

# Test via Lambda invoke
echo "Testing Lambda function directly..."
LAMBDA_FUNCTION_NAME="crypto-trading-bot-${ENVIRONMENT}"

aws lambda invoke \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$REGION" \
    --payload '{"action":"get_account_info"}' \
    --cli-binary-format raw-in-base64-out \
    response.json

if [ $? -eq 0 ]; then
    echo "✅ Lambda function test successful"
    echo "Response:"
    cat response.json | python -m json.tool
    rm response.json
else
    echo "❌ Lambda function test failed"
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Confirm SNS email subscriptions in your inbox"
echo "2. Test manual trading via API Gateway:"
echo "   curl -X POST $API_URL/trading -H 'Content-Type: application/json' -d '{\"action\":\"analyze_and_trade\"}'"
echo "3. Monitor CloudWatch logs for scheduled executions"
echo "4. Check DynamoDB tables for trading data"
echo ""
echo "🔧 Management commands:"
echo "• View logs: aws logs tail /aws/lambda/$LAMBDA_FUNCTION_NAME --follow"
echo "• Manual invoke: aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME --payload '{\"action\":\"analyze_and_trade\"}' response.json"
echo "• Emergency stop: aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME --payload '{\"action\":\"emergency_stop\"}' response.json"
echo ""
echo "⚠️  Remember:"
echo "• This is deployed to ${ENVIRONMENT} environment"
echo "• Monitor costs in AWS Billing Dashboard"
echo "• Set up CloudWatch alarms for monitoring"
