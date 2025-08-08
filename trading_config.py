# File cấu hình cho Auto Trading
# QUAN TRỌNG: Đây là file cấu hình cho Binance Testnet - AN TOÀN để test

# =============================================================================
# BINANCE API CONFIGURATION (TESTNET)
# =============================================================================
# Để lấy API key testnet:
# 1. Truy cập: https://testnet.binance.vision/
# 2. Đăng ký tài khoản testnet (MIỄN PHÍ)
# 3. Tạo API key và secret
# 4. Thay thế các giá trị dưới đây

# Production config (commented for safety)
# BINANCE_CONFIG = {
#     'api_key': 'your_production_api_key',
#     'api_secret': 'your_production_api_secret',
#     'testnet': False
# }

# Testnet config (SAFE FOR TESTING)
BINANCE_CONFIG = {
    'api_key': 'HL4vtEnEMo3M5Ut5TFXKbj3gbwS9WoU5MFtAwiqUkH6fchlbgbaQpp6dZIQvbg6T',
    'api_secret': 'd2c633SMoBaTjPp9z63fPn6TRcsV9n0yoNOB7iBMvRyNxySNJpBx48l0d5edztFO',
    'testnet': True  # MUST be True for testnet
}

# =============================================================================
# TRADING CONFIGURATION
# =============================================================================
TRADING_CONFIG = {
    # Bật/tắt auto trading
    'enabled': True,  # BẬT cho testnet - AN TOÀN vì dùng tiền ảo
    
    # Quản lý rủi ro
    'max_trades': 2,  # Tối đa 2 trades cùng lúc
    'risk_per_trade': 0.5,  # 50% tài khoản cho mỗi trade khi có 2 coins
    'min_order_value': 1500,  # Giá trị order tối thiểu (JPY) - tương đương 10 USD
    'max_order_value': 750000,  # Giá trị order tối đa (JPY) - tương đương 5000 USD
    
    # Slippage và fees
    'slippage': 0.001,  # 0.1% slippage cho market orders
    'trading_fee': 0.001,  # 0.1% trading fee Binance
    
    # Stop Loss và Take Profit
    'use_oco_orders': True,  # Sử dụng OCO orders (One-Cancels-Other)
    'stop_loss_buffer': 0.005,  # 0.5% buffer cho stop loss
    'take_profit_buffer': 0.002,  # 0.2% buffer cho take profit
    
    # Timeouts
    'order_timeout': 30,  # Timeout cho orders (seconds)
    'price_check_interval': 5,  # Interval kiểm tra giá (seconds)
    
    # Trading and monitoring intervals (seconds)
    'monitor_interval': 300,  # Chu kỳ kiểm tra lệnh và phân tích thị trường (30 giây)
    'error_sleep_interval': 600,  # Thời gian sleep khi lỗi (1 phút)
    
    # Bot operation mode
    'continuous_monitoring': False,  # True: tự động lặp kiểm tra + trading, False: chỉ chạy 1 lần khi user khởi động
    # continuous_monitoring = True:  Bot tự động lặp: Kiểm tra lệnh bán -> Phân tích thị trường -> Đặt lệnh mua -> Sleep order_monitor_interval -> Lặp lại
    # continuous_monitoring = False: Bot chỉ chạy 1 lần: Kiểm tra lệnh bán -> Phân tích thị trường -> Đặt lệnh -> Dừng (user phải khởi động lại để chạy tiếp)
    
    # Logging và cleanup
    'log_trades': True,  # Ghi log các trades
    'log_file': 'trading_log.txt',
    'auto_cleanup_logs': True,  # Tự động dọn dẹp log cũ
    'log_retention_days': 7,  # Xóa log cũ hơn 7 ngày
    'max_log_size_mb': 50,  # Backup log khi vượt quá 50MB
    'cleanup_check_interval': 86400,  # Kiểm tra cleanup mỗi 24 giờ
    
    # System reliability và error handling
    'auto_restart_on_error': True,  # Tự động restart khi có lỗi hệ thống
    'max_error_retries': 3,  # Số lần thử lại tối đa
    'error_retry_delay': 60,  # Delay giữa các lần retry (seconds)
    'send_error_emails': True,  # Gửi email khi có lỗi hệ thống
    'error_email_cooldown': 300,  # Cooldown giữa các email lỗi (5 phút) để tránh spam
    
    # Safety checks
    'max_daily_loss': 0.05,  # Tối đa 5% loss mỗi ngày
    'emergency_stop': False,  # Emergency stop trading
    
    # JPY specific settings
    'base_currency': 'JPY',  # Sử dụng JPY làm base currency
    'jpy_to_usd_rate': 150,  # Tỷ giá JPY/USD để tham khảo (1 USD = 150 JPY)
}

# =============================================================================
# PRICE CONVERSION CONFIGURATION
# =============================================================================
# Không cần chuyển đổi - Trade trực tiếp JPY
# Cấu hình này chỉ để dự phòng

# =============================================================================
# COIN PAIR MAPPING
# =============================================================================
# Trade trực tiếp JPY pairs - Đơn giản và hiệu quả
# Binance hỗ trợ 22 JPY pairs bao gồm: ADA/JPY, BTC/JPY, ETH/JPY, XLM/JPY...

# Không cần mapping - Trade trực tiếp JPY
USE_PAIR_MAPPING = False

# =============================================================================
# NOTIFICATION CONFIGURATION
# =============================================================================
NOTIFICATION_CONFIG = {
    'enabled': True,
    'telegram_enabled': False,  # Bật thông báo Telegram
    'telegram_token': 'YOUR_TELEGRAM_BOT_TOKEN',
    'telegram_chat_id': 'YOUR_TELEGRAM_CHAT_ID',
    'email_enabled': True,  # BẬT email notifications
    'email_smtp_server': 'smtp.gmail.com',  # Sửa tên key
    'email_smtp_port': 587,  # Thêm tên key đúng
    'email_sender': 'tradebotonlyone@gmail.com',  # Sửa tên key
    'email_password': 'lexbgslzxcuamevn',
    'email_recipient': 'onlyone231287@gmail.com',  # Sửa tên key
}

# =============================================================================
# HƯỚNG DẪN SETUP
# =============================================================================
SETUP_INSTRUCTIONS = """
🚀 HƯỚNG DẪN SETUP AUTO TRADING

1. TẠO TÀI KHOẢN TESTNET:
   - Truy cập: https://testnet.binance.vision/
   - Đăng ký tài khoản testnet (MIỄN PHÍ)
   - Đăng nhập và tạo API key

2. CẤU HÌNH API:
   - Vào API Management
   - Tạo API key mới
   - Bật quyền "Spot & Margin Trading"
   - Copy API Key và Secret Key
   - Dán vào BINANCE_CONFIG ở trên

3. TEST TRADING:
   - Đặt TRADING_CONFIG['enabled'] = True
   - Chạy chương trình và kiểm tra
   - Theo dõi orders trên testnet.binance.vision

4. AN TOÀN:
   - LUÔN test trên testnet trước
   - KHÔNG bao giờ chia sẻ API key
   - Kiểm tra cấu hình kỹ trước khi bật
   - Đặt giới hạn rủi ro hợp lý

5. CHUYỂN SANG LIVE:
   - Chỉ khi đã test kỹ trên testnet
   - Đổi sandbox=False
   - Sử dụng API key live
   - Bắt đầu với số tiền nhỏ
"""

if __name__ == "__main__":
    print(SETUP_INSTRUCTIONS)
