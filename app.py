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
def analyze_trends(df, timeframe='1h', rsi_buy=65, rsi_sell=35, volatility_threshold=5):
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
    
    # Xác định tín hiệu mua/bán
    df['Signal'] = 0
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
    return df

# Hàm vectorized backtesting và tối ưu hóa tham số với vectorbt
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

# Hàm chọn 3 coin có điểm vào tốt nhất
def find_best_coins(timeframe='1h'):
    try:
        jpy_pairs = get_jpy_pairs()
        if not jpy_pairs:
            print("Không tìm thấy cặp JPY nào.")
            return []
            
        print(f"Đang phân tích {len(jpy_pairs)} cặp JPY...")
        results = []
        
        for i, symbol in enumerate(jpy_pairs):
            try:
                print(f"Đang phân tích {symbol} ({i+1}/{len(jpy_pairs)})...")
                df = get_crypto_data(symbol, timeframe='1m', limit=1000)
                if df is None or len(df) < 200:
                    continue
                
                analyzed_df = analyze_trends(df, timeframe)
                if analyzed_df is None:
                    continue
                
                predicted_price = predict_price_lstm(analyzed_df)
                if predicted_price is None:
                    continue
                
                latest_data = analyzed_df.iloc[-1]
                current_price = latest_data['close']
                profit_potential = (predicted_price - current_price) / current_price * 100
                
                if latest_data['Signal'] == 1 and profit_potential >= config.MIN_PROFIT_POTENTIAL:  # Giảm ngưỡng để ưu tiên win rate
                    win_rate, vbt_profit, best_params = vectorbt_optimize(analyzed_df)
                    if best_params is not None and win_rate > config.MIN_WIN_RATE:  # Chỉ chọn coin có win rate > 50%
                        # Tính giá bán sau khi trừ phí
                        fee = 0.001
                        sell_price = current_price * (1 + best_params['take_profit'] + 2 * fee)
                        
                        results.append({
                            'coin': symbol.replace('/JPY', ''),
                            'current_price': current_price,
                            'sell_price': sell_price,
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
                            'best_params': best_params
                        })
                time.sleep(config.API_DELAY)  # Tránh vượt giới hạn API Binance
            except Exception as e:
                print(f"Lỗi khi phân tích {symbol}: {e}")
                continue
        
        # Sắp xếp theo win rate và chọn top 3
        results = sorted(results, key=lambda x: x['win_rate'], reverse=True)[:3]
        return results
    except Exception as e:
        print(f"Lỗi trong find_best_coins: {e}")
        return []

# Hàm in kết quả ra command line
def print_results():
    print("DỰ ĐOÁN XU HƯỚNG GIÁ CÁC CẶP CRYPTO/JPY (Tối ưu hóa Win Rate)")
    print("=" * 70)
    
    for tf in config.TIMEFRAMES:
        print(f"\nKhung thời gian: {tf}")
        print("-" * 70)
        
        try:
            best_coins = find_best_coins(tf)
            
            if not best_coins:
                print("Không tìm thấy coin nào có tín hiệu mua mạnh và win rate cao.")
                continue
            
            for coin_data in best_coins:
                # Kiểm tra dữ liệu hợp lệ
                if not all(key in coin_data for key in ['coin', 'current_price', 'win_rate', 'best_params']):
                    continue
                    
                print(f"\nCoin: {coin_data['coin']}/JPY")
                print(f"Giá hiện tại: ¥{coin_data['current_price']:.2f}")
                print(f"Giá bán (sau phí 0.1%): ¥{coin_data.get('sell_price', 0):.2f}")
                print(f"Giá dự đoán (LSTM): ¥{coin_data.get('predicted_price', 0):.2f}")
                print(f"Tiềm năng lợi nhuận: {coin_data.get('profit_potential', 0):.2f}%")
                print(f"Tỷ lệ thắng (Win Rate): {coin_data['win_rate']:.2f}%")
                print(f"Tín hiệu: Mua (Take-profit: {coin_data['best_params']['take_profit']*100:.2f}%, Stop-loss: 0.3%)")
                print(f"RSI: {coin_data.get('rsi', 0):.2f}")
                print(f"MACD: {coin_data.get('macd', 0):.2f}")
                print(f"SMA 50: ¥{coin_data.get('sma_50', 0):.2f}")
                print(f"SMA 200: ¥{coin_data.get('sma_200', 0):.2f}")
                print(f"Bollinger Band Cao: ¥{coin_data.get('bb_high', 0):.2f}")
                print(f"Bollinger Band Thấp: ¥{coin_data.get('bb_low', 0):.2f}")
                print(f"Stochastic Oscillator: {coin_data.get('stoch', 0):.2f}")
                print(f"Độ biến động: {coin_data.get('volatility', 0):.2f}%")
                print(f"Lợi nhuận VectorBT: ¥{coin_data.get('vbt_profit', 0):.2f}")
                print(f"Tham số tối ưu: RSI Buy={coin_data['best_params']['rsi_buy']}, RSI Sell={coin_data['best_params']['rsi_sell']}, Volatility={coin_data['best_params']['volatility_threshold']}, Take-profit={coin_data['best_params']['take_profit']*100:.2f}%")
                print("-" * 70)
        except Exception as e:
            print(f"Lỗi khi xử lý timeframe {tf}: {e}")
            continue

# Chạy chương trình
if __name__ == "__main__":
    print_results()