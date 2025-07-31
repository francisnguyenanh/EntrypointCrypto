# 🚀 Hướng Dẫn Deploy CCXT Layer cho AWS Lambda

## 📦 Layer đã tạo thành công
✅ File: `ccxt-layer.zip` (24MB)
✅ Chứa: CCXT 4.2.25 + tất cả dependencies
✅ Compatible với: Python 3.9

## 🎯 Các bước deploy:

### 1. Upload Layer lên AWS Lambda
```bash
# Sử dụng AWS CLI
aws lambda publish-layer-version \
    --layer-name ccxt-trading-layer \
    --description "CCXT Trading Library v4.2.25" \
    --license-info "MIT" \
    --zip-file fileb://ccxt-layer.zip \
    --compatible-runtimes python3.9 \
    --region ap-southeast-2
```

### 2. Hoặc upload qua AWS Console:
1. Mở AWS Lambda Console
2. Đi đến "Layers" 
3. Click "Create layer"
4. Nhập tên: `ccxt-trading-layer`
5. Upload file: `ccxt-layer.zip`
6. Compatible runtimes: `python3.9`
7. Click "Create"

### 3. Thêm layer vào Lambda function:
1. Mở Lambda function của bạn
2. Scroll xuống "Layers"
3. Click "Add a layer"
4. Chọn "Custom layers"
5. Chọn layer vừa tạo: `ccxt-trading-layer`
6. Click "Add"

### 4. Test với code đã có:
```json
{
  "emergency_debug": true
}
```

## ✅ Kết quả mong đợi:
```json
{
  "statusCode": 200,
  "body": {
    "layer_info": {
      "ccxt_found": true,
      "ccxt_import": "✅ SUCCESS: CCXT version 4.2.25"
    }
  }
}
```

## 🔧 Troubleshooting:

### Nếu vẫn lỗi "No module named 'ccxt'":
1. Kiểm tra layer đã được add vào function chưa
2. Kiểm tra compatible runtime (phải là python3.9)
3. Kiểm tra layer order (layer này phải ở đầu danh sách)

### Nếu lỗi timeout:
- Tăng timeout của Lambda function lên 30 giây
- Tăng memory lên 512MB

## 📝 Notes:
- Layer size: 24MB (dưới limit 50MB)
- Chứa đầy đủ CCXT + dependencies
- Không cần layer AWSSDKPandas-Python39 nữa vì đã include pandas
- Ready để deploy full trading bot sau khi test thành công
