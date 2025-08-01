#!/bin/bash

# Deploy script for Google Cloud Functions
# Make sure gcloud CLI is installed and authenticated

echo "🚀 Deploying Crypto Trading Bot to Google Cloud Functions..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK first."
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if .env.yaml exists
if [ ! -f ".env.yaml" ]; then
    echo "❌ .env.yaml file not found"
    echo "   Please create .env.yaml from .env.yaml.template"
    exit 1
fi

# Check if authenticated
echo "🔐 Checking authentication..."
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Not authenticated with gcloud"
    echo "   Please run: gcloud auth login"
    echo "   Then run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "✅ Project ID: $PROJECT_ID"

# Deploy function
echo "📦 Deploying function..."
gcloud functions deploy crypto-trading-bot \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --memory 512MB \
  --timeout 540s \
  --env-vars-file .env.yaml \
  --region asia-southeast1 \
  --entry-point crypto_trading_main

if [ $? -eq 0 ]; then
    echo "✅ Function deployed successfully!"
    
    # Get trigger URL
    TRIGGER_URL=$(gcloud functions describe crypto-trading-bot --region=asia-southeast1 --format="value(httpsTrigger.url)")
    echo "🔗 Function URL: $TRIGGER_URL"
    
    echo ""
    echo "🧪 Test your function:"
    echo "curl -X POST $TRIGGER_URL -H \"Content-Type: application/json\" -d '{\"action\": \"get_balance\"}'"
    
    echo ""
    echo "⏰ Next steps:"
    echo "1. Setup Cloud Scheduler with URL: $TRIGGER_URL"  
    echo "2. Monitor function logs in GCP Console"
    echo "3. Check Firestore for trading data"
else
    echo "❌ Deployment failed!"
    exit 1
fi
