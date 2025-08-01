# 💰 TÍNH TOÁN TAKE PROFIT VỚI PHÍ GIAO DỊCH

## 📊 Tóm tắt cấu hình

### Target: 0.4% lợi nhuận ròng
- **Phí giao dịch**: 0.1% mỗi lệnh (mua/bán)
- **Tổng phí**: 0.2% (0.1% mua + 0.1% bán) 
- **Take Profit thực tế**: 0.6% (0.4% lợi nhuận + 0.2% phí)

## 🔢 Công thức tính toán

### 1. Chi phí tổng khi mua:
```
Total Cost = Entry Price + Buy Fee
Buy Fee = Entry Price × 0.1%
```

### 2. Thu nhập khi bán:
```
Net Revenue = TP Price - Sell Fee  
Sell Fee = TP Price × 0.1%
```

### 3. Lợi nhuận ròng:
```
Net Profit = Net Revenue - Total Cost
Net Profit % = (Net Profit / Total Cost) × 100%
```

### 4. TP Price cần thiết:
```
Required TP % = Target Profit % + Total Fees %
TP Price = Entry Price × (1 + Required TP % / 100)
```

## 💡 Ví dụ cụ thể

### Entry Price: ¥100
- **Buy Fee**: ¥100 × 0.1% = ¥0.10
- **Total Cost**: ¥100 + ¥0.10 = ¥100.10
- **TP Price**: ¥100 × (1 + 0.6/100) = ¥100.60
- **Sell Fee**: ¥100.60 × 0.1% = ¥0.1006
- **Net Revenue**: ¥100.60 - ¥0.1006 = ¥100.4994
- **Net Profit**: ¥100.4994 - ¥100.10 = ¥0.3994
- **Net Profit %**: (¥0.3994 / ¥100.10) × 100% = **0.40%** ✅

## ⚙️ Cấu hình trong trading_config.py

```python
TRADING_CONFIG = {
    # Phí giao dịch
    'trading_fee': 0.001,              # 0.1% per transaction
    'total_trading_fees': 0.002,       # 0.2% total (buy + sell)
    
    # Take Profit settings
    'take_profit_percent': 0.4,        # 0.4% net profit target
    'take_profit_with_fees': 0.6,      # 0.6% actual TP (includes fees)
}
```

## 🎯 Kết quả

✅ **Đảm bảo lợi nhuận ròng 0.4%** sau khi trừ toàn bộ phí giao dịch

✅ **Tự động tính toán** dựa trên config - không cần hardcode

✅ **Linh hoạt** - có thể thay đổi target profit và fees dễ dàng

## 📈 Các mức TP khác nhau

| Target Profit | Trading Fees | Required TP | Result |
|---------------|--------------|-------------|---------|
| 0.4% | 0.2% | 0.6% | ✅ Current |
| 0.3% | 0.2% | 0.5% | Tùy chọn |
| 0.5% | 0.2% | 0.7% | Tùy chọn |

Để thay đổi target profit, chỉ cần sửa `take_profit_percent` trong config!
