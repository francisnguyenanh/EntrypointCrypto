# Chuyển đổi từ CCXT sang Python-Binance

## Tổng quan thay đổi

Dự án đã được chuyển đổi từ sử dụng thư viện `ccxt` sang `python-binance` để tối ưu hiệu suất và độ ổn định.

## Các thay đổi chính

### 1. Thư viện và Dependencies
- **Trước:** `ccxt`
- **Sau:** `python-binance`
- **File thay đổi:** `requirements.txt`

### 2. Cấu hình API
- **File:** `trading_config.py`
- **Thay đổi:**
  ```python
  # Trước (ccxt format)
  BINANCE_CONFIG = {
      'apiKey': 'your_key',
      'secret': 'your_secret',
      'sandbox': True,
      'enableRateLimit': True
  }
  
  # Sau (python-binance format)
  BINANCE_CONFIG = {
      'api_key': 'your_key',
      'api_secret': 'your_secret',
      'testnet': True
  }
  ```

### 3. Khởi tạo Client
- **Trước:** `binance = ccxt.binance(config)`
- **Sau:** `binance = Client(api_key, api_secret, testnet=True)`

### 4. Định dạng Symbol
- **Trước:** `ADA/JPY`
- **Sau:** `ADAJPY` (không có dấu gạch chéo)

### 5. API Methods

#### Lấy giá hiện tại
```python
# Trước
ticker = binance.fetch_ticker('ADA/JPY')
price = ticker['last']

# Sau  
ticker = binance.get_symbol_ticker(symbol='ADAJPY')
price = float(ticker['price'])
```

#### Lấy số dư tài khoản
```python
# Trước
balance = binance.fetch_balance()
jpy_balance = balance['JPY']['free']

# Sau
account = binance.get_account()
for balance in account['balances']:
    if balance['asset'] == 'JPY':
        jpy_balance = float(balance['free'])
```

#### Đặt lệnh mua
```python
# Trước
order = binance.create_market_buy_order('ADA/JPY', quantity)

# Sau
order = binance.order_market_buy(symbol='ADAJPY', quantity=quantity)
```

#### Đặt lệnh bán
```python
# Trước
order = binance.create_market_sell_order('ADA/JPY', quantity)

# Sau
order = binance.order_market_sell(symbol='ADAJPY', quantity=quantity)
```

#### Kiểm tra trạng thái lệnh
```python
# Trước
order = binance.fetch_order(order_id, 'ADA/JPY')

# Sau
order = binance.get_order(symbol='ADAJPY', orderId=order_id)
```

#### Tạo OCO Order
```python
# Trước
oco_order = binance.create_order(
    symbol='ADA/JPY',
    type='OCO',
    side='sell',
    amount=quantity,
    price=tp_price,
    params={'stopPrice': stop_loss}
)

# Sau
oco_order = binance.create_oco_order(
    symbol='ADAJPY',
    side='SELL',
    quantity=quantity,
    price=str(tp_price),
    stopPrice=str(stop_loss),
    stopLimitPrice=str(stop_loss * 0.999)
)
```

### 6. Xử lý dữ liệu lịch sử
```python
# Trước
ohlcv = binance.fetch_ohlcv('ADA/JPY', '1m', limit=1000)

# Sau
klines = binance.get_historical_klines('ADAJPY', Client.KLINE_INTERVAL_1MINUTE, "1000 minutes ago UTC")
```

### 7. Order Book
```python
# Trước
order_book = binance.fetch_order_book('ADA/JPY', limit=20)

# Sau
order_book_data = binance.get_order_book(symbol='ADAJPY', limit=20)
# Cần convert format để tương thích
```

## Cài đặt

### Tự động
Chạy file batch:
```bash
install_python_binance.bat
```

### Thủ công
```bash
pip uninstall ccxt -y
pip install python-binance
pip install pandas numpy ta scikit-learn glob2
```

## Lưu ý quan trọng

1. **Symbol Format:** Tất cả symbols giờ sử dụng format không có dấu gạch chéo (VD: `ADAJPY` thay vì `ADA/JPY`)

2. **Response Format:** Cấu trúc response từ python-binance khác với ccxt, đã được xử lý conversion

3. **Error Handling:** Thêm xử lý lỗi cụ thể cho `BinanceAPIException` và `BinanceOrderException`

4. **Testnet:** URL testnet không thay đổi: https://testnet.binance.vision/

5. **Rate Limiting:** python-binance tự động xử lý rate limiting

## Kiểm tra hoạt động

1. Kiểm tra kết nối:
```python
account = binance.get_account()
print("✅ Kết nối thành công")
```

2. Test lấy giá:
```python
ticker = binance.get_symbol_ticker(symbol='ADAJPY')
print(f"ADA/JPY: {ticker['price']}")
```

3. Test lấy số dư:
```python
account = binance.get_account()
print("Số dư:", account['balances'])
```

## Troubleshooting

### Lỗi thường gặp:

1. **Import Error:**
   ```
   ImportError: No module named 'binance'
   ```
   **Giải pháp:** Chạy `pip install python-binance`

2. **Symbol Error:**
   ```
   Invalid symbol format
   ```
   **Giải pháp:** Đảm bảo sử dụng format `ADAJPY` thay vì `ADA/JPY`

3. **API Error:**
   ```
   BinanceAPIException: Invalid API key
   ```
   **Giải pháp:** Kiểm tra API key và secret trong `trading_config.py`

## Lợi ích của việc chuyển đổi

1. **Hiệu suất:** python-binance được tối ưu riêng cho Binance
2. **Độ ổn định:** Ít lỗi connection và timeout hơn
3. **Tính năng:** Hỗ trợ đầy đủ các API mới nhất của Binance  
4. **Bảo trì:** Được maintain tích cực bởi cộng đồng Binance
5. **Documentation:** Tài liệu chi tiết và ví dụ cụ thể

## Liên hệ

Nếu gặp vấn đề, vui lòng kiểm tra:
1. File log: `trading_log.txt`
2. Cấu hình API trong `trading_config.py`
3. Kết nối mạng và testnet status
