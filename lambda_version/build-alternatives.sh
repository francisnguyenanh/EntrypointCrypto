#!/bin/bash

# Alternative: Build CCXT layer using AWS CloudShell or EC2
echo "🚀 Building CCXT Layer for AWS Lambda (Alternative method)..."

# Create build script for AWS CloudShell/EC2
cat > build_on_aws.sh << 'EOF'
#!/bin/bash
# Run this script on AWS CloudShell or Amazon Linux EC2

echo "Building CCXT layer on AWS infrastructure..."

# Install required tools
sudo yum update -y
sudo yum install -y zip

# Create directory structure
mkdir -p ccxt-layer-aws/python/lib/python3.9/site-packages

# Install CCXT
pip3.9 install ccxt==4.2.25 -t ccxt-layer-aws/python/lib/python3.9/site-packages/

# Create ZIP package
cd ccxt-layer-aws
zip -r ../ccxt-layer-aws.zip python/

echo "✅ Layer built successfully on AWS!"
echo "Download ccxt-layer-aws.zip and upload as Lambda layer"
EOF

chmod +x build_on_aws.sh

echo "📋 Alternative build methods:"
echo ""
echo "Method 1: Docker (if available)"
echo "./build-ccxt-layer-linux.sh"
echo ""
echo "Method 2: AWS CloudShell"
echo "1. Open AWS CloudShell"
echo "2. Upload build_on_aws.sh"
echo "3. Run: ./build_on_aws.sh"
echo "4. Download ccxt-layer-aws.zip"
echo ""
echo "Method 3: Simplified layer (pure Python)"
echo "./build-ccxt-simple.sh"
