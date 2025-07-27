# 🚀 Hướng Dẫn Setup Auto Trading System

## 📋 BƯỚC 1: Cài đặt API Key Binance Testnet

### 1.1 Tạo Binance Testnet Account
1. Truy cập: https://testnet.binance.vision/
2. Đăng nhập bằng GitHub account
3. Vào **API Management** → **Create API Key**
4. Copy **API Key** và **Secret Key**

### 1.2 Cấu hình API trong file
Mở `trading_config.py` và cập nhật:
```python
BINANCE_CONFIG = {
    'apiKey': 'PASTE_YOUR_TESTNET_API_KEY_HERE',
    'secret': 'PASTE_YOUR_TESTNET_SECRET_KEY_HERE',
    'sandbox': True,  # QUAN TRỌNG: Giữ True cho testnet
    'enableRateLimit': True,
}
```

## 📋 BƯỚC 2: Cấu hình Trading Parameters

### 2.1 Risk Management
```python
TRADING_CONFIG = {
    'enabled': False,  # Đặt True để bật auto trading
    'max_trades': 2,   # Tối đa 2 trades cùng lúc
    'min_order_value': 11.0,  # Tối thiểu $11 USDT
    'risk_per_trade': 0.95,   # 95% cho 1 coin, 47.5% cho 2 coins
}
```

### 2.2 Stop Loss & Take Profit
```python
TRADING_CONFIG = {
    'stop_loss_pct': 0.02,    # Stop loss 2%
    'take_profit_pct': 0.05,  # Take profit 5%
}
```

## 📋 BƯỚC 3: Test Hệ Thống

### 3.1 Chạy Test Script
```bash
python test_trading.py
```

### 3.2 Kiểm tra Output
- ✅ **Binance Connection**: API key và kết nối
- ✅ **Market Data**: Lấy dữ liệu thị trường
- ✅ **Trading Config**: Cấu hình hợp lệ
- ✅ **Price Conversion**: Chuyển đổi JPY → USDT

## 📋 BƯỚC 4: Chạy Auto Trading

### 4.1 Bật Auto Trading
```python
# Trong trading_config.py
TRADING_CONFIG = {
    'enabled': True,  # BẬT AUTO TRADING
}
```

### 4.2 Chạy Phân Tích + Auto Trade
```bash
python app.py
```

## ⚠️ QUAN TRỌNG: Safety Guidelines

### 🔒 Testnet Safety
- ✅ **LUÔN** test trên testnet trước
- ✅ **KIỂM TRA** `sandbox: True` trong config
- ✅ **VERIFY** kết nối testnet trong test script

### 💰 Money Management
- 🎯 **1 coin**: All-in 95% tài khoản
- 🎯 **2 coins**: Chia đôi 47.5% mỗi coin
- 🛡️ **Stop Loss**: 2% tự động
- 🎯 **Take Profit**: 5% tự động

### 📊 Monitoring
- 📱 **Notifications**: Telegram/Email alerts
- 🔍 **Logs**: Chi tiết mọi giao dịch
- 🚨 **Emergency Stop**: Có thể dừng bất cứ lúc nào

## 🛠️ Troubleshooting

### ❌ API Connection Failed
```
Lỗi: Invalid API Key
Giải pháp: Kiểm tra lại API Key trong trading_config.py
```

### ❌ Insufficient Balance
```
Lỗi: Account has insufficient balance
Giải pháp: 
1. Kiểm tra số dư USDT trong testnet
2. Faucet thêm USDT tại https://testnet.binance.vision/
```

### ❌ Order Size Too Small
```
Lỗi: Order size below minimum
Giải pháp: Tăng min_order_value trong TRADING_CONFIG
```

## 📞 Support

### 🐛 Bug Reports
- File: Ghi lại lỗi chi tiết
- Config: Share cấu hình (ẩn API keys)
- Logs: Terminal output

### 💡 Feature Requests
- Strategy: Mô tả chiến lược mong muốn
- Risk: Yêu cầu risk management
- Notification: Loại thông báo cần thiết

---

## 🎯 Quick Start Commands

```bash
# 1. Test hệ thống
python test_trading.py

# 2. Chạy phân tích (no trading)
python app.py

# 3. Bật auto trading và chạy
# (Sửa enabled=True trong trading_config.py trước)
python app.py
```

**🎉 Chúc bạn trading thành công!**
