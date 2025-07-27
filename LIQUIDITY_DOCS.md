# 💧 Liquidity-Based Order Sizing Documentation

## Tổng quan
Hệ thống này tự động điều chỉnh kích thước lệnh dựa trên thanh khoản thị trường để đảm bảo:
- Không gây tác động lớn đến giá thị trường
- Bảo vệ nhà đầu tư khỏi slippage cao
- Duy trì tính thanh khoản cho thị trường

## Cách hoạt động

### 1. Phân tích Order Book
```python
order_book_analysis = analyze_order_book(order_book)
```
**Thông tin thu thập:**
- `available_liquidity_buy`: Thanh khoản mua (từ bid orders)
- `available_liquidity_sell`: Thanh khoản bán (từ ask orders)
- `total_bid_volume`: Tổng volume bids (top 10)
- `total_ask_volume`: Tổng volume asks (top 10)
- `spread`: Độ chênh lệch bid-ask (%)
- `price_range_buy/sell`: Khoảng giá

### 2. Tính toán Số lượng An toàn
```python
safe_quantity, reason = calculate_max_quantity_from_liquidity(symbol, quantity, analysis, side='buy')
```

**Giới hạn áp dụng:**
- **Liquidity Usage**: Tối đa 15% thanh khoản có sẵn
- **Volume Impact**: Tối đa 10% tổng volume
- **Spread Adjustment**: Giảm size nếu spread > 0.5%

### 3. Đánh giá Tác động Thị trường
```python
market_impact = check_market_impact(symbol, quantity, analysis, side='buy')
```

**Mức độ tác động:**
- **LOW**: Liquidity usage < 8%, Volume impact < 5%
- **MEDIUM**: Liquidity usage 8-15%, Volume impact 5-10%
- **HIGH**: Liquidity usage > 15%, Volume impact > 10%

## Ví dụ thực tế

### Lệnh MUA
```
📊 Liquidity Analysis for BTC/JPY (BUY):
   💧 Available liquidity (sell-side): 2.500000
   📈 Total volume (top 10): 5.000000
   📏 Spread: 0.250%
   🎯 Planned quantity: 1.000000
   ✅ Max safe quantity: 0.375000
   📝 Reason: Liquidity limit (15% of 2.500000)
```

### Lệnh BÁN
```
📊 Liquidity Analysis for BTC/JPY (SELL):
   💧 Available liquidity (buy-side): 1.800000
   📈 Total volume (top 10): 3.600000
   📏 Spread: 0.250%
   🎯 Planned quantity: 1.000000
   ✅ Max safe quantity: 0.270000
   📝 Reason: Liquidity limit (15% of 1.800000)
```

## Tích hợp trong Trading

### Lệnh MUA
```python
# Tự động điều chỉnh quantity
safe_quantity, liquidity_reason = calculate_max_quantity_from_liquidity(
    symbol, quantity, order_book_analysis, side='buy'
)

# Kiểm tra tác động
market_impact = check_market_impact(symbol, safe_quantity, order_book_analysis, side='buy')

# Đặt lệnh với quantity đã điều chỉnh
buy_order = binance.create_market_buy_order(trading_symbol, safe_quantity)
```

### Thông báo
```
✅ MUA BTC/JPY: 0.375000 @ $45,250.00
💧 Liquidity impact: medium
📊 Volume usage: 7.5%
```

## Lợi ích

### 1. Bảo vệ Thanh khoản
- Không "ăn hết" order book
- Giữ thị trường ổn định
- Tránh price impact lớn

### 2. Giảm Slippage
- Lệnh lớn được chia nhỏ tự động
- Giá thực tế gần giá dự kiến
- Chi phí giao dịch thấp hơn

### 3. Risk Management
- Tự động phát hiện thị trường thin
- Cảnh báo spread cao
- Điều chỉnh size theo điều kiện thị trường

## Configuration

### Thông số có thể điều chỉnh:
```python
MAX_LIQUIDITY_USAGE = 0.15     # 15% thanh khoản
MAX_VOLUME_IMPACT = 0.10       # 10% volume
MAX_SPREAD_TOLERANCE = 0.5     # 0.5% spread
```

### Minimum Order Size:
```python
min_order_quantity = 0.001     # Tối thiểu
```

## Testing

Chạy test để kiểm tra:
```bash
python test_liquidity.py
```

**Test cases:**
- Thanh khoản bình thường
- Thanh khoản thấp
- Lệnh cực lớn
- Spread cao
- Cả BUY và SELL

## Warning & Notes

⚠️ **Lưu ý quan trọng:**
1. Hệ thống chỉ sử dụng dữ liệu real-time
2. Order book có thể thay đổi nhanh
3. Không đảm bảo 100% tránh slippage
4. Thích hợp cho giao dịch trung và dài hạn

📈 **Best Practices:**
- Kiểm tra liquidity trước khi trade lớn
- Sử dụng limit orders cho precision cao
- Monitor market impact warnings
- Điều chỉnh parameters theo market conditions

---
*Tính năng này giúp đảm bảo giao dịch không gây tác động tiêu cực đến thị trường và bảo vệ lợi ích của trader.*
