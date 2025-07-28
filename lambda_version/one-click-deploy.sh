#!/bin/bash

# 🚀 One-Click Deployment Script
# Script đơn giản để deploy trading bot lên AWS Lambda

echo "🎯 Crypto Trading Bot - One-Click AWS Lambda Deployment"
echo "======================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install AWS CLI on macOS
install_aws_cli_mac() {
    if command_exists brew; then
        print_step "Installing AWS CLI via Homebrew..."
        brew install awscli
    else
        print_step "Installing AWS CLI via curl..."
        curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
        sudo installer -pkg AWSCLIV2.pkg -target /
        rm AWSCLIV2.pkg
    fi
}

# Function to install SAM CLI on macOS
install_sam_cli_mac() {
    if command_exists brew; then
        print_step "Installing SAM CLI via Homebrew..."
        brew install aws-sam-cli
    else
        print_error "Please install Homebrew first: https://brew.sh/"
        exit 1
    fi
}

# Step 1: Check and install prerequisites
print_step "Checking prerequisites..."

# Check Python
if ! command_exists python3; then
    print_error "Python 3 is required but not installed."
    echo "Please install Python 3: https://www.python.org/downloads/"
    exit 1
fi
print_success "Python 3 found: $(python3 --version)"

# Check Git
if ! command_exists git; then
    print_error "Git is required but not installed."
    echo "Please install Git: https://git-scm.com/downloads"
    exit 1
fi
print_success "Git found: $(git --version)"

# Check/Install AWS CLI
if ! command_exists aws; then
    print_warning "AWS CLI not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        install_aws_cli_mac
    else
        print_error "Please install AWS CLI manually: https://aws.amazon.com/cli/"
        exit 1
    fi
fi
print_success "AWS CLI found: $(aws --version)"

# Check/Install SAM CLI
if ! command_exists sam; then
    print_warning "SAM CLI not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        install_sam_cli_mac
    else
        print_error "Please install SAM CLI manually: https://aws.amazon.com/serverless/sam/"
        exit 1
    fi
fi
print_success "SAM CLI found: $(sam --version)"

# Step 2: AWS Configuration
print_step "Checking AWS configuration..."

if ! aws sts get-caller-identity >/dev/null 2>&1; then
    print_warning "AWS credentials not configured."
    echo ""
    echo "🔧 Let's configure AWS credentials:"
    echo "You need:"
    echo "1. AWS Access Key ID"
    echo "2. AWS Secret Access Key"
    echo "3. Default region (suggest: ap-southeast-1)"
    echo ""
    read -p "Do you want to configure AWS now? (y/n): " configure_aws
    
    if [[ $configure_aws =~ ^[Yy]$ ]]; then
        aws configure
        
        # Test configuration
        if aws sts get-caller-identity >/dev/null 2>&1; then
            print_success "AWS configuration successful!"
        else
            print_error "AWS configuration failed. Please check your credentials."
            exit 1
        fi
    else
        print_error "AWS configuration is required. Please run 'aws configure' first."
        exit 1
    fi
else
    print_success "AWS credentials configured"
    aws sts get-caller-identity
fi

# Step 3: Get trading parameters
print_step "Collecting trading bot configuration..."

echo ""
echo "🔑 Trading Bot Configuration"
echo "You need the following from Binance:"

if [ -z "$BINANCE_API_KEY" ]; then
    echo ""
    echo "📝 Go to Binance → Account → API Management → Create API Key"
    echo "   Enable: Spot & Margin Trading, Futures Trading (if needed)"
    echo "   IP Restriction: Optional but recommended"
    echo ""
    read -p "Enter your Binance API Key: " BINANCE_API_KEY
fi

if [ -z "$BINANCE_SECRET" ]; then
    echo ""
    read -sp "Enter your Binance API Secret: " BINANCE_SECRET
    echo ""
fi

if [ -z "$NOTIFICATION_EMAIL" ]; then
    echo ""
    read -p "Enter your email for notifications: " NOTIFICATION_EMAIL
fi

# Choose environment
echo ""
echo "🎯 Deployment Environment:"
echo "1. testnet - For testing (safe, no real money)"
echo "2. production - For live trading (real money)"
echo ""
read -p "Choose environment (1 or 2): " env_choice

case $env_choice in
    1)
        ENVIRONMENT="testnet"
        ;;
    2)
        ENVIRONMENT="production"
        print_warning "You selected PRODUCTION environment!"
        print_warning "This will use REAL MONEY for trading!"
        read -p "Are you sure? Type 'YES' to continue: " confirm
        if [ "$confirm" != "YES" ]; then
            echo "Deployment cancelled."
            exit 1
        fi
        ;;
    *)
        print_error "Invalid choice. Defaulting to testnet."
        ENVIRONMENT="testnet"
        ;;
esac

# Step 4: Download and deploy
print_step "Downloading latest code from GitHub..."

TEMP_DIR="/tmp/crypto-bot-deploy-$(date +%s)"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Download code
if command_exists git; then
    git clone https://github.com/francisnguyenanh/EntrypointCrypto.git .
else
    curl -L https://github.com/francisnguyenanh/EntrypointCrypto/archive/main.zip -o code.zip
    unzip code.zip
    mv EntrypointCrypto-main/* .
    rm code.zip
fi

# Navigate to lambda version
cd lambda_version

print_success "Code downloaded successfully!"

# Step 5: Setup Python environment
print_step "Setting up Python environment..."

python3 -m venv venv
source venv/bin/activate
pip install -r requirements-local.txt

print_success "Dependencies installed!"

# Step 6: Test configuration
print_step "Testing configuration..."

python test_dependencies.py
if [ $? -ne 0 ]; then
    print_error "Dependency test failed!"
    exit 1
fi

sam validate
if [ $? -ne 0 ]; then
    print_error "SAM template validation failed!"
    exit 1
fi

print_success "Configuration tests passed!"

# Step 7: Build and deploy
print_step "Building Lambda package..."

sam build --use-container
if [ $? -ne 0 ]; then
    print_error "Build failed!"
    exit 1
fi

print_success "Build completed!"

print_step "Deploying to AWS Lambda ($ENVIRONMENT)..."

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

if [ $? -ne 0 ]; then
    print_error "Deployment failed!"
    exit 1
fi

print_success "Deployment completed!"

# Step 8: Test deployment
print_step "Testing deployment..."

LAMBDA_FUNCTION_NAME="crypto-trading-bot-${ENVIRONMENT}"
REGION="${AWS_REGION:-ap-southeast-1}"

aws lambda invoke \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$REGION" \
    --payload '{"action":"get_account_info"}' \
    --cli-binary-format raw-in-base64-out \
    response.json

if [ $? -eq 0 ]; then
    print_success "Deployment test successful!"
    echo ""
    echo "📊 Account Info Response:"
    cat response.json | python -m json.tool
else
    print_warning "Deployment test had issues, but deployment may still be successful."
fi

# Step 9: Get deployment info
print_step "Getting deployment information..."

FUNCTION_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`TradingBotFunctionArn`].OutputValue' \
    --output text 2>/dev/null)

API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text 2>/dev/null)

# Cleanup
deactivate
cd /
rm -rf "$TEMP_DIR"

# Final success message
echo ""
echo "🎉 ========================================== 🎉"
echo "     DEPLOYMENT SUCCESSFUL!"
echo "🎉 ========================================== 🎉"
echo ""
print_success "Your Crypto Trading Bot is now running on AWS Lambda!"
echo ""
echo "📋 Deployment Summary:"
echo "   Environment: $ENVIRONMENT"
echo "   Stack Name: $STACK_NAME"
echo "   Region: $REGION"
if [ -n "$FUNCTION_ARN" ]; then
    echo "   Function ARN: $FUNCTION_ARN"
fi
if [ -n "$API_URL" ]; then
    echo "   API Gateway: $API_URL"
fi
echo ""
echo "📝 What's Next:"
echo "   1. Check your email and confirm SNS subscription"
echo "   2. Monitor CloudWatch logs for trading activity"
echo "   3. Set up billing alerts in AWS Console"
echo ""
echo "🛠️  Management Commands:"
echo "   # View real-time logs"
echo "   aws logs tail /aws/lambda/$LAMBDA_FUNCTION_NAME --follow"
echo ""
echo "   # Manual trading trigger"
echo "   aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME --payload '{\"action\":\"analyze_and_trade\"}' response.json"
echo ""
echo "   # Emergency stop all trading"
echo "   aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME --payload '{\"action\":\"emergency_stop\"}' response.json"
echo ""
echo "💰 Cost Estimate: ~$3-10/month (much cheaper than running a server 24/7)"
echo ""
print_warning "Important: Monitor your AWS costs in the Billing Dashboard!"
print_warning "This bot trades with real money in production mode!"
echo ""
echo "📚 For detailed documentation, see: DEPLOYMENT_GUIDE.md"
echo ""
print_success "Happy Trading! 🚀📈"
