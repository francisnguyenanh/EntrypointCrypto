#!/bin/bash

# Script to build CCXT layer using Docker for AWS Lambda compatibility
echo "🐳 Building CCXT Layer with Docker for AWS Lambda..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Clean up any previous builds
echo "🧹 Cleaning up previous builds..."
rm -rf ccxt-layer.zip layer-output
mkdir -p layer-output

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t ccxt-lambda-builder .

if [ $? -ne 0 ]; then
    echo "❌ Failed to build Docker image"
    exit 1
fi

# Run container to build layer
echo "📦 Building layer in Docker container..."
docker run --rm -v "$PWD/layer-output:/output" ccxt-lambda-builder

if [ $? -ne 0 ]; then
    echo "❌ Failed to build layer"
    exit 1
fi

# Check if layer was created
if [ -f "layer-output/ccxt-layer.zip" ]; then
    # Move layer to current directory
    mv layer-output/ccxt-layer.zip ./
    
    # Show layer info
    echo "✅ Layer built successfully!"
    echo "📊 Layer size: $(du -sh ccxt-layer.zip | cut -f1)"
    echo "📁 File: ccxt-layer.zip"
    
    # Clean up
    rm -rf layer-output
    
    echo ""
    echo "🎯 Next steps:"
    echo "1. Upload ccxt-layer.zip to AWS Lambda as a layer"
    echo "2. Set compatible runtime: python3.9"
    echo "3. Set compatible architecture: x86_64"
    echo "4. Add layer to your Lambda function"
    echo "5. Test with lambda_trading_core.py"
    
else
    echo "❌ Layer file not found"
    exit 1
fi
