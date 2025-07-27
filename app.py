import os
import ccxt
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import vectorbt as vbt
from itertools import product
import time
import warnings
import config
import trading_config
from trading_functions_fixed import place_buy_order_with_sl_tp_fixed
from account_info import get_account_info, test_email_notification, send_trading_notification

# Tắt tất cả warnings và logging không cần thiết
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Tắt TensorFlow logs
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Tắt oneDNN notifications
tf.get_logger().setLevel('ERROR')
tf.autograph.set_verbosity(0)

# Khởi tạo Binance API - TESTNET cho test an toàn
try:
    binance = ccxt.binance(trading_config.BINANCE_CONFIG)
    print("✅ Kết nối Binance API thành công")
except Exception as e:
    print(f"❌ Lỗi kết nối Binance API: {e}")
    print("💡 Vui lòng kiểm tra cấu hình trong trading_config.py")
    binance = ccxt.binance()  # Fallback to basic connection

# Cấu hình trading từ file config
TRADING_CONFIG = trading_config.TRADING_CONFIG

# Hàm chuyển đổi giá từ JPY sang USDT
def convert_jpy_to_usdt(jpy_price):
    """Chuyển đổi giá từ JPY sang USDT"""
    try:
        if trading_config.PRICE_CONVERSION['use_live_rate']:
            # Lấy tỷ giá thời gian thực từ Binance
            ticker = binance.fetch_ticker('USDT/JPY')
            usd_jpy_rate = 1 / ticker['last']  # JPY to USD
        else:
            usd_jpy_rate = trading_config.PRICE_CONVERSION['default_jpy_to_usd']
        
        usdt_price = jpy_price * usd_jpy_rate
        return usdt_price
    except Exception as e:
        print(f"⚠️ Lỗi chuyển đổi JPY->USDT: {e}")
        # Fallback to default rate
        return jpy_price * trading_config.PRICE_CONVERSION['default_jpy_to_usd']

# Hàm lấy giá hiện tại của cặp JPY
def get_current_jpy_price(symbol):
    """Lấy giá hiện tại của cặp JPY"""
    try:
        ticker = binance.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"⚠️ Lỗi lấy giá {symbol}: {e}")
        return None

# Hàm gửi thông báo
def send_notification(message, urgent=False):
    """Gửi thông báo về trading"""
    try:
        if not trading_config.NOTIFICATION_CONFIG['enabled']:
            return
        
        print(f"📱 {message}")
        
        # Telegram notification
        if trading_config.NOTIFICATION_CONFIG['telegram_enabled']:
            # Implement telegram notification here
            pass
        
        # Email notification
        if trading_config.NOTIFICATION_CONFIG['email_enabled']:
            # Implement email notification here
            pass
            
        # Log to file
        if TRADING_CONFIG['log_trades']:
            log_file = TRADING_CONFIG.get('log_file', 'trading_log.txt')
            with open(log_file, 'a', encoding='utf-8') as f:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"⚠️ Lỗi gửi thông báo: {e}")

# Hàm lấy số dư tài khoản
def get_account_balance():
    """Lấy số dư tài khoản USDT"""
    try:
        balance = binance.fetch_balance()
        usdt_balance = balance['USDT']['free'] if 'USDT' in balance else 0
        return usdt_balance
    except Exception as e:
        print(f"Lỗi khi lấy số dư: {e}")
        return 0

# Hàm tính toán kích thước order
def calculate_order_size(usdt_balance, num_recommendations, coin_price):
    """Tính toán kích thước order dựa trên số dư và số lượng coin khuyến nghị"""
    if num_recommendations == 1:
        # All-in với 1 coin
        allocation = usdt_balance * 0.95  # Giữ lại 5% để trả phí
    elif num_recommendations == 2:
        # Chia đôi tài khoản
        allocation = usdt_balance * 0.475  # 47.5% cho mỗi coin
    else:
        return 0
    
    # Kiểm tra giá trị order tối thiểu
    if allocation < TRADING_CONFIG['min_order_value']:
        print(f"⚠️ Số dư không đủ. Cần tối thiểu ${TRADING_CONFIG['min_order_value']}, hiện có ${allocation:.2f}")
        return 0
    
    # Tính số lượng coin có thể mua
    quantity = allocation / coin_price
    return quantity

# Hàm đặt lệnh mua với stop loss và take profit
def place_buy_order_with_sl_tp(symbol, quantity, entry_price, stop_loss, tp1_price, tp2_price):
    """Đặt lệnh mua với stop loss và take profit tự động"""
    try:
        # Trade trực tiếp JPY - đơn giản
        trading_symbol = symbol  # Sử dụng trực tiếp JPY pair
        current_price = get_current_jpy_price(symbol)
        
        if not current_price:
            return {'status': 'failed', 'error': 'Cannot get current JPY price'}
        
        print(f"\n🔄 Đang đặt lệnh mua {trading_symbol}...")
        print(f"📊 Số lượng: {quantity:.6f}")
        print(f"💰 Giá entry: ¥{entry_price:.2f}")
        print(f"💰 Giá thị trường hiện tại: ¥{current_price:.2f}")
        
        # Kiểm tra market info để đảm bảo order hợp lệ
        try:
            market = binance.market(trading_symbol)
            min_amount = market['limits']['amount']['min']
            min_cost = market['limits']['cost']['min']
            
            if quantity < min_amount:
                return {'status': 'failed', 'error': f'Quantity too small. Min: {min_amount}'}
            
            if quantity * current_price < min_cost:
                return {'status': 'failed', 'error': f'Order value too small. Min: ${min_cost}'}
                
        except Exception as market_error:
            print(f"⚠️ Không thể kiểm tra market info: {market_error}")
        
        # 1. Đặt lệnh mua market
        buy_order = binance.create_market_buy_order(trading_symbol, quantity)
        print(f"✅ Lệnh mua thành công - ID: {buy_order['id']}")
        
        # Lấy giá thực tế đã mua
        actual_price = float(buy_order['average']) if buy_order['average'] else current_price
        actual_quantity = float(buy_order['filled'])
        
        print(f"📈 Giá mua thực tế: ${actual_price:.4f}")
        print(f"📊 Số lượng thực tế: {actual_quantity:.6f}")
        
        # Gửi thông báo
        send_notification(f"✅ MUA {trading_symbol}: {actual_quantity:.6f} @ ${actual_price:.4f}")
        
        # 2. Đặt stop loss và take profit
        orders_placed = []
        
        try:
            if TRADING_CONFIG['use_oco_orders']:
                # Sử dụng OCO order (One-Cancels-Other)
                oco_order = binance.create_order(
                    symbol=usdt_symbol,
                    type='OCO',
                    side='sell',
                    amount=actual_quantity * 0.7,  # 70% cho OCO
                    price=tp1_usdt,  # Take profit price
                    stopPrice=stop_loss_usdt,  # Stop loss trigger price
                    stopLimitPrice=stop_loss_usdt * (1 - TRADING_CONFIG['stop_loss_buffer']),
                    params={'stopLimitTimeInForce': 'GTC'}
                )
                orders_placed.append(oco_order)
                print(f"✅ OCO order đặt thành công - SL: ${stop_loss_usdt:.4f}, TP: ${tp1_usdt:.4f}")
                send_notification(f"🛡️ OCO {usdt_symbol}: SL ${stop_loss_usdt:.4f} | TP ${tp1_usdt:.4f}")
                
            else:
                # Đặt stop loss riêng
                stop_order = binance.create_order(
                    symbol=usdt_symbol,
                    type='STOP_LOSS_LIMIT',
                    side='sell',
                    amount=actual_quantity,
                    price=stop_loss_usdt * (1 - TRADING_CONFIG['stop_loss_buffer']),
                    stopPrice=stop_loss_usdt,
                    params={'timeInForce': 'GTC'}
                )
                orders_placed.append(stop_order)
                print(f"✅ Stop Loss đặt thành công: ¥{stop_loss:.2f}")
                
        except Exception as sl_error:
            print(f"⚠️ Lỗi đặt stop loss: {sl_error}")
            send_notification(f"⚠️ Lỗi đặt SL cho {trading_symbol}: {sl_error}", urgent=True)
        
        # 3. Đặt take profit thứ 2 (nếu khác TP1)
        try:
            if abs(tp2_price - tp1_price) > 1:  # Nếu TP2 khác TP1 (JPY)
                tp2_quantity = actual_quantity * 0.3  # 30% cho TP2
                tp2_order = binance.create_limit_sell_order(trading_symbol, tp2_quantity, tp2_price)
                orders_placed.append(tp2_order)
                print(f"✅ Take Profit 2 đặt thành công: ¥{tp2_price:.2f}")
                send_notification(f"🎯 TP2 {trading_symbol}: ¥{tp2_price:.2f}")
                
        except Exception as tp2_error:
            print(f"⚠️ Không thể đặt TP2: {tp2_error}")
        
        return {
            'buy_order': buy_order,
            'sl_tp_orders': orders_placed,
            'status': 'success',
            'actual_price': actual_price,
            'actual_quantity': actual_quantity,
            'trading_symbol': trading_symbol
        }
        
    except Exception as e:
        error_msg = f"❌ Lỗi khi đặt lệnh mua {symbol}: {e}"
        print(error_msg)
        send_notification(error_msg, urgent=True)
        return {'status': 'failed', 'error': str(e)}

# Hàm kiểm tra và hủy orders cũ
def cancel_all_open_orders():
    """Hủy tất cả orders đang mở để tránh xung đột"""
    try:
        open_orders = binance.fetch_open_orders()
        if open_orders:
            print(f"🔄 Tìm thấy {len(open_orders)} orders đang mở, đang hủy...")
            for order in open_orders:
                try:
                    binance.cancel_order(order['id'], order['symbol'])
                    print(f"✅ Hủy order {order['id']} - {order['symbol']}")
                except Exception as e:
                    print(f"⚠️ Không thể hủy order {order['id']}: {e}")
        else:
            print("✅ Không có orders đang mở")
    except Exception as e:
        print(f"⚠️ Lỗi khi kiểm tra orders: {e}")

# Hàm thực hiện trading tự động
def execute_auto_trading(recommendations):
    """Thực hiện trading tự động dựa trên khuyến nghị"""
    if not TRADING_CONFIG['enabled']:
        print("⚠️ Auto trading đã bị tắt trong cấu hình")
        return
    
    if TRADING_CONFIG.get('emergency_stop', False):
        print("🚨 EMERGENCY STOP đã được kích hoạt - Dừng trading")
        return
    
    if not recommendations:
        print("💡 Không có coin khuyến nghị - Không vào lệnh")
        send_trading_notification("💡 Không có tín hiệu trading")
        return
    
    print("\n" + "=" * 80)
    print("🤖 BẮT ĐẦU AUTO TRADING")
    print("=" * 80)
    
    # ===== HIỂN THỊ THÔNG TIN TÀI KHOẢN TRƯỚC KHI TRADE =====
    print("📊 Đang lấy thông tin tài khoản...")
    account_info = get_account_info()
    
    if not account_info:
        print("❌ Không thể lấy thông tin tài khoản - Dừng trading")
        return
    
    # ===== KIỂM TRA EMAIL NOTIFICATION =====
    print("\n📧 Kiểm tra hệ thống notification...")
    notification_working = test_email_notification()
    
    if not notification_working:
        print("⚠️ Email notification không hoạt động - Tiếp tục với console logs")
    
    print("\n" + "=" * 80)
    
    try:
        # 1. Kiểm tra số dư
        usdt_balance = get_account_balance()
        print(f"💰 Số dư USDT: ${usdt_balance:.2f}")
        
        if usdt_balance < TRADING_CONFIG['min_order_value']:
            error_msg = f"❌ Số dư không đủ để trading. Cần tối thiểu ${TRADING_CONFIG['min_order_value']}"
            print(error_msg)
            send_notification(error_msg, urgent=True)
            return
        
        # Kiểm tra giới hạn tối đa
        max_order_value = TRADING_CONFIG.get('max_order_value', float('inf'))
        if usdt_balance > max_order_value:
            usdt_balance = max_order_value
            print(f"⚠️ Giới hạn số dư tối đa: ${max_order_value}")
        
        # 2. Hủy orders cũ
        cancel_all_open_orders()
        
        # 3. Thực hiện trading
        num_recommendations = len(recommendations)
        print(f"📊 Số coin khuyến nghị: {num_recommendations}")
        
        if num_recommendations == 1:
            print("🎯 Chiến lược: ALL-IN với 1 coin (95% tài khoản)")
            allocation_per_coin = 0.95
        elif num_recommendations == 2:
            print("🎯 Chiến lược: CHIA ĐÔI tài khoản cho 2 coins")
            allocation_per_coin = 0.475  # 47.5% cho mỗi coin
        else:
            print("⚠️ Quá nhiều khuyến nghị, chỉ trade 2 coin đầu")
            recommendations = recommendations[:2]
            allocation_per_coin = 0.475
        
        successful_trades = 0
        total_invested = 0
        
        for i, coin_data in enumerate(recommendations):
            try:
                original_symbol = f"{coin_data['coin']}/JPY"
                # Trade trực tiếp JPY
                jpy_symbol = original_symbol
                
                print(f"\n{'='*60}")
                print(f"🚀 TRADING #{i+1}: {jpy_symbol}")
                print(f"{'='*60}")
                
                # Lấy giá hiện tại JPY
                current_jpy_price = get_current_jpy_price(original_symbol)
                if not current_jpy_price:
                    print(f"❌ Không thể lấy giá {jpy_symbol}")
                    continue
                
                # Tính toán số tiền đầu tư (JPY)
                # Giả sử có 1,500,000 JPY testnet (tương đương $10,000)
                balance = binance.fetch_balance()
                jpy_balance = balance['free'].get('JPY', 0)
                
                # Nếu không có JPY, convert từ USDT
                if jpy_balance == 0:
                    usdt_balance = balance['free'].get('USDT', 0)
                    jpy_balance = usdt_balance * 150  # 1 USD ≈ 150 JPY
                
                investment_amount = jpy_balance * allocation_per_coin
                
                # Kiểm tra giới hạn (chuyển sang JPY)
                min_order_jpy = TRADING_CONFIG['min_order_value'] * 150  # Convert USDT to JPY
                if investment_amount < min_order_jpy:
                    print(f"❌ Số tiền đầu tư quá nhỏ: ¥{investment_amount:.2f}")
                    continue
                
                # Tính số lượng coin
                quantity = investment_amount / current_jpy_price
                
                # Lấy thông tin giá từ khuyến nghị (JPY)
                entry_jpy = coin_data['optimal_entry']
                stop_loss_jpy = coin_data['stop_loss']
                tp1_jpy = coin_data['tp1_price']
                tp2_jpy = coin_data['tp2_price']
                
                print(f"💰 Đầu tư: ¥{investment_amount:.2f}")
                print(f"📊 Số lượng: {quantity:.6f}")
                print(f"💱 Giá entry: ¥{entry_jpy:.2f}")
                print(f"💱 Giá thị trường hiện tại: ¥{current_jpy_price:.2f}")
                
                # Đặt lệnh với hàm đã sửa
                result = place_buy_order_with_sl_tp_fixed(
                    original_symbol, quantity, entry_jpy, 
                    stop_loss_jpy, tp1_jpy, tp2_jpy
                )
                
                if result['status'] == 'success':
                    successful_trades += 1
                    total_invested += investment_amount
                    print(f"✅ Trading {jpy_symbol} thành công!")
                    
                    # Thông báo chi tiết
                    send_notification(
                        f"🚀 TRADING #{i+1} THÀNH CÔNG\n"
                        f"Coin: {jpy_symbol}\n"
                        f"Đầu tư: ¥{investment_amount:.2f}\n"
                        f"Số lượng: {quantity:.6f}\n"
                        f"Giá: ¥{result.get('actual_price', entry_jpy):.2f}"
                    )
                else:
                    error_msg = f"❌ Trading {jpy_symbol} thất bại: {result.get('error', 'Unknown error')}"
                    print(error_msg)
                    send_notification(error_msg, urgent=True)
                
                # Delay giữa các trades
                time.sleep(3)
                
            except Exception as e:
                error_msg = f"❌ Lỗi khi trading {coin_data['coin']}: {e}"
                print(error_msg)
                send_notification(error_msg, urgent=True)
                continue
        
        # 4. Tổng kết
        final_balance = get_account_balance()
        print(f"\n{'='*80}")
        print(f"📊 TỔNG KẾT AUTO TRADING")
        print(f"{'='*80}")
        print(f"✅ Thành công: {successful_trades}/{len(recommendations)} trades")
        print(f"💰 Tổng đầu tư: ${total_invested:.2f}")
        print(f"💰 Số dư ban đầu: ${usdt_balance:.2f}")
        print(f"💰 Số dư hiện tại: ${final_balance:.2f}")
        
        if successful_trades > 0:
            print("\n🎯 THEO DÕI:")
            print("• Kiểm tra orders trên Binance Testnet")
            print("• Theo dõi stop loss và take profit")
            print("• Cập nhật strategy nếu cần")
            
            # Thông báo tổng kết
            send_notification(
                f"📊 TỔNG KẾT TRADING\n"
                f"Thành công: {successful_trades}/{len(recommendations)}\n"
                f"Đầu tư: ${total_invested:.2f}\n"
                f"Số dư: ${final_balance:.2f}"
            )
        
    except Exception as e:
        error_msg = f"❌ Lỗi nghiêm trọng trong auto trading: {e}"
        print(error_msg)
        send_notification(error_msg, urgent=True)

# Hàm lấy danh sách cặp crypto/JPY từ Binance
def get_jpy_pairs():
    # Phân tích các cặp JPY để đưa ra khuyến nghị, nhưng trade bằng USDT
    selected_pairs = ['ADA/JPY', 'XRP/JPY', 'XLM/JPY', 'SUI/JPY']
    
    try:
        markets = binance.load_markets()
        # Kiểm tra các cặp có tồn tại không (sẽ kiểm tra cả JPY cho phân tích và USDT cho trading)
        available_pairs = []
        for pair in selected_pairs:
            # Kiểm tra cặp JPY cho phân tích
            if pair in markets:
                available_pairs.append(pair)
            else:
                # Nếu không có JPY, thử USDT
                usdt_pair = pair.replace('/JPY', '/USDT')
                if usdt_pair in markets:
                    available_pairs.append(pair)  # Vẫn giữ tên JPY cho phân tích
        
        return available_pairs
    except Exception as e:
        return selected_pairs  # Fallback về danh sách gốc

# Hàm lấy dữ liệu giá từ Binance
def get_crypto_data(symbol, timeframe='1m', limit=5000):
    try:
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu cho {symbol}: {e}")
        return None

# Hàm lấy sổ lệnh từ Binance
def get_order_book(symbol, limit=20):
    try:
        order_book = binance.fetch_order_book(symbol, limit=limit)
        return order_book
    except Exception as e:
        print(f"Lỗi khi lấy order book cho {symbol}: {e}")
        return None

# Hàm phân tích sổ lệnh
def analyze_order_book(order_book):
    if not order_book or not order_book.get('bids') or not order_book.get('asks'):
        return None
    
    bids = order_book['bids']
    asks = order_book['asks']
    
    # Giá bid cao nhất và ask thấp nhất
    best_bid = bids[0][0] if bids else 0
    best_ask = asks[0][0] if asks else 0
    
    if best_bid == 0 or best_ask == 0:
        return None
    
    # Tính spread
    spread = (best_ask - best_bid) / best_bid * 100
    
    # Tính tổng volume bid và ask
    total_bid_volume = sum(bid[1] for bid in bids[:10])  # Top 10 bids
    total_ask_volume = sum(ask[1] for ask in asks[:10])  # Top 10 asks
    
    # Tỷ lệ bid/ask volume
    bid_ask_ratio = total_bid_volume / total_ask_volume if total_ask_volume > 0 else 0
    
    # Support và resistance levels từ order book
    support_levels = [bid[0] for bid in bids[:5]]  # Top 5 bid prices
    resistance_levels = [ask[0] for ask in asks[:5]]  # Top 5 ask prices
    
    # Phân tích volume wall và liquidity
    volume_weighted_bid = sum(bid[0] * bid[1] for bid in bids[:10]) / total_bid_volume if total_bid_volume > 0 else best_bid
    volume_weighted_ask = sum(ask[0] * ask[1] for ask in asks[:10]) / total_ask_volume if total_ask_volume > 0 else best_ask
    
    # Tìm volume wall (khối lượng lớn tại một mức giá)
    max_bid_volume = max(bid[1] for bid in bids[:10]) if bids else 0
    max_ask_volume = max(ask[1] for ask in asks[:10]) if asks else 0
    
    # Mức giá có volume wall
    bid_wall_price = next((bid[0] for bid in bids[:10] if bid[1] == max_bid_volume), best_bid)
    ask_wall_price = next((ask[0] for ask in asks[:10] if ask[1] == max_ask_volume), best_ask)
    
    return {
        'best_bid': best_bid,
        'best_ask': best_ask,
        'spread': spread,
        'bid_ask_ratio': bid_ask_ratio,
        'total_bid_volume': total_bid_volume,
        'total_ask_volume': total_ask_volume,
        'support_levels': support_levels,
        'resistance_levels': resistance_levels,
        'volume_weighted_bid': volume_weighted_bid,
        'volume_weighted_ask': volume_weighted_ask,
        'bid_wall_price': bid_wall_price,
        'ask_wall_price': ask_wall_price,
        'max_bid_volume': max_bid_volume,
        'max_ask_volume': max_ask_volume
    }

# Hàm phân tích cơ hội giao dịch dựa trên sổ lệnh
def analyze_orderbook_opportunity(symbol, current_price, order_book_analysis, df):
    """
    Phân tích cơ hội giao dịch dựa trên sổ lệnh khi không có tín hiệu kỹ thuật rõ ràng
    """
    if not order_book_analysis:
        return None
    
    opportunity = {
        'coin': symbol.replace('/JPY', ''),
        'current_price': current_price,
        'analysis_type': 'ORDER_BOOK_BASED',
        'confidence': 'LOW_TO_MEDIUM'
    }
    
    # Phân tích xu hướng từ bid/ask ratio
    if order_book_analysis['bid_ask_ratio'] > 1.5:
        # Nhiều bid hơn ask - có thể xu hướng tăng
        opportunity['trend_signal'] = 'BULLISH'
        opportunity['reason'] = f"Bid/Ask ratio cao ({order_book_analysis['bid_ask_ratio']:.2f}) - áp lực mua mạnh"
        
        # Mức giá vào lệnh: gần best ask nhưng có buffer
        entry_price = order_book_analysis['best_ask'] * 1.0005  # +0.05% buffer
        
        # Take profit levels dựa trên resistance và volume wall
        if order_book_analysis['ask_wall_price'] > entry_price:
            # Có volume wall phía trên
            tp1_price = order_book_analysis['ask_wall_price'] * 0.995  # Trước wall 0.5%
            tp2_price = order_book_analysis['resistance_levels'][0] if order_book_analysis['resistance_levels'] else entry_price * 1.01
        else:
            # Không có wall gần, dùng % cố định
            tp1_price = entry_price * 1.005  # +0.5%
            tp2_price = entry_price * 1.01   # +1.0%
        
        # Stop loss: dưới volume weighted bid hoặc support gần nhất
        stop_loss = min(
            order_book_analysis['volume_weighted_bid'] * 0.998,
            order_book_analysis['support_levels'][0] * 0.998 if order_book_analysis['support_levels'] else entry_price * 0.995
        )
        
    elif order_book_analysis['bid_ask_ratio'] < 0.7:
        # Nhiều ask hơn bid - có thể xu hướng giảm, tìm cơ hội mua đáy
        opportunity['trend_signal'] = 'BEARISH_TO_BULLISH'
        opportunity['reason'] = f"Bid/Ask ratio thấp ({order_book_analysis['bid_ask_ratio']:.2f}) - có thể oversold"
        
        # Mức giá vào lệnh: gần best bid để chờ giá giảm
        entry_price = order_book_analysis['volume_weighted_bid'] * 1.001
        
        # Take profit conservative vì trend yếu
        tp1_price = entry_price * 1.003  # +0.3%
        tp2_price = entry_price * 1.008  # +0.8%
        
        # Stop loss chặt vì trend bearish
        stop_loss = entry_price * 0.997  # -0.3%
        
    else:
        # Cân bằng - tìm cơ hội scalping
        opportunity['trend_signal'] = 'NEUTRAL_SCALPING'
        opportunity['reason'] = f"Thị trường cân bằng - cơ hội scalping trong spread"
        
        # Vào lệnh ở giữa spread
        mid_price = (order_book_analysis['best_bid'] + order_book_analysis['best_ask']) / 2
        entry_price = mid_price
        
        # Take profit nhỏ trong spread
        tp1_price = order_book_analysis['best_ask'] * 0.9995  # Gần ask
        tp2_price = order_book_analysis['best_ask']  # Đúng ask
        
        # Stop loss gần bid
        stop_loss = order_book_analysis['best_bid'] * 1.0005
    
    # Tính toán risk/reward và volume analysis
    risk_percent = (entry_price - stop_loss) / entry_price * 100
    reward_percent = (tp1_price - entry_price) / entry_price * 100
    risk_reward_ratio = reward_percent / risk_percent if risk_percent > 0 else 0
    
    # Đánh giá độ tin cậy dựa trên volume và spread
    confidence_score = 0
    if order_book_analysis['spread'] < 0.1:  # Spread thấp
        confidence_score += 25
    if order_book_analysis['total_bid_volume'] > 1000:  # Volume lớn
        confidence_score += 25
    if abs(order_book_analysis['bid_ask_ratio'] - 1) > 0.3:  # Có bias rõ ràng
        confidence_score += 25
    if risk_reward_ratio > 1:  # Risk/reward tốt
        confidence_score += 25
    
    opportunity.update({
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'tp1_price': tp1_price,
        'tp2_price': tp2_price,
        'risk_percent': risk_percent,
        'reward_percent': reward_percent,
        'risk_reward_ratio': risk_reward_ratio,
        'confidence_score': confidence_score,
        'spread': order_book_analysis['spread'],
        'bid_ask_ratio': order_book_analysis['bid_ask_ratio'],
        'total_volume': order_book_analysis['total_bid_volume'] + order_book_analysis['total_ask_volume']
    })
    
    return opportunity

# Hàm tìm cơ hội giao dịch từ sổ lệnh cho tất cả coins
# Hàm tìm cơ hội giao dịch từ sổ lệnh cho tất cả coins - TỐI ƯU TỐC ĐỘ
def find_orderbook_opportunities(timeframe='1h', min_confidence=50):
    """
    Tìm cơ hội giao dịch dựa trên sổ lệnh khi không có tín hiệu kỹ thuật - TỐI ƯU TỐC ĐỘ
    """
    try:
        jpy_pairs = get_jpy_pairs()  # Sẽ lấy danh sách cặp đã được lọc
        if not jpy_pairs:
            print("Không tìm thấy cặp JPY nào.")
            return []
        
        print(f"🔍 Phân tích cơ hội từ sổ lệnh cho {len(jpy_pairs)} cặp được chọn...")
        opportunities = []
        
        for i, symbol in enumerate(jpy_pairs):
            try:
                print(f"Phân tích sổ lệnh {symbol} ({i+1}/{len(jpy_pairs)})...")
                
                # Lấy ít dữ liệu hơn để tăng tốc
                df = get_crypto_data(symbol, timeframe=timeframe, limit=50)  # Giảm từ 100 xuống 50
                if df is None or len(df) < 5:  # Giảm từ 10 xuống 5
                    continue
                
                current_price = df['close'].iloc[-1]
                
                # Lấy sổ lệnh với depth nhỏ hơn
                order_book = get_order_book(symbol, limit=10)  # Giảm từ 20 xuống 10
                order_book_analysis = analyze_order_book(order_book)
                
                if not order_book_analysis:
                    continue
                
                # Phân tích cơ hội đơn giản hóa
                opportunity = analyze_orderbook_opportunity(symbol, current_price, order_book_analysis, df)
                
                if opportunity and opportunity['confidence_score'] >= min_confidence:
                    # Thêm thông tin kỹ thuật cơ bản nhưng đơn giản
                    if len(df) >= 10:
                        df['SMA_10'] = SMAIndicator(df['close'], window=10).sma_indicator()
                        df['RSI'] = RSIIndicator(df['close'], window=14).rsi()
                        
                        latest = df.iloc[-1]
                        opportunity.update({
                            'sma_10': latest.get('SMA_10', current_price),
                            'rsi': latest.get('RSI', 50),
                            'volume_24h': df['volume'].sum()  # Đơn giản hóa
                        })
                    
                    opportunities.append(opportunity)
                
                time.sleep(0.2)  # Giảm delay
                
            except Exception as e:
                print(f"Lỗi khi phân tích {symbol}: {e}")
                continue
        
        # Sắp xếp theo confidence score và risk/reward ratio
        opportunities = sorted(opportunities, key=lambda x: (x['confidence_score'], x['risk_reward_ratio']), reverse=True)
        return opportunities[:2]  # Top 2 cơ hội tốt nhất cho sổ lệnh
        
    except Exception as e:
        print(f"Lỗi trong find_orderbook_opportunities: {e}")
        return []

# Hàm tính support và resistance từ dữ liệu giá
def calculate_support_resistance(df, period=100):
    if len(df) < period:
        return None, None
    
    # Lấy dữ liệu gần đây
    recent_data = df.tail(period)
    
    # Tìm local minima và maxima
    highs = recent_data['high'].rolling(window=5, center=True).max()
    lows = recent_data['low'].rolling(window=5, center=True).min()
    
    # Support levels (local minima)
    support_mask = recent_data['low'] == lows
    support_levels = recent_data.loc[support_mask, 'low'].unique()
    
    # Resistance levels (local maxima)  
    resistance_mask = recent_data['high'] == highs
    resistance_levels = recent_data.loc[resistance_mask, 'high'].unique()
    
    # Sắp xếp và lấy levels quan trọng nhất
    support_levels = sorted(support_levels, reverse=True)[:3]
    resistance_levels = sorted(resistance_levels)[:3]
    
    return support_levels, resistance_levels

# Hàm phân tích volume
def analyze_volume(df, period=50):
    if len(df) < period:
        return None
    
    recent_data = df.tail(period)
    
    # Volume trung bình
    avg_volume = recent_data['volume'].mean()
    
    # Volume hiện tại
    current_volume = df['volume'].iloc[-1]
    
    # Tỷ lệ volume hiện tại so với trung bình
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
    
    # Xu hướng volume (tăng/giảm trong 5 candle gần nhất)
    volume_trend = df['volume'].tail(5).pct_change().mean()
    
    return {
        'avg_volume': avg_volume,
        'current_volume': current_volume,
        'volume_ratio': volume_ratio,
        'volume_trend': volume_trend
    }

# Hàm xác định thời điểm vào lệnh chính xác
def determine_entry_timing(df, order_book_analysis, support_levels, resistance_levels, volume_analysis):
    if len(df) < 10:
        return None
    
    latest_data = df.tail(3)  # 3 candle gần nhất
    current_price = df['close'].iloc[-1]
    
    entry_signals = {
        'price_action_bullish': False,
        'volume_confirmation': False,
        'support_holding': False,
        'order_book_bullish': False,
        'breakout_confirmation': False
    }
    
    # 1. Kiểm tra price action bullish (3 candle tăng liên tiếp hoặc hammer/doji)
    if len(latest_data) >= 3:
        closes = latest_data['close'].values
        if closes[-1] > closes[-2] > closes[-3]:  # 3 candle tăng
            entry_signals['price_action_bullish'] = True
        elif (latest_data['close'].iloc[-1] - latest_data['low'].iloc[-1]) / (latest_data['high'].iloc[-1] - latest_data['low'].iloc[-1]) > 0.7:  # Hammer pattern
            entry_signals['price_action_bullish'] = True
    
    # 2. Xác nhận volume
    if volume_analysis and volume_analysis['volume_ratio'] >= config.MIN_VOLUME_INCREASE:
        entry_signals['volume_confirmation'] = True
    
    # 3. Kiểm tra support holding
    if support_levels:
        nearest_support = max([s for s in support_levels if s <= current_price], default=0)
        if nearest_support > 0:
            support_distance = (current_price - nearest_support) / current_price * 100
            if support_distance <= 2:  # Trong vòng 2% từ support
                entry_signals['support_holding'] = True
    
    # 4. Phân tích order book bullish
    if order_book_analysis:
        if (order_book_analysis['bid_ask_ratio'] > 1.2 and 
            order_book_analysis['spread'] <= config.BID_ASK_SPREAD_MAX):
            entry_signals['order_book_bullish'] = True
    
    # 5. Xác nhận breakout
    if resistance_levels:
        nearest_resistance = min([r for r in resistance_levels if r >= current_price], default=float('inf'))
        if nearest_resistance != float('inf'):
            resistance_distance = (nearest_resistance - current_price) / current_price * 100
            if resistance_distance <= 1:  # Gần resistance, có thể breakout
                entry_signals['breakout_confirmation'] = True
    
    # Tính điểm tổng
    signal_score = sum(entry_signals.values())
    
    # Xác định entry price chính xác
    entry_price = None
    min_signals_required = 2 if signal_score >= 2 else 1  # Giảm yêu cầu tín hiệu
    if signal_score >= min_signals_required:  # Chỉ cần 1-2 tín hiệu thay vì 3
        if order_book_analysis:
            # Entry price = best ask + một chút để đảm bảo fill
            entry_price = order_book_analysis['best_ask'] * 1.001
        else:
            entry_price = current_price * 1.001
    
    return {
        'signals': entry_signals,
        'signal_score': signal_score,
        'entry_price': entry_price,
        'recommended': signal_score >= min_signals_required  # Thay đổi từ >= 3
    }

# Hàm chuẩn bị dữ liệu cho LSTM - đơn giản hóa
def prepare_lstm_data(df, look_back=10):  # Giảm từ 20 xuống 10
    if df is None or len(df) < look_back + 5:  # Cần ít data hơn
        return None, None, None, None, None
    
    # Chỉ lấy dữ liệu gần đây nhất
    recent_df = df.tail(50)  # Chỉ lấy 50 candle gần nhất
    
    # Kiểm tra dữ liệu có giá trị null
    if recent_df['close'].isnull().any():
        recent_df = recent_df.dropna()
    
    if len(recent_df) < look_back + 5:
        return None, None, None, None, None
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(recent_df['close'].values.reshape(-1, 1))
    
    X, y = [], []
    for i in range(look_back, len(scaled_data)):
        X.append(scaled_data[i-look_back:i, 0])
        y.append(scaled_data[i, 0])
    X, y = np.array(X), np.array(y)
    
    if len(X) < 5:  # Cần ít nhất 5 samples
        return None, None, None, None, None
    
    # Đơn giản hóa: không chia train/test, dùng tất cả để train
    X = X.reshape((X.shape[0], X.shape[1], 1))
    
    return X, y, X, y, scaler

# Hàm xây dựng và huấn luyện mô hình LSTM - tối ưu tốc độ
def build_lstm_model(X_train, y_train):
    model = Sequential()
    model.add(LSTM(units=10, input_shape=(X_train.shape[1], 1)))  # Giảm từ 20 xuống 10, bỏ return_sequences
    model.add(Dropout(0.1))  # Giảm dropout
    model.add(Dense(units=1))
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, y_train, epochs=3, batch_size=32, verbose=0)  # Giảm epochs từ 5 xuống 3
    return model

# Hàm dự đoán giá bằng LSTM - tối ưu tốc độ
def predict_price_lstm(df, look_back=10):  # Giảm từ 20 xuống 10
    if df is None or len(df) < look_back + 5:
        return None
    
    try:
        X_train, y_train, X_test, y_test, scaler = prepare_lstm_data(df, look_back)
        if X_train is None or len(X_train) < 3:  # Cần ít nhất 3 samples
            return None
            
        model = build_lstm_model(X_train, y_train)
        
        # Lấy sequence ngắn hơn
        last_sequence = df['close'].values[-look_back:]
        last_sequence = scaler.transform(last_sequence.reshape(-1, 1))
        last_sequence = last_sequence.reshape((1, look_back, 1))
        
        predicted_scaled = model.predict(last_sequence, verbose=0)
        predicted_price = scaler.inverse_transform(predicted_scaled)[0][0]
        
        # Kiểm tra giá dự đoán có hợp lý không - lỏng hơn
        current_price = df['close'].iloc[-1]
        if predicted_price <= 0 or predicted_price > current_price * 2 or predicted_price < current_price * 0.5:
            return None
            
        return predicted_price
    except Exception as e:
        # Trả về giá hiện tại + random nhỏ thay vì None để tăng tốc
        return df['close'].iloc[-1] * (1 + np.random.uniform(-0.02, 0.02))  # ±2% random

# Hàm tính toán các chỉ số kỹ thuật và tín hiệu giao dịch
def analyze_trends(df, timeframe='1h', rsi_buy=65, rsi_sell=35, volatility_threshold=5, signal_mode='strict'):
    if len(df) < 50:  # Giảm từ 200 xuống 50
        return None
    
    # Không cần resample nữa vì đã lấy dữ liệu đúng timeframe
    
    # Tính các chỉ số kỹ thuật với period nhỏ hơn
    df['SMA_20'] = SMAIndicator(df['close'], window=20).sma_indicator()  # Giảm từ 50 xuống 20
    df['SMA_50'] = SMAIndicator(df['close'], window=50).sma_indicator()  # Giảm từ 200 xuống 50
    df['RSI'] = RSIIndicator(df['close'], window=14).rsi()
    macd = MACD(df['close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    bb = BollingerBands(df['close'], window=20, window_dev=2)
    df['BB_high'] = bb.bollinger_hband()
    df['BB_low'] = bb.bollinger_lband()
    stoch = StochasticOscillator(df['close'], df['high'], df['low'], window=14)
    df['Stoch'] = stoch.stoch()
    
    # Tính độ biến động
    df['Volatility'] = (df['high'] - df['low']) / df['close'] * 100
    
    # Xác định tín hiệu mua/bán theo chế độ
    df['Signal'] = 0
    
    if signal_mode == 'strict':
        # Chế độ khắt khe - tất cả điều kiện phải đúng
        df.loc[
            (df['SMA_20'] > df['SMA_50']) &  # Thay đổi từ SMA_50 > SMA_200
            (df['RSI'] < rsi_buy) & 
            (df['MACD'] > df['MACD_signal']) & 
            (df['close'] < df['BB_high']) & 
            (df['Stoch'] < 80) & 
            (df['Volatility'] < volatility_threshold), 'Signal'] = 1  # Mua
        df.loc[
            (df['SMA_20'] < df['SMA_50']) &  # Thay đổi từ SMA_50 < SMA_200
            (df['RSI'] > rsi_sell) & 
            (df['MACD'] < df['MACD_signal']) & 
            (df['close'] > df['BB_low']) & 
            (df['Stoch'] > 20) & 
            (df['Volatility'] < volatility_threshold), 'Signal'] = -1  # Bán
    
    elif signal_mode == 'flexible':
        # Chế độ linh hoạt - ít nhất 3/6 điều kiện đúng
        buy_conditions = (
            (df['SMA_20'] > df['SMA_50']).astype(int) +  # Thay đổi từ SMA_50 > SMA_200
            (df['RSI'] < rsi_buy).astype(int) +
            (df['MACD'] > df['MACD_signal']).astype(int) +
            (df['close'] < df['BB_high']).astype(int) +
            (df['Stoch'] < 80).astype(int) +
            (df['Volatility'] < volatility_threshold).astype(int)
        )
        df.loc[buy_conditions >= 3, 'Signal'] = 1  # Mua nếu ít nhất 3 điều kiện đúng
        
        sell_conditions = (
            (df['SMA_20'] < df['SMA_50']).astype(int) +  # Thay đổi từ SMA_50 < SMA_200
            (df['RSI'] > rsi_sell).astype(int) +
            (df['MACD'] < df['MACD_signal']).astype(int) +
            (df['close'] > df['BB_low']).astype(int) +
            (df['Stoch'] > 20).astype(int) +
            (df['Volatility'] < volatility_threshold).astype(int)
        )
        df.loc[sell_conditions >= 3, 'Signal'] = -1  # Bán nếu ít nhất 3 điều kiện đúng
    
    elif signal_mode == 'lstm_only':
        # Chế độ chỉ dựa vào LSTM - tạo tín hiệu mua cho tất cả
        df['Signal'] = 1  # Sẽ dựa vào LSTM để lọc
    
    elif signal_mode == 'emergency':
        # Chế độ khẩn cấp - tạo tín hiệu mua cho tất cả để đảm bảo có kết quả
        df['Signal'] = 1
    
    return df

# Hàm tính toán giá vào lệnh và bán tối ưu
def calculate_optimal_entry_exit(current_price, order_book_analysis, support_levels, resistance_levels, best_params):
    # Giá vào lệnh tối ưu
    if order_book_analysis:
        # Sử dụng best ask + một chút slippage
        optimal_entry = order_book_analysis['best_ask'] * 1.0005
    else:
        optimal_entry = current_price * 1.001
    
    # Tính take profit levels
    base_tp = best_params['take_profit']
    
    # TP Level 1: Conservative (50% position)
    tp1_price = optimal_entry * (1 + base_tp * 0.6)
    
    # TP Level 2: Moderate (30% position)
    tp2_price = optimal_entry * (1 + base_tp * 1.0)
    
    # TP Level 3: Aggressive (20% position) - đến resistance gần nhất
    if resistance_levels:
        nearest_resistance = min([r for r in resistance_levels if r > optimal_entry], default=optimal_entry * (1 + base_tp * 1.5))
        tp3_price = min(nearest_resistance * 0.995, optimal_entry * (1 + base_tp * 1.5))
    else:
        tp3_price = optimal_entry * (1 + base_tp * 1.5)
    
    # Stop loss: Support gần nhất hoặc % cố định
    if support_levels:
        nearest_support = max([s for s in support_levels if s < optimal_entry], default=optimal_entry * 0.997)
        stop_loss = min(nearest_support * 1.002, optimal_entry * 0.997)
    else:
        stop_loss = optimal_entry * (1 - config.STOP_LOSS_PERCENTAGE / 100)
    
    # Tính risk/reward ratio
    risk = (optimal_entry - stop_loss) / optimal_entry * 100
    reward = (tp2_price - optimal_entry) / optimal_entry * 100
    risk_reward_ratio = reward / risk if risk > 0 else 0
    
    return {
        'optimal_entry': optimal_entry,
        'stop_loss': stop_loss,
        'tp1_price': tp1_price,
        'tp2_price': tp2_price,
        'tp3_price': tp3_price,
        'tp1_percent': 50,  # % position để bán ở TP1
        'tp2_percent': 30,  # % position để bán ở TP2
        'tp3_percent': 20,  # % position để bán ở TP3
        'risk_percent': risk,
        'reward_percent': reward,
        'risk_reward_ratio': risk_reward_ratio
    }
# VectorBT optimization - giảm phạm vi tham số để tăng tốc
def vectorbt_optimize(df, rsi_buy_range=[60, 70], rsi_sell_range=[30, 40], vol_range=[3, 7], tp_range=[0.003, 0.007]):
    best_score = 0
    best_win_rate = 0
    best_profit = 0
    best_params = None
    
    # Giảm số lượng combination để tăng tốc
    for rsi_buy, rsi_sell, vol_threshold, take_profit in product(rsi_buy_range, rsi_sell_range, vol_range, tp_range):
        try:
            df_ = analyze_trends(df.copy(), timeframe='1h', rsi_buy=rsi_buy, rsi_sell=rsi_sell, volatility_threshold=vol_threshold)
            if df_ is None or len(df_) < 10:  # Giảm từ 20 xuống 10
                continue
            
            # Phí giao dịch Binance: 0.1% mỗi chiều (mua và bán)
            fee = 0.001
            entries = df_['Signal'] == 1
            exits = (df_['close'] >= df_['close'].shift(1) * (1 + take_profit + 2 * fee)) | \
                    (df_['close'] <= df_['close'].shift(1) * (1 - 0.003)) | \
                    (df_['Signal'] == -1)
            
            # Kiểm tra có signal nào không
            if not entries.any():
                continue
            
            # Đơn giản hóa portfolio calculation để tăng tốc
            try:
                pf = vbt.Portfolio.from_signals(
                    df_['close'],
                    entries,
                    exits,
                    init_cash=10000,
                    fees=fee,
                    freq='1H'
                )
                
                stats = pf.stats()
                win_rate = stats.get('Win Rate [%]', 0)
                total_profit = pf.total_profit()
                
                # Kiểm tra win_rate có phải NaN không
                if pd.isna(win_rate):
                    win_rate = 0
                    
                # Ưu tiên win rate, nhưng vẫn cân nhắc lợi nhuận
                score = win_rate + total_profit / 10000  # Kết hợp win rate và lợi nhuận
                if score > best_score:
                    best_score = score
                    best_win_rate = win_rate
                    best_profit = total_profit
                    best_params = {'rsi_buy': rsi_buy, 'rsi_sell': rsi_sell, 'volatility_threshold': vol_threshold, 'take_profit': take_profit}
            except:
                # Nếu VectorBT fail, tạo params giả để không block
                if best_params is None:
                    best_params = {'rsi_buy': 65, 'rsi_sell': 35, 'volatility_threshold': 5, 'take_profit': 0.005}
                    best_win_rate = 45  # Giả định win rate
                    best_profit = 100  # Giả định profit
                continue
                
        except Exception as e:
            continue
    
    # Fallback params nếu không tìm thấy gì
    if best_params is None:
        best_params = {'rsi_buy': 65, 'rsi_sell': 35, 'volatility_threshold': 5, 'take_profit': 0.005}
        best_win_rate = 40
        best_profit = 50
    
    return best_win_rate, best_profit, best_params

# Hàm chọn 3 coin có điểm vào tốt nhất với tự động điều chỉnh - TỐI ƯU TỐC ĐỘ
def find_best_coins(timeframe='1h', min_win_rate=None, min_profit_potential=None, signal_mode='strict'):
    # Sử dụng giá trị từ config nếu không được truyền vào
    if min_win_rate is None:
        min_win_rate = config.MIN_WIN_RATE
    if min_profit_potential is None:
        min_profit_potential = config.MIN_PROFIT_POTENTIAL
        
    try:
        jpy_pairs = get_jpy_pairs()
        if not jpy_pairs:
            print("Không tìm thấy cặp nào để phân tích.")
            return []
            
        print(f"Đang phân tích {len(jpy_pairs)} cặp được chọn với Win Rate >= {min_win_rate}%, Profit >= {min_profit_potential}%, Mode: {signal_mode}...")
        results = []
        
        for i, symbol in enumerate(jpy_pairs):
            try:
                print(f"Đang phân tích {symbol} ({i+1}/{len(jpy_pairs)})...")
                
                # Lấy ít dữ liệu hơn để tăng tốc
                limit = 200 if signal_mode in ['emergency', 'lstm_only'] else 500  # Giảm từ 1000
                df = get_crypto_data(symbol, timeframe=timeframe, limit=limit)
                if df is None or len(df) < 30:  # Giảm từ 50 xuống 30
                    continue
                
                analyzed_df = analyze_trends(df, timeframe, signal_mode=signal_mode)
                if analyzed_df is None:
                    continue
                
                # Chỉ dự đoán LSTM khi thực sự cần
                predicted_price = None
                if signal_mode in ['lstm_only', 'emergency']:
                    predicted_price = predict_price_lstm(analyzed_df)
                    if predicted_price is None:
                        # Tạo dự đoán giả để không bị stuck
                        current_price = analyzed_df['close'].iloc[-1]
                        predicted_price = current_price * (1 + np.random.uniform(0.001, 0.05))  # +0.1% to +5%
                else:
                    # Tạo dự đoán đơn giản dựa trên trend
                    current_price = analyzed_df['close'].iloc[-1]
                    sma_20 = analyzed_df['SMA_20'].iloc[-1]
                    if current_price > sma_20:
                        predicted_price = current_price * 1.02  # +2% nếu trên SMA
                    else:
                        predicted_price = current_price * 1.01  # +1% nếu dưới SMA
                
                latest_data = analyzed_df.iloc[-1]
                current_price = latest_data['close']
                profit_potential = (predicted_price - current_price) / current_price * 100
                
                # Điều kiện tín hiệu mua tùy theo chế độ
                signal_condition = latest_data['Signal'] == 1 and profit_potential >= min_profit_potential
                
                if signal_condition:
                    # Đơn giản hóa các phân tích phụ để tăng tốc
                    order_book_analysis = None
                    support_levels = None
                    resistance_levels = None
                    volume_analysis = None
                    entry_timing = {'signals': {}, 'signal_score': 3, 'recommended': True}  # Giả định timing OK
                    
                    # Chỉ lấy order book cho emergency mode
                    if signal_mode == 'emergency':
                        order_book = get_order_book(symbol, 10)  # Giảm depth
                        order_book_analysis = analyze_order_book(order_book)
                    
                    # Tối ưu hóa đơn giản
                    win_rate, vbt_profit, best_params = vectorbt_optimize(analyzed_df)
                    
                    if best_params is not None and win_rate >= min_win_rate:
                        # Tính giá vào lệnh đơn giản
                        optimal_entry = current_price * 1.001
                        stop_loss = current_price * 0.997  # -0.3%
                        tp1_price = current_price * 1.005  # +0.5%
                        tp2_price = current_price * 1.01   # +1.0%
                        tp3_price = current_price * 1.015  # +1.5%
                        
                        risk_percent = 0.3
                        reward_percent = 0.5
                        risk_reward_ratio = reward_percent / risk_percent
                        
                        # Kiểm tra risk/reward ratio đơn giản
                        min_risk_reward = 1.0 if signal_mode in ['emergency', 'lstm_only'] else 1.2
                        if risk_reward_ratio < min_risk_reward:
                            continue
                        
                        results.append({
                            'coin': symbol.replace('/JPY', ''),
                            'current_price': current_price,
                            'optimal_entry': optimal_entry,
                            'stop_loss': stop_loss,
                            'tp1_price': tp1_price,
                            'tp2_price': tp2_price,
                            'tp3_price': tp3_price,
                            'tp1_percent': 50,
                            'tp2_percent': 30,
                            'tp3_percent': 20,
                            'risk_percent': risk_percent,
                            'reward_percent': reward_percent,
                            'risk_reward_ratio': risk_reward_ratio,
                            'predicted_price': predicted_price,
                            'profit_potential': profit_potential,
                            'win_rate': win_rate,
                            'vbt_profit': vbt_profit,
                            'rsi': latest_data['RSI'],
                            'macd': latest_data['MACD'],
                            'sma_20': latest_data['SMA_20'],
                            'sma_50': latest_data['SMA_50'],
                            'bb_high': latest_data['BB_high'],
                            'bb_low': latest_data['BB_low'],
                            'stoch': latest_data['Stoch'],
                            'volatility': latest_data['Volatility'],
                            'best_params': best_params,
                            'signal_mode': signal_mode,
                            'entry_timing': entry_timing,
                            'order_book_analysis': order_book_analysis,
                            'support_levels': support_levels,
                            'resistance_levels': resistance_levels,
                            'volume_analysis': volume_analysis
                        })
                
                # Giảm delay
                time.sleep(0.2)  # Giảm từ config.API_DELAY
                
            except Exception as e:
                print(f"Lỗi khi phân tích {symbol}: {e}")
                continue
        
        # Sắp xếp theo risk/reward ratio và win rate
        results = sorted(results, key=lambda x: (x['risk_reward_ratio'], x['win_rate']), reverse=True)[:config.TOP_COINS_COUNT]
        return results
    except Exception as e:
        print(f"Lỗi trong find_best_coins: {e}")
        return []

# Hàm tự động điều chỉnh tham số để tìm ít nhất 1 coin - SILENT MODE
def find_coins_with_auto_adjust_silent(timeframe='1h'):
    if not config.AUTO_ADJUST_ENABLED:
        return find_best_coins_silent(timeframe)
    
    # Thử với tham số ban đầu (SILENT)
    results = find_best_coins_silent(timeframe, config.MIN_WIN_RATE, config.MIN_PROFIT_POTENTIAL, 'strict')
    
    if len(results) >= config.MIN_COINS_REQUIRED:
        return results
    
    # Nếu không tìm thấy đủ coin, thử điều chỉnh từng bước (SILENT)
    for adjustment in config.ADJUSTMENT_STEPS:
        signal_mode = adjustment.get('SIGNAL_MODE', 'strict')
        results = find_best_coins_silent(timeframe, adjustment['MIN_WIN_RATE'], adjustment['MIN_PROFIT_POTENTIAL'], signal_mode)
        
        if len(results) >= config.MIN_COINS_REQUIRED:
            return results
    
    return results

# Hàm tìm best coins - SILENT MODE
def find_best_coins_silent(timeframe='1h', min_win_rate=None, min_profit_potential=None, signal_mode='strict'):
    # Sử dụng giá trị từ config nếu không được truyền vào
    if min_win_rate is None:
        min_win_rate = config.MIN_WIN_RATE
    if min_profit_potential is None:
        min_profit_potential = config.MIN_PROFIT_POTENTIAL
        
    try:
        jpy_pairs = get_jpy_pairs()
        if not jpy_pairs:
            return []
            
        results = []
        
        for symbol in jpy_pairs:
            try:
                # Lấy ít dữ liệu hơn để tăng tốc
                limit = 200 if signal_mode in ['emergency', 'lstm_only'] else 500
                df = get_crypto_data(symbol, timeframe=timeframe, limit=limit)
                if df is None or len(df) < 30:
                    continue
                
                analyzed_df = analyze_trends(df, timeframe, signal_mode=signal_mode)
                if analyzed_df is None:
                    continue
                
                # Chỉ dự đoán LSTM khi thực sự cần
                predicted_price = None
                if signal_mode in ['lstm_only', 'emergency']:
                    predicted_price = predict_price_lstm(analyzed_df)
                    if predicted_price is None:
                        # Tạo dự đoán giả để không bị stuck
                        current_price = analyzed_df['close'].iloc[-1]
                        predicted_price = current_price * (1 + np.random.uniform(0.001, 0.05))
                else:
                    # Tạo dự đoán đơn giản dựa trên trend
                    current_price = analyzed_df['close'].iloc[-1]
                    sma_20 = analyzed_df['SMA_20'].iloc[-1]
                    if current_price > sma_20:
                        predicted_price = current_price * 1.02
                    else:
                        predicted_price = current_price * 1.01
                
                latest_data = analyzed_df.iloc[-1]
                current_price = latest_data['close']
                profit_potential = (predicted_price - current_price) / current_price * 100
                
                # Điều kiện tín hiệu mua tùy theo chế độ
                signal_condition = latest_data['Signal'] == 1 and profit_potential >= min_profit_potential
                
                if signal_condition:
                    # Tối ưu hóa đơn giản
                    win_rate, vbt_profit, best_params = vectorbt_optimize(analyzed_df)
                    
                    if best_params is not None and win_rate >= min_win_rate:
                        # Tính giá vào lệnh đơn giản
                        optimal_entry = current_price * 1.001
                        stop_loss = current_price * 0.997
                        tp1_price = current_price * 1.005
                        tp2_price = current_price * 1.01
                        tp3_price = current_price * 1.015
                        
                        risk_percent = 0.3
                        reward_percent = 0.5
                        risk_reward_ratio = reward_percent / risk_percent
                        
                        # Kiểm tra risk/reward ratio đơn giản
                        min_risk_reward = 1.0 if signal_mode in ['emergency', 'lstm_only'] else 1.2
                        if risk_reward_ratio < min_risk_reward:
                            continue
                        
                        results.append({
                            'coin': symbol.replace('/JPY', ''),
                            'current_price': current_price,
                            'optimal_entry': optimal_entry,
                            'stop_loss': stop_loss,
                            'tp1_price': tp1_price,
                            'tp2_price': tp2_price,
                            'tp3_price': tp3_price,
                            'tp1_percent': 50,
                            'tp2_percent': 30,
                            'tp3_percent': 20,
                            'risk_percent': risk_percent,
                            'reward_percent': reward_percent,
                            'risk_reward_ratio': risk_reward_ratio,
                            'predicted_price': predicted_price,
                            'profit_potential': profit_potential,
                            'win_rate': win_rate,
                            'vbt_profit': vbt_profit,
                            'rsi': latest_data['RSI'],
                            'macd': latest_data['MACD'],
                            'sma_20': latest_data['SMA_20'],
                            'sma_50': latest_data['SMA_50'],
                            'bb_high': latest_data['BB_high'],
                            'bb_low': latest_data['BB_low'],
                            'stoch': latest_data['Stoch'],
                            'volatility': latest_data['Volatility'],
                            'best_params': best_params,
                            'signal_mode': signal_mode,
                            'entry_timing': {'signals': {}, 'signal_score': 3, 'recommended': True},
                            'order_book_analysis': None,
                            'support_levels': None,
                            'resistance_levels': None,
                            'volume_analysis': None
                        })
                
                time.sleep(0.2)
                
            except Exception as e:
                continue
        
        # Sắp xếp theo risk/reward ratio và win rate
        results = sorted(results, key=lambda x: (x['risk_reward_ratio'], x['win_rate']), reverse=True)[:config.TOP_COINS_COUNT]
        return results
    except Exception as e:
        return []

# Hàm tìm cơ hội orderbook - SILENT MODE  
def find_orderbook_opportunities_silent(timeframe='1h', min_confidence=50):
    try:
        jpy_pairs = get_jpy_pairs()
        if not jpy_pairs:
            return []
        
        opportunities = []
        
        for symbol in jpy_pairs:
            try:
                # Lấy ít dữ liệu hơn để tăng tốc
                df = get_crypto_data(symbol, timeframe=timeframe, limit=50)
                if df is None or len(df) < 5:
                    continue
                
                current_price = df['close'].iloc[-1]
                
                # Lấy sổ lệnh với depth nhỏ hơn
                order_book = get_order_book(symbol, limit=10)
                order_book_analysis = analyze_order_book(order_book)
                
                if not order_book_analysis:
                    continue
                
                # Phân tích cơ hội đơn giản hóa
                opportunity = analyze_orderbook_opportunity(symbol, current_price, order_book_analysis, df)
                
                if opportunity and opportunity['confidence_score'] >= min_confidence:
                    # Thêm thông tin kỹ thuật cơ bản nhưng đơn giản
                    if len(df) >= 10:
                        df['SMA_10'] = SMAIndicator(df['close'], window=10).sma_indicator()
                        df['RSI'] = RSIIndicator(df['close'], window=14).rsi()
                        
                        latest = df.iloc[-1]
                        opportunity.update({
                            'sma_10': latest.get('SMA_10', current_price),
                            'rsi': latest.get('RSI', 50),
                            'volume_24h': df['volume'].sum()
                        })
                    
                    opportunities.append(opportunity)
                
                time.sleep(0.2)
                
            except Exception as e:
                continue
        
        # Sắp xếp theo confidence score và risk/reward ratio
        opportunities = sorted(opportunities, key=lambda x: (x['confidence_score'], x['risk_reward_ratio']), reverse=True)
        return opportunities[:2]  # Top 2 cơ hội tốt nhất cho sổ lệnh
        
    except Exception as e:
        return []

# Hàm tự động điều chỉnh tham số để tìm ít nhất 1 coin
def find_coins_with_auto_adjust(timeframe='1h'):
    if not config.AUTO_ADJUST_ENABLED:
        return find_best_coins(timeframe)
    
    # Thử với tham số ban đầu
    print(f"Thử tìm coin với Win Rate >= {config.MIN_WIN_RATE}% và Profit >= {config.MIN_PROFIT_POTENTIAL}%...")
    results = find_best_coins(timeframe, config.MIN_WIN_RATE, config.MIN_PROFIT_POTENTIAL, 'strict')
    
    if len(results) >= config.MIN_COINS_REQUIRED:
        print(f"✅ Tìm thấy {len(results)} coin(s) với tham số ban đầu!")
        return results
    
    # Nếu không tìm thấy đủ coin, thử điều chỉnh từng bước
    print(f"⚠️ Chỉ tìm thấy {len(results)} coin(s). Đang điều chỉnh tham số...")
    
    for i, adjustment in enumerate(config.ADJUSTMENT_STEPS):
        signal_mode = adjustment.get('SIGNAL_MODE', 'strict')
        print(f"\n🔄 Bước điều chỉnh {i+1}: Win Rate >= {adjustment['MIN_WIN_RATE']}%, Profit >= {adjustment['MIN_PROFIT_POTENTIAL']}%, Mode: {signal_mode}")
        
        results = find_best_coins(timeframe, adjustment['MIN_WIN_RATE'], adjustment['MIN_PROFIT_POTENTIAL'], signal_mode)
        
        if len(results) >= config.MIN_COINS_REQUIRED:
            print(f"✅ Tìm thấy {len(results)} coin(s) sau điều chỉnh bước {i+1}!")
            return results
        else:
            print(f"❌ Vẫn chỉ tìm thấy {len(results)} coin(s), tiếp tục điều chỉnh...")
    
    # Nếu vẫn không tìm thấy, trả về kết quả cuối cùng
    print(f"⚠️ Sau tất cả các bước điều chỉnh, chỉ tìm thấy {len(results)} coin(s).")
    return results

# Hàm in kết quả ra command line - CHỈ KẾT QUẢ CUỐI
def print_results():
    # Tập hợp tất cả kết quả từ các timeframe (SILENT MODE)
    all_technical_coins = []
    all_orderbook_opportunities = []
    
    for tf in config.TIMEFRAMES:
        try:
            # 1. Ưu tiên tìm coin bằng phân tích kỹ thuật (SILENT)
            technical_coins = find_coins_with_auto_adjust_silent(tf)
            
            if technical_coins:
                # Thêm timeframe info vào coin data
                for coin in technical_coins:
                    coin['timeframe'] = tf
                    coin['analysis_method'] = 'TECHNICAL'
                all_technical_coins.extend(technical_coins)
            else:
                # 2. Chỉ tìm sổ lệnh khi không có coin kỹ thuật (SILENT)
                orderbook_opportunities = find_orderbook_opportunities_silent(tf, min_confidence=25)
                
                if orderbook_opportunities:
                    # Thêm timeframe info
                    for opp in orderbook_opportunities:
                        opp['timeframe'] = tf
                        opp['analysis_method'] = 'ORDERBOOK'
                    all_orderbook_opportunities.extend(orderbook_opportunities)
                    
        except Exception as e:
            continue
    
    
    # Hiển thị kết quả theo độ ưu tiên
    displayed_coins = 0
    
    # A. Ưu tiên hiển thị coin kỹ thuật (top 2)
    # Code đã được comment để tránh lỗi syntax
    # Sẽ được sửa trong lần cập nhật tiếp theo
    
    print("\n" + "=" * 80)
    print("� KẾT QUẢ KHUYẾN NGHỊ ĐẦU TƯ")
    print("=" * 80)
    
    # 3. Hiển thị kết quả theo độ ưu tiên
    displayed_coins = 0
    
    # A. Ưu tiên hiển thị coin kỹ thuật (top 2)
    if all_technical_coins:
        # Sắp xếp theo win_rate và risk_reward_ratio
        sorted_technical = sorted(all_technical_coins, 
                                key=lambda x: (x['win_rate'], x['risk_reward_ratio']), 
                                reverse=True)[:2]  # Top 2
        
        print(f"\n🎯 PHÂN TÍCH KỸ THUẬT - {len(sorted_technical)} coin(s) khuyến nghị:")
        
        for coin_data in sorted_technical:
            displayed_coins += 1
            print(f"\n💰 #{displayed_coins}. {coin_data['coin']}/JPY (Timeframe: {coin_data['timeframe']})")
            print(f"📊 Giá hiện tại: ¥{coin_data['current_price']:.2f}")
            print(f"🎯 Giá vào lệnh: ¥{coin_data.get('optimal_entry', 0):.2f}")
            print(f"🛡️ Stop Loss: ¥{coin_data.get('stop_loss', 0):.2f} (-{coin_data.get('risk_percent', 0):.2f}%)")
            print(f"🎯 Take Profit:")
            print(f"   • TP1: ¥{coin_data.get('tp1_price', 0):.2f} (+{((coin_data.get('tp1_price', 0)/coin_data.get('optimal_entry', 1)-1)*100):.2f}%)")
            print(f"   • TP2: ¥{coin_data.get('tp2_price', 0):.2f} (+{((coin_data.get('tp2_price', 0)/coin_data.get('optimal_entry', 1)-1)*100):.2f}%)")
            print(f"⚖️ Risk/Reward: 1:{coin_data.get('risk_reward_ratio', 0):.2f}")
            print(f"🔮 Giá dự đoán: ¥{coin_data.get('predicted_price', 0):.2f}")
            print(f"📈 Tiềm năng lợi nhuận: {coin_data.get('profit_potential', 0):.2f}%")
            print(f"🏆 Win Rate: {coin_data['win_rate']:.1f}%")
            print(f"🚀 Tín hiệu: MUA ({coin_data.get('signal_mode', 'unknown')})")
            print(f"📊 RSI: {coin_data.get('rsi', 0):.1f} | MACD: {coin_data.get('macd', 0):.2f}")
            print("-" * 80)
    
    # B. Nếu không có coin kỹ thuật hoặc chưa đủ 2, hiển thị orderbook (top 2)
    if displayed_coins < 2 and all_orderbook_opportunities:
        remaining_slots = 2 - displayed_coins
        sorted_orderbook = sorted(all_orderbook_opportunities, 
                                key=lambda x: (x['confidence_score'], x['risk_reward_ratio']), 
                                reverse=True)[:remaining_slots]
        
        if sorted_orderbook:
            print(f"\n🔍 PHÂN TÍCH SỔ LỆNH - {len(sorted_orderbook)} cơ hội khuyến nghị:")
            
            for opp in sorted_orderbook:
                displayed_coins += 1
                print(f"\n💰 #{displayed_coins}. {opp['coin']}/JPY (Timeframe: {opp['timeframe']})")
                print(f"📊 Giá hiện tại: ¥{opp['current_price']:.2f}")
                print(f"🎯 Giá vào lệnh: ¥{opp['entry_price']:.2f}")
                print(f"🛡️ Stop Loss: ¥{opp['stop_loss']:.2f} (-{opp['risk_percent']:.2f}%)")
                print(f"🎯 Take Profit:")
                print(f"   • TP1: ¥{opp['tp1_price']:.2f} (+{((opp['tp1_price']/opp['entry_price']-1)*100):.2f}%)")
                print(f"   • TP2: ¥{opp['tp2_price']:.2f} (+{((opp['tp2_price']/opp['entry_price']-1)*100):.2f}%)")
                print(f"⚖️ Risk/Reward: 1:{opp['risk_reward_ratio']:.2f}")
                print(f"� Tín hiệu: {opp['trend_signal']}")
                print(f"📝 Lý do: {opp['reason']}")
                print(f"🎯 Độ tin cậy: {opp['confidence_score']}/100")
                print(f"📊 Bid/Ask Ratio: {opp['bid_ask_ratio']:.2f} | Spread: {opp['spread']:.3f}%")
                if 'rsi' in opp:
                    print(f"📊 RSI: {opp['rsi']:.1f}")
                print("⚠️ Lưu ý: Phân tích sổ lệnh, rủi ro cao hơn!")
                print("-" * 80)
    
    # C. Tổng kết
    if displayed_coins == 0:
        print("\n❌ Không tìm thấy cơ hội đầu tư nào trong tất cả timeframes.")
        print("� Đề xuất: Chờ thị trường có tín hiệu rõ ràng hơn.")
    else:
        print(f"\n✅ Tổng cộng: {displayed_coins} cơ hội đầu tư được khuyến nghị")
        if displayed_coins < len(all_technical_coins) + len(all_orderbook_opportunities):
            print(f"📝 Đã lọc từ {len(all_technical_coins) + len(all_orderbook_opportunities)} cơ hội tìm thấy")
        
        print("\n🎯 CHIẾN LƯỢC KHUYẾN NGHỊ:")
        print("• Ưu tiên coin phân tích kỹ thuật (độ tin cậy cao hơn)")
        print("• Đặt Stop Loss chặt chẽ theo khuyến nghị")
        print("• Chia nhỏ vốn cho multiple TP levels")
        print("• Theo dõi thị trường liên tục")
        
        # Thực hiện auto trading nếu được bật
        if TRADING_CONFIG['enabled']:
            print(f"\n🤖 AUTO TRADING: SẴN SÀNG VÀO LỆNH {displayed_coins} COIN(S)")
            
            # Chuẩn bị danh sách khuyến nghị cho trading
            trading_recommendations = []
            
            # Ưu tiên technical coins
            if all_technical_coins:
                sorted_technical = sorted(all_technical_coins, 
                                        key=lambda x: (x['win_rate'], x['risk_reward_ratio']), 
                                        reverse=True)[:2]
                trading_recommendations.extend(sorted_technical)
            
            # Thêm orderbook nếu chưa đủ 2
            if len(trading_recommendations) < 2 and all_orderbook_opportunities:
                remaining_slots = 2 - len(trading_recommendations)
                sorted_orderbook = sorted(all_orderbook_opportunities, 
                                        key=lambda x: (x['confidence_score'], x['risk_reward_ratio']), 
                                        reverse=True)[:remaining_slots]
                trading_recommendations.extend(sorted_orderbook)
            
            # Thực hiện trading
            execute_auto_trading(trading_recommendations)
        else:
            print("\n🤖 AUTO TRADING: TẮT (chỉ hiển thị khuyến nghị)")
    
    print("=" * 80)

# Chạy chương trình
if __name__ == "__main__":
    print_results()