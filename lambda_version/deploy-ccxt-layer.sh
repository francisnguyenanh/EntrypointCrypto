#!/bin/bash

# Script to deploy CCXT layer to AWS Lambda
echo "🚀 Deploying CCXT Layer to AWS Lambda..."

# Check if ccxt-layer.zip exists
if [ ! -f "ccxt-layer.zip" ]; then
    echo "❌ Error: ccxt-layer.zip not found!"
    echo "Run ./build-ccxt-layer.sh first"
    exit 1
fi

# Set variables
LAYER_NAME="ccxt-trading-layer"
DESCRIPTION="CCXT Trading Library v4.2.25 with all dependencies"
REGION="ap-southeast-2"

echo "📦 Uploading layer: $LAYER_NAME"
echo "📍 Region: $REGION"
echo "📋 Description: $DESCRIPTION"

# Deploy layer
aws lambda publish-layer-version \
    --layer-name "$LAYER_NAME" \
    --description "$DESCRIPTION" \
    --license-info "MIT" \
    --zip-file fileb://ccxt-layer.zip \
    --compatible-runtimes python3.9 \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Layer deployed successfully!"
    echo ""
    echo "🎯 Next steps:"
    echo "1. Add this layer to your Lambda function"
    echo "2. Test with emergency_debug: true"
    echo "3. Deploy your full trading bot"
    echo ""
    echo "📝 Layer ARN will be displayed above"
else
    echo "❌ Failed to deploy layer"
    echo "Check your AWS credentials and permissions"
    exit 1
fi
