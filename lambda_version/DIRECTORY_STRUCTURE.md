# 🧹 Lambda Version Directory - Cleaned Structure

## 📁 Core Files (Docker-based CCXT Layer)
```
📦 lambda_version/
├── 🐳 Dockerfile                     # Docker build environment
├── 🔨 build-layer.sh                 # Build CCXT layer with Docker
├── 🚀 deploy-layer.sh                # Deploy layer to AWS
├── 📋 requirements.txt               # CCXT + dependencies
├── 🧪 lambda_trading_core.py         # Test/debug Lambda function
└── 📖 README_DOCKER.md              # Docker build documentation
```

## 📁 Documentation & Guides
```
├── 📚 README.md                      # Main documentation
├── 🚀 QUICK_START.md                 # Quick start guide
├── 📋 DEPLOYMENT_GUIDE.md            # Deployment instructions
├── 🧪 TESTING_GUIDE.md               # Testing procedures
├── 🔧 TROUBLESHOOTING.md             # Common issues
└── 🏗️  LAMBDA_LAYERS_STRATEGY.md     # Layer strategy
```

## 📁 Lambda Handlers (Examples)
```
├── 🎯 lambda_handler_simple.py       # Basic handler
├── 🎯 lambda_handler_simplified.py   # Simplified version
├── 🎯 lambda_handler_enhanced.py     # Enhanced features
├── 🎯 lambda_handler_full.py         # Full trading bot
├── ⚙️  lambda_config_full.py         # Full configuration
├── 📊 lambda_technical_analysis.py   # Technical analysis
├── 📊 lambda_technical_analysis_simplified.py
└── 🏢 lambda_trading_engine.py       # Trading engine
```

## 📁 Deployment Scripts
```
├── 🚀 deploy_full_bot.sh            # Deploy complete bot
├── 🧪 test_lambda.sh                # Test Lambda functions
├── 🧪 test-full-trading-bot.sh      # Full bot testing
├── 🔄 update-function-with-layer.sh # Update with layer
└── 📁 test_payloads/                # Test JSON payloads
```

## 📁 Templates
```
├── 📄 template.yaml                 # SAM template (full)
├── 📄 template-simple.yaml          # SAM template (simple)
└── 📄 test_payload.json            # Basic test payload
```

## 🎯 Main Workflow
1. **Build**: `./build-layer.sh` - Creates Docker-compatible layer
2. **Deploy**: `./deploy-layer.sh` - Uploads layer to AWS  
3. **Test**: Use `lambda_trading_core.py` with `{"emergency_debug": true}`
4. **Implement**: Choose appropriate handler for your needs

## ✅ Ready to Use
- All build scripts are executable
- Docker-based build ensures Linux compatibility
- Clean structure for easy navigation
