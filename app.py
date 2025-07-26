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

# Tắt tất cả warnings và logging không cần thiết
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Tắt TensorFlow logs
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Tắt oneDNN notifications
tf.get_logger().setLevel('ERROR')
tf.autograph.set_verbosity(0)

# Khởi tạo Binance API
binance = ccxt.binance()

# Hàm lấy danh sách cặp crypto/JPY từ Binance
def get_jpy_pairs():
    markets = binance.load_markets()
    jpy_pairs = [symbol for symbol in markets if symbol.endswith('/JPY')]
    return jpy_pairs

# Hàm lấy dữ liệu giá từ Binance
def get_crypto_data(symbol, timeframe='1m', limit=1000):
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
    
    return {
        'best_bid': best_bid,
        'best_ask': best_ask,
        'spread': spread,
        'bid_ask_ratio': bid_ask_ratio,
        'total_bid_volume': total_bid_volume,
        'total_ask_volume': total_ask_volume,
        'support_levels': support_levels,
        'resistance_levels': resistance_levels
    }

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
    if signal_score >= 3:  # Ít nhất 3/5 tín hiệu tích cực
        if order_book_analysis:
            # Entry price = best ask + một chút để đảm bảo fill
            entry_price = order_book_analysis['best_ask'] * 1.001
        else:
            entry_price = current_price * 1.001
    
    return {
        'signals': entry_signals,
        'signal_score': signal_score,
        'entry_price': entry_price,
        'recommended': signal_score >= 3
    }

# Hàm chuẩn bị dữ liệu cho LSTM
def prepare_lstm_data(df, look_back=60):
    if df is None or len(df) < look_back:
        return None, None, None, None, None
    
    # Kiểm tra dữ liệu có giá trị null
    if df['close'].isnull().any():
        df = df.dropna()
    
    if len(df) < look_back:
        return None, None, None, None, None
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df['close'].values.reshape(-1, 1))
    
    X, y = [], []
    for i in range(look_back, len(scaled_data)):
        X.append(scaled_data[i-look_back:i, 0])
        y.append(scaled_data[i, 0])
    X, y = np.array(X), np.array(y)
    
    if len(X) == 0:
        return None, None, None, None, None
    
    train_size = int(len(X) * 0.8)
    if train_size == 0:
        return None, None, None, None, None
        
    X_train, y_train = X[:train_size], y[:train_size]
    X_test, y_test = X[train_size:], y[train_size:]
    
    X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
    X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))
    
    return X_train, y_train, X_test, y_test, scaler

# Hàm xây dựng và huấn luyện mô hình LSTM
def build_lstm_model(X_train, y_train):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50))
    model.add(Dropout(0.2))
    model.add(Dense(units=1))
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=0)
    return model

# Hàm dự đoán giá bằng LSTM
def predict_price_lstm(df, look_back=60):
    if df is None or len(df) < look_back:
        return None
    
    try:
        X_train, y_train, X_test, y_test, scaler = prepare_lstm_data(df, look_back)
        if X_train is None:
            return None
            
        model = build_lstm_model(X_train, y_train)
        
        last_sequence = df['close'].values[-look_back:]
        last_sequence = scaler.transform(last_sequence.reshape(-1, 1))
        last_sequence = last_sequence.reshape((1, look_back, 1))
        
        predicted_scaled = model.predict(last_sequence, verbose=0)
        predicted_price = scaler.inverse_transform(predicted_scaled)[0][0]
        
        # Kiểm tra giá dự đoán có hợp lý không
        current_price = df['close'].iloc[-1]
        if predicted_price <= 0 or predicted_price > current_price * config.MAX_PRICE_PREDICTION_RATIO:  # Tránh dự đoán quá vô lý
            return None
            
        return predicted_price
    except Exception as e:
        print(f"Lỗi trong dự đoán LSTM: {e}")
        return None

# Hàm tính toán các chỉ số kỹ thuật và tín hiệu giao dịch
def analyze_trends(df, timeframe='1h', rsi_buy=65, rsi_sell=35, volatility_threshold=5, signal_mode='strict'):
    if len(df) < 200:
        return None
    if timeframe == '15m':
        df = df.resample('15T').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()
    elif timeframe == '30m':
        df = df.resample('30T').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()
    elif timeframe == '1h':
        df = df.resample('1H').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()
    elif timeframe == '4h':
        df = df.resample('4H').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()
    
    # Tính các chỉ số kỹ thuật
    df['SMA_50'] = SMAIndicator(df['close'], window=50).sma_indicator()
    df['SMA_200'] = SMAIndicator(df['close'], window=200).sma_indicator()
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
            (df['SMA_50'] > df['SMA_200']) & 
            (df['RSI'] < rsi_buy) & 
            (df['MACD'] > df['MACD_signal']) & 
            (df['close'] < df['BB_high']) & 
            (df['Stoch'] < 80) & 
            (df['Volatility'] < volatility_threshold), 'Signal'] = 1  # Mua
        df.loc[
            (df['SMA_50'] < df['SMA_200']) & 
            (df['RSI'] > rsi_sell) & 
            (df['MACD'] < df['MACD_signal']) & 
            (df['close'] > df['BB_low']) & 
            (df['Stoch'] > 20) & 
            (df['Volatility'] < volatility_threshold), 'Signal'] = -1  # Bán
    
    elif signal_mode == 'flexible':
        # Chế độ linh hoạt - ít nhất 3/6 điều kiện đúng
        buy_conditions = (
            (df['SMA_50'] > df['SMA_200']).astype(int) +
            (df['RSI'] < rsi_buy).astype(int) +
            (df['MACD'] > df['MACD_signal']).astype(int) +
            (df['close'] < df['BB_high']).astype(int) +
            (df['Stoch'] < 80).astype(int) +
            (df['Volatility'] < volatility_threshold).astype(int)
        )
        df.loc[buy_conditions >= 3, 'Signal'] = 1  # Mua nếu ít nhất 3 điều kiện đúng
        
        sell_conditions = (
            (df['SMA_50'] < df['SMA_200']).astype(int) +
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
def vectorbt_optimize(df, rsi_buy_range=[60, 65, 70], rsi_sell_range=[30, 35, 40], vol_range=[3, 5, 7], tp_range=[0.003, 0.005, 0.007]):
    best_score = 0
    best_win_rate = 0
    best_profit = 0
    best_params = None
    
    for rsi_buy, rsi_sell, vol_threshold, take_profit in product(rsi_buy_range, rsi_sell_range, vol_range, tp_range):
        try:
            df_ = analyze_trends(df.copy(), timeframe='1h', rsi_buy=rsi_buy, rsi_sell=rsi_sell, volatility_threshold=vol_threshold)
            if df_ is None or len(df_) < 50:  # Cần đủ dữ liệu để backtest
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
        except Exception as e:
            print(f"Lỗi trong tối ưu hóa: {e}")
            continue
    
    return best_win_rate, best_profit, best_params

# Hàm chọn 3 coin có điểm vào tốt nhất với tự động điều chỉnh
def find_best_coins(timeframe='1h', min_win_rate=None, min_profit_potential=None, signal_mode='strict'):
    # Sử dụng giá trị từ config nếu không được truyền vào
    if min_win_rate is None:
        min_win_rate = config.MIN_WIN_RATE
    if min_profit_potential is None:
        min_profit_potential = config.MIN_PROFIT_POTENTIAL
        
    try:
        jpy_pairs = get_jpy_pairs()
        if not jpy_pairs:
            print("Không tìm thấy cặp JPY nào.")
            return []
            
        print(f"Đang phân tích {len(jpy_pairs)} cặp JPY với Win Rate >= {min_win_rate}%, Profit >= {min_profit_potential}%, Mode: {signal_mode}...")
        results = []
        
        for i, symbol in enumerate(jpy_pairs):
            try:
                print(f"Đang phân tích {symbol} ({i+1}/{len(jpy_pairs)})...")
                df = get_crypto_data(symbol, timeframe='1m', limit=1000)
                if df is None or len(df) < 200:
                    continue
                
                analyzed_df = analyze_trends(df, timeframe, signal_mode=signal_mode)
                if analyzed_df is None:
                    continue
                
                predicted_price = predict_price_lstm(analyzed_df)
                if predicted_price is None:
                    continue
                
                latest_data = analyzed_df.iloc[-1]
                current_price = latest_data['close']
                profit_potential = (predicted_price - current_price) / current_price * 100
                
                # Điều kiện tín hiệu mua tùy theo chế độ
                signal_condition = latest_data['Signal'] == 1 and profit_potential >= min_profit_potential
                
                if signal_condition:
                    # Lấy order book để phân tích thêm
                    order_book = get_order_book(symbol, config.ORDER_BOOK_DEPTH)
                    order_book_analysis = analyze_order_book(order_book)
                    
                    # Tính support/resistance
                    support_levels, resistance_levels = calculate_support_resistance(analyzed_df, config.SUPPORT_RESISTANCE_PERIOD)
                    
                    # Phân tích volume
                    volume_analysis = analyze_volume(analyzed_df, config.VOLUME_ANALYSIS_PERIOD)
                    
                    # Xác định timing vào lệnh
                    entry_timing = determine_entry_timing(analyzed_df, order_book_analysis, support_levels, resistance_levels, volume_analysis)
                    
                    # Chỉ tiếp tục nếu timing tốt
                    if not entry_timing or not entry_timing['recommended']:
                        continue
                    
                    win_rate, vbt_profit, best_params = vectorbt_optimize(analyzed_df)
                    if best_params is not None and win_rate >= min_win_rate:
                        # Tính giá vào lệnh và bán tối ưu
                        optimal_prices = calculate_optimal_entry_exit(current_price, order_book_analysis, support_levels, resistance_levels, best_params)
                        
                        # Kiểm tra risk/reward ratio (giảm yêu cầu xuống)
                        if optimal_prices['risk_reward_ratio'] < 1.5:  # Risk/Reward phải >= 1.5:1
                            continue
                        
                        results.append({
                            'coin': symbol.replace('/JPY', ''),
                            'current_price': current_price,
                            'optimal_entry': optimal_prices['optimal_entry'],
                            'stop_loss': optimal_prices['stop_loss'],
                            'tp1_price': optimal_prices['tp1_price'],
                            'tp2_price': optimal_prices['tp2_price'],
                            'tp3_price': optimal_prices['tp3_price'],
                            'tp1_percent': optimal_prices['tp1_percent'],
                            'tp2_percent': optimal_prices['tp2_percent'],
                            'tp3_percent': optimal_prices['tp3_percent'],
                            'risk_percent': optimal_prices['risk_percent'],
                            'reward_percent': optimal_prices['reward_percent'],
                            'risk_reward_ratio': optimal_prices['risk_reward_ratio'],
                            'predicted_price': predicted_price,
                            'profit_potential': profit_potential,
                            'win_rate': win_rate,
                            'vbt_profit': vbt_profit,
                            'rsi': latest_data['RSI'],
                            'macd': latest_data['MACD'],
                            'sma_50': latest_data['SMA_50'],
                            'sma_200': latest_data['SMA_200'],
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
                time.sleep(config.API_DELAY)  # Tránh vượt giới hạn API Binance
            except Exception as e:
                print(f"Lỗi khi phân tích {symbol}: {e}")
                continue
        
        # Sắp xếp theo risk/reward ratio và win rate
        results = sorted(results, key=lambda x: (x['risk_reward_ratio'], x['win_rate']), reverse=True)[:config.TOP_COINS_COUNT]
        return results
    except Exception as e:
        print(f"Lỗi trong find_best_coins: {e}")
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

# Hàm in kết quả ra command line
def print_results():
    print("DỰ ĐOÁN XU HƯỚNG GIÁ CÁC CẶP CRYPTO/JPY (Tự động điều chỉnh để tìm coin)")
    print("=" * 80)
    
    for tf in config.TIMEFRAMES:
        print(f"\nKhung thời gian: {tf}")
        print("-" * 80)
        
        try:
            # Sử dụng hàm tự động điều chỉnh
            best_coins = find_coins_with_auto_adjust(tf)
            
            if not best_coins:
                print("❌ Không tìm thấy coin nào có tín hiệu mua sau tất cả các bước điều chỉnh.")
                continue
            
            print(f"\n🎯 Tìm thấy {len(best_coins)} coin(s) khuyến nghị:")
            
            for coin_data in best_coins:
                # Kiểm tra dữ liệu hợp lệ
                if not all(key in coin_data for key in ['coin', 'current_price', 'win_rate', 'best_params']):
                    continue
                    
                print(f"\n💰 Coin: {coin_data['coin']}/JPY")
                print(f"📊 Giá hiện tại: ¥{coin_data['current_price']:.2f}")
                print(f"🎯 Giá vào lệnh tối ưu: ¥{coin_data.get('optimal_entry', 0):.2f}")
                print(f"🛡️ Stop Loss: ¥{coin_data.get('stop_loss', 0):.2f} (-{coin_data.get('risk_percent', 0):.2f}%)")
                print(f"🎯 Take Profit Levels:")
                print(f"   • TP1 ({coin_data.get('tp1_percent', 0)}%): ¥{coin_data.get('tp1_price', 0):.2f}")
                print(f"   • TP2 ({coin_data.get('tp2_percent', 0)}%): ¥{coin_data.get('tp2_price', 0):.2f}")
                print(f"   • TP3 ({coin_data.get('tp3_percent', 0)}%): ¥{coin_data.get('tp3_price', 0):.2f}")
                print(f"� Risk/Reward: 1:{coin_data.get('risk_reward_ratio', 0):.2f}")
                print(f"�🔮 Giá dự đoán (LSTM): ¥{coin_data.get('predicted_price', 0):.2f}")
                print(f"📈 Tiềm năng lợi nhuận: {coin_data.get('profit_potential', 0):.2f}%")
                print(f"🏆 Tỷ lệ thắng (Win Rate): {coin_data['win_rate']:.2f}%")
                print(f"🚀 Tín hiệu: MUA (Mode: {coin_data.get('signal_mode', 'unknown')})")
                
                # Hiển thị timing signals
                if coin_data.get('entry_timing'):
                    timing = coin_data['entry_timing']
                    signals = timing['signals']
                    print(f"⏰ Entry Timing Score: {timing['signal_score']}/5")
                    print(f"   • Price Action: {'✅' if signals['price_action_bullish'] else '❌'}")
                    print(f"   • Volume Confirm: {'✅' if signals['volume_confirmation'] else '❌'}")
                    print(f"   • Support Holding: {'✅' if signals['support_holding'] else '❌'}")
                    print(f"   • Order Book: {'✅' if signals['order_book_bullish'] else '❌'}")
                    print(f"   • Breakout: {'✅' if signals['breakout_confirmation'] else '❌'}")
                
                # Hiển thị order book analysis
                if coin_data.get('order_book_analysis'):
                    ob = coin_data['order_book_analysis']
                    print(f"📋 Order Book:")
                    print(f"   • Best Bid: ¥{ob['best_bid']:.2f}")
                    print(f"   • Best Ask: ¥{ob['best_ask']:.2f}")
                    print(f"   • Spread: {ob['spread']:.3f}%")
                    print(f"   • Bid/Ask Ratio: {ob['bid_ask_ratio']:.2f}")
                
                print(f"📊 Chỉ số kỹ thuật:")
                print(f"   • RSI: {coin_data.get('rsi', 0):.2f}")
                print(f"   • MACD: {coin_data.get('macd', 0):.2f}")
                print(f"   • SMA 50: ¥{coin_data.get('sma_50', 0):.2f}")
                print(f"   • SMA 200: ¥{coin_data.get('sma_200', 0):.2f}")
                print(f"   • BB High: ¥{coin_data.get('bb_high', 0):.2f}")
                print(f"   • BB Low: ¥{coin_data.get('bb_low', 0):.2f}")
                print(f"   • Stochastic: {coin_data.get('stoch', 0):.2f}")
                print(f"   • Độ biến động: {coin_data.get('volatility', 0):.2f}%")
                print(f"💹 Lợi nhuận BackTest: ¥{coin_data.get('vbt_profit', 0):.2f}")
                print(f"⚙️ Tham số tối ưu: RSI Buy={coin_data['best_params']['rsi_buy']}, RSI Sell={coin_data['best_params']['rsi_sell']}, Vol={coin_data['best_params']['volatility_threshold']}, TP={coin_data['best_params']['take_profit']*100:.2f}%")
                print("-" * 80)
        except Exception as e:
            print(f"Lỗi khi xử lý timeframe {tf}: {e}")
            continue

# Chạy chương trình
if __name__ == "__main__":
    print_results()