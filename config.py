# Cấu hình cho EntrypointCrypto

# Cấu hình giao dịch
MIN_WIN_RATE = 40  # Tỷ lệ thắng tối thiểu (%)
MIN_PROFIT_POTENTIAL = 0.3  # Tiềm năng lợi nhuận tối thiểu (%)
TRADING_FEE = 0.001  # Phí giao dịch Binance (0.1%)
STOP_LOSS_PERCENTAGE = 0.3  # Stop loss (%)

# Cấu hình LSTM
LOOK_BACK_PERIOD = 20  # Số ngày nhìn lại cho LSTM (giảm từ 60 xuống 20)
LSTM_EPOCHS = 5  # Số epochs training (giảm từ 10 xuống 5)
LSTM_BATCH_SIZE = 16  # Batch size (giảm từ 32 xuống 16)
TRAIN_TEST_SPLIT = 0.8  # Tỷ lệ train/test

# Cấu hình API
API_DELAY = 1  # Delay giữa các API calls (giây)
DATA_LIMIT = 5000  # Số lượng candles lấy từ API (tăng để có đủ dữ liệu sau resample)
MIN_DATA_LENGTH = 50  # Số lượng dữ liệu tối thiểu (giảm từ 200 xuống 50)

# Cấu hình validation
MAX_PRICE_PREDICTION_RATIO = 10  # Giá dự đoán không được vượt quá N lần giá hiện tại

# Cấu hình technical indicators
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
SMA_SHORT = 50
SMA_LONG = 200
BB_PERIOD = 20
BB_STD = 2
STOCH_PERIOD = 14

# Cấu hình tối ưu hóa
RSI_BUY_RANGE = [60, 65, 70]
RSI_SELL_RANGE = [30, 35, 40]
VOLATILITY_RANGE = [3, 5, 7]
TAKE_PROFIT_RANGE = [0.003, 0.005, 0.007]

# Cấu hình timeframes
TIMEFRAMES = ['15m', '30m', '1h', '4h']

# Cấu hình sổ lệnh (Order Book)
ORDER_BOOK_DEPTH = 20  # Độ sâu sổ lệnh
BID_ASK_SPREAD_MAX = 0.5  # Spread tối đa giữa bid/ask (%)
SUPPORT_RESISTANCE_PERIOD = 100  # Số candle để tính support/resistance
VOLUME_ANALYSIS_PERIOD = 50  # Số candle để phân tích volume

# Cấu hình timing vào lệnh
ENTRY_CONFIRMATION_CANDLES = 3  # Số candle xác nhận tín hiệu
MIN_VOLUME_INCREASE = 1.5  # Volume tăng tối thiểu so với trung bình
PRICE_ACTION_CONFIRMATION = True  # Xác nhận price action

# Cấu hình output
TOP_COINS_COUNT = 3  # Số lượng coin tốt nhất hiển thị

# Cấu hình tự động điều chỉnh để tìm ít nhất 1 coin
AUTO_ADJUST_ENABLED = True  # Bật tự động điều chỉnh
MIN_COINS_REQUIRED = 1  # Số coin tối thiểu cần tìm thấy
ADJUSTMENT_STEPS = [
    # Bước 1: Giảm win rate xuống 35%
    {'MIN_WIN_RATE': 35, 'MIN_PROFIT_POTENTIAL': 0.3, 'SIGNAL_MODE': 'strict'},
    # Bước 2: Giảm win rate xuống 30% và profit xuống 0.2%
    {'MIN_WIN_RATE': 30, 'MIN_PROFIT_POTENTIAL': 0.2, 'SIGNAL_MODE': 'strict'},
    # Bước 3: Giảm win rate xuống 25% và profit xuống 0.15%
    {'MIN_WIN_RATE': 25, 'MIN_PROFIT_POTENTIAL': 0.15, 'SIGNAL_MODE': 'strict'},
    # Bước 4: Chuyển sang chế độ linh hoạt với win rate 20%
    {'MIN_WIN_RATE': 20, 'MIN_PROFIT_POTENTIAL': 0.1, 'SIGNAL_MODE': 'flexible'},
    # Bước 5: Chế độ linh hoạt với win rate 10%
    {'MIN_WIN_RATE': 10, 'MIN_PROFIT_POTENTIAL': 0.05, 'SIGNAL_MODE': 'flexible'},
    # Bước 6: Chế độ rất linh hoạt - chỉ cần dự đoán LSTM tích cực và win rate > 0%
    {'MIN_WIN_RATE': 0, 'MIN_PROFIT_POTENTIAL': 0.01, 'SIGNAL_MODE': 'lstm_only'},
    # Bước 7: Cuối cùng - chỉ cần có giá và LSTM không null
    {'MIN_WIN_RATE': 0, 'MIN_PROFIT_POTENTIAL': 0.001, 'SIGNAL_MODE': 'emergency'}
]
