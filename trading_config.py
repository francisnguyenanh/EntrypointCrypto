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

BINANCE_CONFIG = {
    'apiKey': '51s73pfeptNTANWnjmmdJcdZ5a3Fr3a9Yp57lGic4MW0t3xfdzLssLXxaICxaT7Y',  # Thay bằng API key testnet
    'secret': '3b1aV0Fufo76bxLawFs39y84Z94PJIS8GrNwKanrVNkEwyGKCWSY7hwmHWI3vku6',   # Thay bằng secret testnet
    'sandbox': True,  # PHẢI LÀ True cho testnet
    'enableRateLimit': True,
    'timeout': 30000,
    'options': {
        'defaultType': 'spot',  # spot trading
        'recvWindow': 60000,
    }
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
    'min_order_value': 10,  # Giá trị order tối thiểu (USDT)
    'max_order_value': 5000,  # Giá trị order tối đa (USDT) - Tăng lên cho testnet có nhiều tiền
    
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
    
    # Logging
    'log_trades': True,  # Ghi log các trades
    'log_file': 'trading_log.txt',
    
    # Safety checks
    'max_daily_loss': 0.05,  # Tối đa 5% loss mỗi ngày
    'emergency_stop': False,  # Emergency stop trading
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
    'email_enabled': True,  # TẮT email - Không cần thiết cho testnet
    'email_smtp': 'smtp.gmail.com',
    'email_port': 587,
    'email_user': 'kyoto20200511@gmail.com',
    'email_password': 'nguyenanh231287',  # Không cần thiết khi tắt email
    'email_to': 'onlyone231287@gmail.com',  # Không cần thiết khi tắt email
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
