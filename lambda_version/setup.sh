#!/bin/bash

# Setup script cho Lambda version development
# Cài đặt tất cả dependencies cần thiết

echo "🔧 Setting up Lambda development environment..."

# Kiểm tra Python environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider using: python -m venv venv && source venv/bin/activate"
fi

# Install dependencies cho local development
echo "📦 Installing dependencies for local development..."
pip install -r requirements-local.txt

# Test dependencies
echo "🧪 Testing dependencies..."
python test_dependencies.py

echo ""
echo "✅ Setup completed!"
echo ""
echo "📝 Next steps:"
echo "1. Configure AWS credentials: aws configure"
echo "2. Set environment variables in lambda_config.py"
echo "3. Deploy to AWS: ./deploy.sh testnet"
echo ""
echo "🚨 Important notes:"
echo "• boto3 is included in AWS Lambda runtime"
echo "• For production deploy, use requirements.txt (without boto3)"
echo "• For local development, use requirements-local.txt (with boto3)"
