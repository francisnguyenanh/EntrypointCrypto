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
from binance.client import Client

# Khởi tạo Binance API (cho CCXT và python-binance)
binance_ccxt = ccxt.binance()
binance = Client("YOUR_API_KEY", "YOUR_API_SECRET")  # Thay bằng API Key/Secret Key của bạn

# Hàm lấy danh sách cặp crypto/JPY từ Binance
def get_jpy_pairs():
    markets = binance_ccxt.load_markets()
    jpy_pairs = [symbol for symbol in markets if symbol.endswith('/JPY')]
    return jpy_pairs

# Hàm lấy dữ liệu giá từ Binance
def get_crypto_data(symbol, timeframe='1m', limit=1000):
    try:
        ohlcv = binance_ccxt.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except:
        return None

# Hàm chuẩn bị dữ liệu cho LSTM
def prepare_lstm_data(df, look_back=60):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df['close'].values.reshape(-1, 1))
    
    X, y = [], []
    for i in range(look_back, len(scaled_data)):
        X.append(scaled_data[i-look_back:i, 0])
        y.append(scaled_data[i, 0])
    X, y = np.array(X), np.array(y)
    
    train_size = int(len(X) * 0.8)
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
    if len(df) < look_back:
        return None
    X_train, y_train, X_test, y_test, scaler = prepare_lstm_data(df, look_back)
    model = build_lstm_model(X_train, y_train)
    
    last_sequence = df['close'].values[-look_back:]
    last_sequence = scaler.transform(last_sequence.reshape(-1, 1))
    last_sequence = last_sequence.reshape((1, look_back, 1))
    
    predicted_scaled = model.predict(last_sequence, verbose=0)
    predicted_price = scaler.inverse_transform(predicted_scaled)[0][0]
    return predicted_price

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
    best_win_rate = 0
    best_profit = 0
    best_params = None
    
    for rsi_buy, rsi_sell, vol_threshold, take_profit in product(rsi_buy_range, rsi_sell_range, vol_range, tp_range):
        df_ = analyze_trends(df.copy(), timeframe='1h', rsi_buy=rsi_buy, rsi_sell=rsi_sell, volatility_threshold=vol_threshold)
        if df_ is None:
            continue
        
        # Phí giao dịch Binance: 0.1% mỗi chiều (mua và bán)
        fee = 0.001
        entries = df_['Signal'] == 1
        exits = (df_['close'] >= df_['close'].shift(1) * (1 + take_profit + 2 * fee)) | \
                (df_['close'] <= df_['close'].shift(1) * (1 - 0.003)) | \
                (df_['Signal'] == -1)
        
        pf = vbt.Portfolio.from_signals(
            df_['close'],
            entries,
            exits,
            init_cash=10000,
            fees=fee,
            freq='1H'
        )
        win_rate = pf.stats()['Win Rate [%]']
        total_profit = pf.total_profit()
        
        # Ưu tiên win rate, nhưng vẫn cân nhắc lợi nhuận
        score = win_rate + total_profit / 10000
        if score > best_win_rate:
            best_win_rate = win_rate
            best_profit = total_profit
            best_params = {'rsi_buy': rsi_buy, 'rsi_sell': rsi_sell, 'volatility_threshold': vol_threshold, 'take_profit': take_profit}
    
    return best_win_rate, best_profit, best_params

# Hàm chọn 3 coin có điểm vào tốt nhất
def find_best_coins(timeframe='1h'):
    jpy_pairs = get_jpy_pairs()
    results = []
    
    for symbol in jpy_pairs:
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
        
        if latest_data['Signal'] == 1 and profit_potential >= 0.3:
            win_rate, vbt_profit, best_params = vectorbt_optimize(analyzed_df)
            if win_rate > 50:
                fee = 0.001
                sell_price = current_price * (1 + best_params['take_profit'] + 2 * fee)
                
                results.append({
                    'coin': symbol.replace('/JPY', ''),
                    'symbol': symbol,  # Lưu symbol đầy đủ để giao dịch
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
        time.sleep(1)  # Tránh vượt giới hạn API
    
    # Sắp xếp theo win rate và chọn top 3
    results = sorted(results, key=lambda x: x['win_rate'], reverse=True)[:3]
    return results

# Hàm đặt lệnh mua
def place_buy_order(symbol, quantity):
    try:
        order = binance.create_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"Đã đặt lệnh mua {symbol}: {order}")
        return order
    except Exception as e:
        print(f"Lỗi khi đặt lệnh mua {symbol}: {e}")
        return None

# Hàm đặt lệnh bán
def place_sell_order(symbol, quantity):
    try:
        order = binance.create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"Đã đặt lệnh bán {symbol}: {order}")
        return order
    except Exception as e:
        print(f"Lỗi khi đặt lệnh bán {symbol}: {e}")
        return None

# Hàm chạy bot giao dịch tự động
def run_trading_bot(timeframe='1h', quantity=0.001, check_interval=60):
    positions = {}  # Lưu trữ thông tin vị thế: {symbol: {'entry_price': float, 'quantity': float}}
    
    while True:
        print(f"\n[Bot] Kiểm tra tín hiệu giao dịch - Khung thời gian: {timeframe}")
        best_coins = find_best_coins(timeframe)
        
        if not best_coins:
            print("Không tìm thấy coin nào có tín hiệu mua mạnh và win rate cao.")
        else:
            for coin_data in best_coins:
                symbol = coin_data['symbol']
                current_price = coin_data['current_price']
                sell_price = coin_data['sell_price']
                take_profit = coin_data['best_params']['take_profit']
                stop_loss = 0.003  # Cố định stop-loss 0.3%
                
                # Kiểm tra tín hiệu mua
                if symbol not in positions and coin_data['win_rate'] > 50:
                    print(f"Tín hiệu mua {symbol} tại giá ¥{current_price:.2f}")
                    order = place_buy_order(symbol, quantity)
                    if order:
                        positions[symbol] = {
                            'entry_price': current_price,
                            'quantity': quantity
                        }
                
                # Kiểm tra điều kiện bán
                if symbol in positions:
                    df = get_crypto_data(symbol, timeframe='1m', limit=100)
                    if df is None:
                        continue
                    latest_price = df['close'].iloc[-1]
                    profit = (latest_price - positions[symbol]['entry_price']) / positions[symbol]['entry_price']
                    loss = (positions[symbol]['entry_price'] - latest_price) / positions[symbol]['entry_price']
                    
                    if latest_price >= sell_price or loss >= stop_loss:
                        print(f"Tín hiệu bán {symbol} tại giá ¥{latest_price:.2f}, Lợi nhuận: {profit*100:.2f}%")
                        order = place_sell_order(symbol, positions[symbol]['quantity'])
                        if order:
                            del positions[symbol]
        
        # Nghỉ trước khi kiểm tra lại
        print(f"[Bot] Đợi {check_interval} giây trước khi kiểm tra tiếp...")
        time.sleep(check_interval)

# Hàm in kết quả ra command line
def print_results():
    timeframes = ['15m', '30m', '1h', '4h']
    
    print("DỰ ĐOÁN XU HƯỚNG GIÁ CÁC CẶP CRYPTO/JPY (Tối ưu hóa Win Rate)")
    print("=" * 70)
    
    for tf in timeframes:
        print(f"\nKhung thời gian: {tf}")
        print("-" * 70)
        best_coins = find_best_coins(tf)
        
        if not best_coins:
            print("Không tìm thấy coin nào có tín hiệu mua mạnh và win rate cao.")
            continue
        
        for coin_data in best_coins:
            print(f"\nCoin: {coin_data['coin']}/JPY")
            print(f"Giá hiện tại: ¥{coin_data['current_price']:.2f}")
            print(f"Giá bán (sau phí 0.1%): ¥{coin_data['sell_price']:.2f}")
            print(f"Giá dự đoán (LSTM): ¥{coin_data['predicted_price']:.2f}")
            print(f"Tiềm năng lợi nhuận: {coin_data['profit_potential']:.2f}%")
            print(f"Tỷ lệ thắng (Win Rate): {coin_data['win_rate']:.2f}%")
            print(f"Tín hiệu: Mua (Take-profit: {coin_data['best_params']['take_profit']*100:.2f}%, Stop-loss: 0.3%)")
            print(f"RSI: {coin_data['rsi']:.2f}")
            print(f"MACD: {coin_data['macd']:.2f}")
            print(f"SMA 50: ¥{coin_data['sma_50']:.2f}")
            print(f"SMA 200: ¥{coin_data['sma_200']:.2f}")
            print(f"Bollinger Band Cao: ¥{coin_data['bb_high']:.2f}")
            print(f"Bollinger Band Thấp: ¥{coin_data['bb_low']:.2f}")
            print(f"Stochastic Oscillator: {coin_data['stoch']:.2f}")
            print(f"Độ biến động: {coin_data['volatility']:.2f}%")
            print(f"Lợi nhuận VectorBT: ¥{coin_data['vbt_profit']:.2f}")
            print(f"Tham số tối ưu: RSI Buy={coin_data['best_params']['rsi_buy']}, RSI Sell={coin_data['best_params']['rsi_sell']}, Volatility={coin_data['best_params']['volatility_threshold']}, Take-profit={coin_data['best_params']['take_profit']*100:.2f}%")
            print("-" * 70)

# Chạy chương trình
if __name__ == "__main__":
    # Chạy bot giao dịch tự động
    run_trading_bot(timeframe='1h', quantity=0.001, check_interval=60)