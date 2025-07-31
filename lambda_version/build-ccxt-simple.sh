#!/bin/bash

# Build simplified CCXT layer without compiled dependencies
echo "🚀 Building Simplified CCXT Layer (Pure Python)..."

# Create directory structure
rm -rf ccxt-simple
mkdir -p ccxt-simple/python/lib/python3.9/site-packages

# Install CCXT with no binary dependencies
echo "📦 Installing CCXT (pure Python mode)..."
pip install --no-binary=:all: ccxt==4.2.25 -t ccxt-simple/python/lib/python3.9/site-packages/ --no-deps

# Install only essential pure-Python dependencies
pip install --no-binary=:all: requests -t ccxt-simple/python/lib/python3.9/site-packages/ --no-deps
pip install --no-binary=:all: urllib3 -t ccxt-simple/python/lib/python3.9/site-packages/ --no-deps
pip install --no-binary=:all: certifi -t ccxt-simple/python/lib/python3.9/site-packages/ --no-deps
pip install --no-binary=:all: charset-normalizer -t ccxt-simple/python/lib/python3.9/site-packages/ --no-deps
pip install --no-binary=:all: idna -t ccxt-simple/python/lib/python3.9/site-packages/ --no-deps

# Check installation
echo "🔍 Checking installation..."
ls -la ccxt-simple/python/lib/python3.9/site-packages/ | grep ccxt

# Show layer size
echo "📊 Layer size:"
du -sh ccxt-simple/python/

# Create deployment package
cd ccxt-simple
echo "📦 Creating layer ZIP..."
zip -r ../ccxt-simple.zip python/
cd ..

# Show final package info
echo "✅ Simplified layer package created:"
ls -lh ccxt-simple.zip

echo ""
echo "⚠️  Note: This simplified layer may have limited functionality"
echo "   Some exchanges requiring cryptography might not work"
echo "   But basic trading operations should work fine"
echo ""
echo "🎯 Next steps:"
echo "1. Upload ccxt-simple.zip to AWS Lambda as a new layer"
echo "2. Set compatible runtimes: python3.9"
echo "3. Add this layer to your Lambda function"
echo "4. Test with the debug function"
