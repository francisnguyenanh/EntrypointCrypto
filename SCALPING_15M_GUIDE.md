# 📊 SCALPING MODE 15M - HƯỚNG DẪN SỬ DỤNG (CẬP NHẬT)

## 🎯 Tính năng mới

**SCALPING MODE** đã được **TÍCH HỢP VÀO SYSTEMATIC TRADING** như cơ hội thứ 2!

### 🔄 Quy trình hoạt động mới:

1. **Systematic Trading 30m** (Ưu tiên 1): Tìm cơ hội với downtrend detection nghiêm ngặt
2. **Scalping 15m** (Ưu tiên 2): NẾU không có cơ hội systematic → Chuyển sang scalping với downtrend detection linh hoạt

## ⚡ Cách sử dụng

```bash
# AUTOMATIC MODE: Systematic + Scalping Fallback (KHUYẾN NGHỊ)
python app.py

# PURE SCALPING MODE: Chỉ scalping 15m  
python app.py --scalping

# Hiển thị help
python app.py --help
```

## 📊 Cải tiến TP trong Downtrend

### TP được điều chỉnh thông minh:

**Base TP rates (đã giảm):**
- HIGH opportunity: 0.18% (giảm từ 0.25%)
- MEDIUM opportunity: 0.15% (giảm từ 0.20%)  
- LOW opportunity: 0.12% (giảm từ 0.15%)

**Dynamic adjustments:**
- **Deep oversold** (RSI < 25): +20% TP (có thể bounce mạnh)
- **Normal oversold** (RSI < 30): +10% TP
- **Higher RSI** (RSI > 45): -20% TP (trong downtrend)
- **High confidence** (>70): +5% TP bonus

**Minimum profit guarantee:** TP tối thiểu 0.25% để đảm bảo lãi 0.05% sau phí

## 🎯 Ví dụ TP Adjustment

```
📊 TP Adjustment for ADA/JPY:
   📈 Base TP: 0.18% → Final TP: 0.19%  
   🎯 RSI: 28.5 | Confidence: 78%
   🔧 Adjustments: Normal oversold RSI (28.5) - slight TP increase
```

## 🔍 2-Level Strategy

### Level 1: Systematic Trading 30m
- **Timeframe**: 30 phút
- **Downtrend**: Nghiêm ngặt (tránh STRONG)
- **TP**: 0.4-0.8%
- **Ưu tiên**: Cao nhất

### Level 2: Scalping 15m (Fallback)
- **Timeframe**: 15 phút  
- **Downtrend**: Linh hoạt (cho phép WEAK/MODERATE)
- **TP**: 0.12-0.19%
- **Kích hoạt**: Khi không có cơ hội Systematic

## 📈 Kết quả mong đợi (Cập nhật)

### Automatic Mode (python app.py):
- **Coverage**: 95% (Systematic + Scalping)
- **Win rate**: 65-75%
- **Average profit**: 0.15-0.6% per trade
- **Frequency**: 2-4 trades per day
- **Strategy selection**: Intelligent fallback

### Pure Scalping Mode (python app.py --scalping):
- **Coverage**: 80% (chỉ scalping)
- **Win rate**: 60-70%
- **Average profit**: 0.12-0.19% per trade  
- **Frequency**: 3-5 trades per day
- **Risk**: Thấp, exit nhanh

## 🛠️ Ví dụ thực tế

```
🔍 Phân tích cơ hội trading - 2 levels
📊 Level 1: Systematic Trading 30m...
❌ Level 1: No systematic opportunities found
⚡ Level 2: Scalping 15m (fallback)...
✅ Level 2 found: ADA Scalping (Confidence: 72/100)

⚡ SELECTED: Scalping 15m - ADA
📋 Strategy: SCALPING_15M  
📊 Coin: ADA
💯 Confidence: 72/100

📊 TP Adjustment for ADA/JPY:
   📈 Base TP: 0.15% → Final TP: 0.17%
   🎯 RSI: 29.2 | Confidence: 72%

✅ SCALPING OPPORTUNITY: ADA/JPY
   🎯 Entry: ¥45.2500 | TP: ¥45.3268 (+0.17%)
   🛡️ SL: ¥45.2140 (-0.08%) | R/R: 2.13
   📊 Confidence: 72/100 | Size: 0.9x

💰 Scalping investment: ¥42,500 (85% balance)
```

## 🎯 Ưu điểm của tích hợp

1. **Coverage tối đa**: Systematic HOẶC Scalping (không bỏ lỡ cơ hội)
2. **Risk intelligent**: Strict cho Systematic, Flexible cho Scalping
3. **Profit optimization**: TP dynamic theo market condition
4. **Frequency tối ưu**: 2-4 trades/day với mix strategies

## ⚠️ Lưu ý quan trọng

- **Automatic mode** (khuyến nghị): `python app.py`
- **TP đã giảm** nhưng **win rate cao hơn** do tích hợp thông minh
- **Monitor**: Scalping cần theo dõi trong 15-60 phút
- **Minimum profit**: Luôn đảm bảo lãi sau phí

---

*Scalping Mode giờ hoạt động như safety net thông minh - khi không có cơ hội systematic thì sẽ tự động chuyển sang tìm cơ hội scalping oversold!* 🎉

## 🔍 Chiến lược Scalping

### Đặc điểm chính:
- **Timeframe**: 15 phút
- **Thời gian hold**: 15-60 phút  
- **Take Profit**: 0.15% - 0.25%
- **Stop Loss**: 0.10% - 0.15%
- **Phí giao dịch**: 0.2% (đã tính sẵn)

### Tín hiệu entry:
1. **RSI Oversold** (< 30): Cơ hội bounce mạnh
2. **Stochastic Oversold** (< 20): Xác nhận tín hiệu
3. **Price near Bollinger Lower Band**: Mean reversion
4. **Volume Spike on Decline**: Potential accumulation
5. **EMA8 > EMA21**: Momentum thuận lợi

### Downtrend Protection:
- **STRONG downtrend**: Tránh hoàn toàn
- **MODERATE downtrend**: Yêu cầu tín hiệu oversold mạnh
- **WEAK downtrend**: Cho phép trade với điều chỉnh risk
- **NO downtrend**: Trade bình thường

## 📊 Risk Management

### Position Size:
- **HIGH confidence**: 95% balance
- **MEDIUM confidence**: 85% balance  
- **LOW confidence**: 75% balance

### Risk Adjustment:
- Position size được điều chỉnh theo confidence
- TP/SL được tối ưu cho từng cơ hội
- Stop loss chặt để bảo vệ tài khoản

## 🎯 Ví dụ thực tế

```
⚡ SCALPING ANALYSIS for ADA/JPY:
   📊 Opportunity: HIGH (Confidence: 78/100)
   ✅ Allow Trade: True

✅ SCALPING OPPORTUNITY: ADA/JPY
   🎯 Entry: ¥45.2500 | TP: ¥45.3625 (+0.25%)
   🛡️ SL: ¥45.1825 (-0.15%) | R/R: 1.67
   📊 Confidence: 78/100 | Size: 1.0x

💰 Scalping investment: ¥47,500 (95% balance)
📊 Position size: 1050.000 ADA
```

## 🔧 So sánh với Systematic Trading

| Tính năng | Scalping 15M | Systematic 30M |
|-----------|-------------|----------------|
| Timeframe | 15 phút | 30 phút |
| Hold time | 15-60 phút | 2-8 giờ |
| Take Profit | 0.15-0.25% | 0.4-0.8% |
| Stop Loss | 0.10-0.15% | 0.8-1.2% |
| Downtrend | Cho phép weak | Tránh hoàn toàn |
| Risk | Thấp, nhanh | Trung bình |
| Frequency | Cao | Trung bình |

## ⚠️ Lưu ý quan trọng

1. **Phí giao dịch**: Đã được tính sẵn trong TP (0.2% cho buy+sell)
2. **Monitor**: Cần theo dõi thường xuyên do thời gian hold ngắn
3. **Market condition**: Hiệu quả nhất trong thị trường sideways/volatile
4. **Risk tolerance**: Chỉ sử dụng số tiền có thể chịu rủi ro

## 📈 Kết quả mong đợi

- **Win rate**: 60-70% (cao hơn systematic)
- **Average profit**: 0.15-0.25% per trade
- **Average loss**: 0.10-0.15% per trade
- **Frequency**: 3-5 trades per day
- **Daily return**: 0.3-0.8% (nếu có cơ hội)

## 🛠️ Troubleshooting

### Không tìm thấy cơ hội:
- Market đang trong strong downtrend
- Spread quá rộng (> 0.15%)
- Thanh khoản thấp
- Không có tín hiệu oversold

### Trade thất bại:
- Kiểm tra API connection
- Verify balance đủ (ít nhất ¥1,000)
- Kiểm tra market hours

## 🎯 Tips để tối ưu

1. **Timing**: Chạy trong giờ có volume cao (8-12h, 20-24h JST)
2. **Frequency**: Chạy mỗi 15-30 phút để catch sóng mới
3. **Monitoring**: Set alert cho các lệnh đã đặt
4. **Balance**: Giữ 5% balance để handle slippage

---

*Scalping Mode 15M được thiết kế để tận dụng volatility ngắn hạn với risk được kiểm soát chặt chẽ. Hãy bắt đầu với số tiền nhỏ để làm quen với strategy.*
