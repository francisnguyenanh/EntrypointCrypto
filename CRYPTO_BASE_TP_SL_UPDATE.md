# CRYPTO BASE CURRENCY TP/SL CALCULATION UPDATE

## 🎯 VẤN ĐỀ ĐÃ GIẢI QUYẾT:
Khi `base_currency = ETH` hoặc `BTC`, các phần trăm TP/SL được thiết kế cho fiat (JPY) sẽ không phù hợp do:
- **Volatility khác nhau**: Crypto có volatility cao hơn fiat
- **Giá trị tương đối**: 0.4% ETH khác 0.4% JPY về giá trị thực
- **Market dynamics**: Crypto có momentum và reversal patterns khác

## 🔧 GIẢI PHÁP ĐÃ TRIỂN KHAI:

### 1. **Hàm `adjust_tp_sl_for_crypto_base()`** ✅
```python
# Multipliers cho crypto base currencies:
'ETH': tp_multiplier: 1.5, sl_multiplier: 1.2
'BTC': tp_multiplier: 1.8, sl_multiplier: 1.3  
'BNB': tp_multiplier: 1.4, sl_multiplier: 1.15
'USDT/BUSD': tp_multiplier: 1.0 (như fiat)
```

### 2. **Dynamic TP/SL Calculation** ✅
- **Fiat Base (JPY)**: TP 0.4% → 0.4% (không đổi)
- **ETH Base**: TP 0.4% → 0.6% (tăng 50%)
- **BTC Base**: TP 0.4% → 0.72% (tăng 80%)

### 3. **Updated Functions** ✅
- `calculate_dynamic_entry_tp_sl()`: Core TP/SL calculation
- `analyze_scalping_opportunity()`: Scalping TP/SL
- `get_min_order_value_for_base_currency()`: Dynamic minimum values

### 4. **Minimum Order Values** ✅
```python
'JPY': 1500    # ~10 USD
'ETH': 0.005   # ~10-15 USD  
'BTC': 0.0002  # ~10-15 USD
'USDT': 10     # 10 USDT
```

## 📊 VÍ DỤ THỰC TẾ:

### **JPY Base (Cũ)**:
- Entry: 150 JPY
- TP: 150.6 JPY (+0.4%)
- SL: 148.8 JPY (-0.8%)

### **ETH Base (Mới)**:
- Entry: 0.1 ETH  
- TP: 0.1006 ETH (+0.6% thay vì +0.4%)
- SL: 0.0988 ETH (-1.2% thay vì -0.8%)

### **BTC Base (Mới)**:
- Entry: 0.01 BTC
- TP: 0.010072 BTC (+0.72% thay vì +0.4%)
- SL: 0.009870 BTC (-1.3% thay vì -0.8%)

## 🎯 LỢI ÍCH:

1. **Phù hợp với volatility**: Crypto có TP/SL rộng hơn
2. **Risk/Reward tối ưu**: Maintain good R/R ratios
3. **Giảm false signals**: Tránh bị stop loss quá sớm
4. **Tăng profit potential**: Higher TP cho crypto pairs

## 🔄 CẤU HÌNH HIỆN TẠI:
```python
# trading_config.py
base_currency = "ETH"
min_order_value = 0.005  # 0.005 ETH minimum
max_order_value = 0.5    # 0.5 ETH maximum
```

## ✅ KẾT QUẢ:
- **Scalping ETH pairs**: TP từ 0.18% → 0.27%, SL từ 0.12% → 0.144%
- **Swing trading ETH**: TP từ 0.4% → 0.6%, SL từ 0.8% → 0.96%
- **Order values**: Phù hợp với ETH denominated amounts
- **Complete automation**: Chỉ cần đổi base_currency trong config

Bot giờ đây **intelligent** trong việc điều chỉnh TP/SL theo từng loại base_currency! 🚀
