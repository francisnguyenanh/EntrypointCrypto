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
import warnings
import config

# Tắt tất cả warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
tf.get_logger().setLevel('ERROR')
tf.autograph.set_verbosity(0)

# Khởi tạo Binance API
binance = ccxt.binance()

def debug_single_coin(symbol='BTC/JPY', timeframe='1h'):
    """Debug phân tích một coin cụ thể"""
    print(f"🔍 DEBUG: Phân tích chi tiết {symbol}")
    print("=" * 60)
    
    try:
        # Lấy dữ liệu
        print("1. Lấy dữ liệu...")
        # Lấy dữ liệu trực tiếp từ timeframe 1h thay vì resample từ 1m
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=1000)  # Lấy trực tiếp 1h data
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        print(f"   ✅ Có {len(df)} candles dữ liệu cho {timeframe}")
        print(f"   💰 Giá hiện tại: ¥{df['close'].iloc[-1]:.2f}")
        
        if len(df) < 50:  # Giảm từ 200 xuống 50
            print("   ❌ Không đủ dữ liệu (cần >= 50 candles)")
            return False
        
        # Tính các chỉ số kỹ thuật
        print("\n2. Tính chỉ số kỹ thuật...")
        df['SMA_20'] = SMAIndicator(df['close'], window=20).sma_indicator()
        df['SMA_50'] = SMAIndicator(df['close'], window=50).sma_indicator()
        df['RSI'] = RSIIndicator(df['close'], window=14).rsi()
        macd = MACD(df['close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        bb = BollingerBands(df['close'], window=20, window_dev=2)
        df['BB_high'] = bb.bollinger_hband()
        df['BB_low'] = bb.bollinger_lband()
        stoch = StochasticOscillator(df['close'], df['high'], df['low'], window=14)
        df['Stoch'] = stoch.stoch()
        df['Volatility'] = (df['high'] - df['low']) / df['close'] * 100
        
        # Kiểm tra giá trị cuối
        latest = df.iloc[-1]
        print(f"   📊 RSI: {latest['RSI']:.2f}")
        print(f"   📊 MACD: {latest['MACD']:.4f} vs Signal: {latest['MACD_signal']:.4f}")
        print(f"   📊 SMA 20: ¥{latest['SMA_20']:.2f} vs SMA 50: ¥{latest['SMA_50']:.2f}")
        print(f"   📊 Stochastic: {latest['Stoch']:.2f}")
        print(f"   📊 Volatility: {latest['Volatility']:.2f}%")
        
        # Test các điều kiện tín hiệu ở các mức độ khác nhau
        print("\n3. Kiểm tra điều kiện tín hiệu...")
        
        # Test strict mode
        strict_conditions = [
            ("SMA 20 > SMA 50", latest['SMA_20'] > latest['SMA_50']),
            ("RSI < 65", latest['RSI'] < 65),
            ("MACD > Signal", latest['MACD'] > latest['MACD_signal']),
            ("Close < BB High", latest['close'] < latest['BB_high']),
            ("Stoch < 80", latest['Stoch'] < 80),
            ("Volatility < 5", latest['Volatility'] < 5)
        ]
        
        print("   🔸 Strict Mode:")
        strict_count = 0
        for condition, result in strict_conditions:
            status = "✅" if result else "❌"
            print(f"     {status} {condition}")
            if result:
                strict_count += 1
        print(f"   🎯 Strict Score: {strict_count}/6")
        
        # Test flexible mode (3/6 điều kiện)
        flexible_pass = strict_count >= 3
        print(f"   🔸 Flexible Mode: {'✅ PASS' if flexible_pass else '❌ FAIL'} ({strict_count}/6 >= 3)")
        
        # Test LSTM prediction
        print("\n4. Test dự đoán LSTM...")
        try:
            predicted_price = predict_price_simple(df)
            if predicted_price:
                current_price = latest['close']
                profit_potential = (predicted_price - current_price) / current_price * 100
                print(f"   ✅ LSTM dự đoán: ¥{predicted_price:.2f}")
                print(f"   📈 Profit potential: {profit_potential:.3f}%")
                
                # Test với các ngưỡng profit khác nhau
                for threshold in [0.01, 0.05, 0.1, 0.15, 0.2, 0.3]:
                    status = "✅" if profit_potential >= threshold else "❌"
                    print(f"     {status} Profit >= {threshold}%")
            else:
                print("   ❌ LSTM prediction failed")
                return False
        except Exception as e:
            print(f"   ❌ LSTM error: {e}")
            return False
        
        # Test với win rate giả định
        print("\n5. Test với win rate giả định...")
        fake_win_rates = [50, 40, 30, 20, 10, 5, 0]
        for win_rate in fake_win_rates:
            status = "✅" if win_rate <= 50 else "❌"  # Giả định win rate = 50%
            print(f"   {status} Win Rate >= {win_rate}%")
        
        print("\n🎯 KẾT LUẬN:")
        if strict_count >= 6:
            print("   ✅ Coin này có thể PASS ở strict mode")
        elif strict_count >= 3:
            print("   ⚠️ Coin này có thể PASS ở flexible mode")
        else:
            print("   ❌ Coin này cần lstm_only mode")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi debug: {e}")
        return False

def predict_price_simple(df, look_back=20):  # Giảm từ 60 xuống 20
    """Simplified LSTM prediction"""
    try:
        if len(df) < look_back:
            return None
        
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df['close'].values.reshape(-1, 1))
        
        X, y = [], []
        for i in range(look_back, len(scaled_data)):
            X.append(scaled_data[i-look_back:i, 0])
            y.append(scaled_data[i, 0])
        X, y = np.array(X), np.array(y)
        
        if len(X) == 0:
            return None
        
        train_size = int(len(X) * 0.8)
        if train_size == 0:
            return None
            
        X_train, y_train = X[:train_size], y[:train_size]
        
        X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
        
        # Simplified LSTM model
        model = Sequential()
        model.add(LSTM(units=20, input_shape=(X_train.shape[1], 1)))  # Reduced complexity
        model.add(Dense(units=1))
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        model.fit(X_train, y_train, epochs=5, batch_size=16, verbose=0)  # Reduced epochs
        
        last_sequence = df['close'].values[-look_back:]
        last_sequence = scaler.transform(last_sequence.reshape(-1, 1))
        last_sequence = last_sequence.reshape((1, look_back, 1))
        
        predicted_scaled = model.predict(last_sequence, verbose=0)
        predicted_price = scaler.inverse_transform(predicted_scaled)[0][0]
        
        # Kiểm tra giá dự đoán có hợp lý không
        current_price = df['close'].iloc[-1]
        if predicted_price <= 0 or predicted_price > current_price * 3:  # Relaxed check
            return None
            
        return predicted_price
    except Exception as e:
        print(f"Lỗi LSTM: {e}")
        return None

def test_multiple_coins():
    """Test nhiều coins để tìm pattern"""
    print("\n🔍 TEST NHIỀU COINS")
    print("=" * 60)
    
    try:
        markets = binance.load_markets()
        jpy_pairs = [symbol for symbol in markets if symbol.endswith('/JPY')][:5]  # Test 5 coins đầu
        
        for symbol in jpy_pairs:
            print(f"\n--- {symbol} ---")
            debug_single_coin(symbol, '1h')
            print()
            
    except Exception as e:
        print(f"Lỗi test multiple coins: {e}")

if __name__ == "__main__":
    print("🚀 CHẠY DEBUG PHÂN TÍCH CRYPTO")
    print("=" * 60)
    
    # Test BTC/JPY trước
    debug_single_coin('BTC/JPY', '1h')
    
    # Uncomment để test nhiều coins
    # test_multiple_coins()
