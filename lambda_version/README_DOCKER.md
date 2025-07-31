# 🐳 Docker Build System for AWS Lambda CCXT Layer

## Tại sao dùng Docker?
- AWS Lambda chạy trên Linux x86_64
- Binary dependencies (như cryptography) cần build trên cùng architecture
- Docker đảm bảo layer tương thích 100%

## Files trong hệ thống:
- `Dockerfile`: Môi trường build Linux
- `build-layer.sh`: Script chính build layer
- `lambda_trading_core.py`: Code test layer
- `deploy-layer.sh`: Deploy layer lên AWS

## Sử dụng:
```bash
# Build layer với Docker
./build-layer.sh

# Deploy layer lên AWS
./deploy-layer.sh
```
