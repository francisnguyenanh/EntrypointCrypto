# EntrypointCrypto - Dự đoán xu hướng giá Crypto/JPY

## Mô tả
Tool phân tích và dự đoán xu hướng giá các cặp cryptocurrency/JPY trên Binance, sử dụng:
- LSTM (Long Short-Term Memory) để dự đoán giá
- Các chỉ số kỹ thuật (RSI, MACD, SMA, Bollinger Bands, Stochastic)
- VectorBT để tối ưu hóa tham số và tính win rate

## Cài đặt

### 1. Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```

### 2. Cấu hình
Chỉnh sửa file `config.py` để điều chỉnh các tham số:
- `MIN_WIN_RATE`: Tỷ lệ thắng tối thiểu
- `MIN_PROFIT_POTENTIAL`: Tiềm năng lợi nhuận tối thiểu
- `TIMEFRAMES`: Các khung thời gian phân tích
- Các tham số khác...

## Sử dụng

### Chạy phân tích
```bash
python app.py
```

## Tính năng chính

### 1. Dự đoán giá bằng LSTM
- Sử dụng dữ liệu giá 60 ngày gần nhất
- Training model với 10 epochs
- Validation dự đoán hợp lý

### 2. Phân tích kỹ thuật
- **RSI (14)**: Xác định vùng quá mua/quá bán
- **MACD**: Tín hiệu xu hướng
- **SMA 50/200**: Xu hướng dài hạn
- **Bollinger Bands**: Volatility và support/resistance
- **Stochastic**: Momentum

### 3. Tối ưu hóa tham số
- Sử dụng VectorBT để backtest
- Tối ưu hóa RSI, volatility, take-profit
- Ưu tiên win rate cao

### 4. Quản lý rủi ro
- Tính phí giao dịch Binance (0.1%)
- Stop-loss tự động (0.3%)
- Validation dữ liệu

## Kết quả

Tool sẽ hiển thị top 3 coin tốt nhất cho mỗi timeframe với thông tin:
- Giá hiện tại và giá dự đoán
- Tỷ lệ thắng (Win Rate)
- Tiềm năng lợi nhuận
- Các chỉ số kỹ thuật
- Tham số tối ưu

## Cải tiến đã thực hiện

### Error Handling
- ✅ Xử lý exception chi tiết
- ✅ Validation dữ liệu đầu vào
- ✅ Kiểm tra dự đoán hợp lý

### Performance
- ✅ Cấu hình tập trung
- ✅ Logging và progress tracking
- ✅ Tối ưu hóa API calls

### Code Quality
- ✅ Tách config ra file riêng
- ✅ Comments tiếng Việt
- ✅ Validation tham số

## Lưu ý quan trọng

⚠️ **Disclaimer**: Tool này chỉ mang tính chất tham khảo. Đầu tư crypto có rủi ro cao, luôn DYOR (Do Your Own Research) trước khi đầu tư.

## Troubleshooting

### Lỗi phổ biến
1. **Import error**: Đảm bảo đã cài đặt đủ requirements
2. **API error**: Kiểm tra kết nối internet
3. **Memory error**: Giảm `DATA_LIMIT` trong config
4. **No data**: Một số cặp JPY có thể không có đủ dữ liệu

### Performance Tips
- Tăng `API_DELAY` nếu bị rate limit
- Giảm `LSTM_EPOCHS` để chạy nhanh hơn
- Điều chỉnh `MIN_WIN_RATE` phù hợp với thị trường
