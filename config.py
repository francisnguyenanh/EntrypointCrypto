# Cấu hình cho EntrypointCrypto

# Cấu hình giao dịch
MIN_WIN_RATE = 50  # Tỷ lệ thắng tối thiểu (%)
MIN_PROFIT_POTENTIAL = 0.3  # Tiềm năng lợi nhuận tối thiểu (%)
TRADING_FEE = 0.001  # Phí giao dịch Binance (0.1%)
STOP_LOSS_PERCENTAGE = 0.3  # Stop loss (%)

# Cấu hình LSTM
LOOK_BACK_PERIOD = 60  # Số ngày nhìn lại cho LSTM
LSTM_EPOCHS = 10  # Số epochs training
LSTM_BATCH_SIZE = 32  # Batch size
TRAIN_TEST_SPLIT = 0.8  # Tỷ lệ train/test

# Cấu hình API
API_DELAY = 1  # Delay giữa các API calls (giây)
DATA_LIMIT = 1000  # Số lượng candles lấy từ API
MIN_DATA_LENGTH = 200  # Số lượng dữ liệu tối thiểu

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

# Cấu hình output
TOP_COINS_COUNT = 3  # Số lượng coin tốt nhất hiển thị
