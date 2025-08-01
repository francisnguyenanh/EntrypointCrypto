#!/bin/bash

# Test script for GCP Cloud Function
echo "🧪 Testing Crypto Trading Bot Cloud Function..."

# Function URL - replace with your actual URL after deployment
FUNCTION_URL="https://asia-southeast1-YOUR_PROJECT_ID.cloudfunctions.net/crypto-trading-bot"

echo "⚠️  Please update FUNCTION_URL in this script with your actual function URL"
echo "   Current URL: $FUNCTION_URL"
echo ""

# Test 1: Get balance
echo "💰 Test 1: Get account balance..."
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{"action": "get_balance"}' \
  -w "\n\n"

echo "📊 Test 2: Analyze only (no trading)..."  
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{"action": "analyze_only"}' \
  -w "\n\n"

echo "🤖 Test 3: Full analysis and trading..."
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{"action": "analyze_and_trade"}' \
  -w "\n\n"

echo "✅ Testing completed!"
echo "📝 Check function logs: gcloud functions logs read crypto-trading-bot --region=asia-southeast1"
