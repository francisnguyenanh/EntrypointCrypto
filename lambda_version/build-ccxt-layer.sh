#!/bin/bash

# Script to build CCXT layer for AWS Lambda
echo "🚀 Building CCXT Layer for AWS Lambda..."

# Create directory structure
rm -rf ccxt-layer
mkdir -p ccxt-layer/python/lib/python3.9/site-packages

# Navigate to layer directory
cd ccxt-layer

# Install CCXT and dependencies
echo "📦 Installing CCXT..."
pip install ccxt==4.2.25 -t python/lib/python3.9/site-packages/

# Check installation
echo "🔍 Checking CCXT installation..."
ls -la python/lib/python3.9/site-packages/ | grep ccxt

# Show layer size
echo "📊 Layer size:"
du -sh python/

# Create deployment package
echo "📦 Creating layer ZIP..."
zip -r ccxt-layer.zip python/

# Show final package info
echo "✅ Layer package created:"
ls -lh ccxt-layer.zip

echo ""
echo "🎯 Next steps:"
echo "1. Upload ccxt-layer.zip to AWS Lambda as a new layer"
echo "2. Set compatible runtimes: python3.9"
echo "3. Add this layer to your Lambda function"
echo "4. Test with the debug function"
