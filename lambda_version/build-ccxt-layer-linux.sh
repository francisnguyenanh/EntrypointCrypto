#!/bin/bash

# Script to build CCXT layer for AWS Lambda using Docker (Linux compatible)
echo "🚀 Building CCXT Layer for AWS Lambda (Linux x86_64)..."

# Create directory structure
rm -rf ccxt-layer-linux
mkdir -p ccxt-layer-linux

# Use Docker to build for Linux
echo "🐳 Using Docker to build Linux-compatible layer..."
docker run --rm -v "$PWD":/var/task -w /var/task python:3.9-slim-bullseye /bin/bash -c "
    mkdir -p ccxt-layer-linux/python/lib/python3.9/site-packages
    pip install ccxt==4.2.25 -t ccxt-layer-linux/python/lib/python3.9/site-packages/
    echo 'Layer built successfully for Linux x86_64'
"

# Check if build was successful
if [ -d "ccxt-layer-linux/python/lib/python3.9/site-packages/ccxt" ]; then
    echo "✅ CCXT installed successfully"
    
    # Show layer size
    echo "📊 Layer size:"
    du -sh ccxt-layer-linux/python/
    
    # Create deployment package
    cd ccxt-layer-linux
    echo "📦 Creating layer ZIP..."
    zip -r ../ccxt-layer-linux.zip python/
    cd ..
    
    # Show final package info
    echo "✅ Linux-compatible layer package created:"
    ls -lh ccxt-layer-linux.zip
    
    echo ""
    echo "🎯 Next steps:"
    echo "1. Upload ccxt-layer-linux.zip to AWS Lambda as a new layer"
    echo "2. Set compatible runtimes: python3.9"
    echo "3. Set compatible architectures: x86_64"
    echo "4. Add this layer to your Lambda function"
    echo "5. Test with the debug function"
else
    echo "❌ Failed to build layer"
    echo "Make sure Docker is running and try again"
fi
