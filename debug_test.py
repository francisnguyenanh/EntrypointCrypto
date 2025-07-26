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

# Tắt warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.get_logger().setLevel('ERROR')

# Khởi tạo Binance API
binance = ccxt.binance()

def test_single_coin():
    try:
        print("🔍 Test debug cho 1 coin...")
        
        # Lấy dữ liệu BTC/JPY
        symbol = 'BTC/JPY'
        ohlcv = binance.fetch_ohlcv(symbol, '1m', limit=1000)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        print(f"✅ Lấy được {len(df)} dòng dữ liệu cho {symbol}")
        print(f"Giá hiện tại: ¥{df['close'].iloc[-1]:.2f}")
        
        # Test LSTM
        if len(df) < 200:
            print("❌ Không đủ dữ liệu")
            return
            
        # Chuẩn bị dữ liệu LSTM
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df['close'].values.reshape(-1, 1))
        
        X, y = [], []
        look_back = 60
        for i in range(look_back, len(scaled_data)):
            X.append(scaled_data[i-look_back:i, 0])
            y.append(scaled_data[i, 0])
        X, y = np.array(X), np.array(y)
        
        print(f"✅ Chuẩn bị LSTM: {len(X)} samples")
        
        if len(X) == 0:
            print("❌ Không có dữ liệu training")
            return
            
        train_size = int(len(X) * 0.8)
        X_train, y_train = X[:train_size], y[:train_size]
        X_test, y_test = X[train_size:], y[train_size:]
        
        X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
        X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))
        
        print(f"✅ Train shape: {X_train.shape}, Test shape: {X_test.shape}")
        
        # Xây dựng mô hình LSTM
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50))
        model.add(Dropout(0.2))
        model.add(Dense(units=1))
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        print("🧠 Đang training LSTM...")
        model.fit(X_train, y_train, epochs=5, batch_size=32, verbose=1)
        
        # Dự đoán
        last_sequence = df['close'].values[-look_back:]
        last_sequence = scaler.transform(last_sequence.reshape(-1, 1))
        last_sequence = last_sequence.reshape((1, look_back, 1))
        
        predicted_scaled = model.predict(last_sequence, verbose=0)
        predicted_price = scaler.inverse_transform(predicted_scaled)[0][0]
        
        current_price = df['close'].iloc[-1]
        profit_potential = (predicted_price - current_price) / current_price * 100
        
        print(f"🔮 Dự đoán LSTM:")
        print(f"   Giá hiện tại: ¥{current_price:.2f}")
        print(f"   Giá dự đoán: ¥{predicted_price:.2f}")
        print(f"   Tiềm năng lợi nhuận: {profit_potential:.2f}%")
        
        # Test technical indicators
        df_resample = df.resample('1H').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()
        
        print(f"✅ Resampled data: {len(df_resample)} rows")
        
        if len(df_resample) < 200:
            print("❌ Không đủ dữ liệu cho technical indicators")
            return
            
        # Tính các chỉ số kỹ thuật
        df_resample['SMA_50'] = SMAIndicator(df_resample['close'], window=50).sma_indicator()
        df_resample['SMA_200'] = SMAIndicator(df_resample['close'], window=200).sma_indicator()
        df_resample['RSI'] = RSIIndicator(df_resample['close'], window=14).rsi()
        macd = MACD(df_resample['close'])
        df_resample['MACD'] = macd.macd()
        df_resample['MACD_signal'] = macd.macd_signal()
        bb = BollingerBands(df_resample['close'], window=20, window_dev=2)
        df_resample['BB_high'] = bb.bollinger_hband()
        df_resample['BB_low'] = bb.bollinger_lband()
        stoch = StochasticOscillator(df_resample['close'], df_resample['high'], df_resample['low'], window=14)
        df_resample['Stoch'] = stoch.stoch()
        df_resample['Volatility'] = (df_resample['high'] - df_resample['low']) / df_resample['close'] * 100
        
        # Tín hiệu mua/bán
        latest_data = df_resample.iloc[-1]
        
        print(f"📊 Technical Indicators:")
        print(f"   SMA 50: ¥{latest_data['SMA_50']:.2f}")
        print(f"   SMA 200: ¥{latest_data['SMA_200']:.2f}")
        print(f"   RSI: {latest_data['RSI']:.2f}")
        print(f"   MACD: {latest_data['MACD']:.4f}")
        print(f"   MACD Signal: {latest_data['MACD_signal']:.4f}")
        print(f"   BB High: ¥{latest_data['BB_high']:.2f}")
        print(f"   BB Low: ¥{latest_data['BB_low']:.2f}")
        print(f"   Stochastic: {latest_data['Stoch']:.2f}")
        print(f"   Volatility: {latest_data['Volatility']:.2f}%")
        
        # Kiểm tra điều kiện tín hiệu mua
        conditions = {
            'SMA_50 > SMA_200': latest_data['SMA_50'] > latest_data['SMA_200'],
            'RSI < 65': latest_data['RSI'] < 65,
            'MACD > MACD_signal': latest_data['MACD'] > latest_data['MACD_signal'],
            'Close < BB_high': latest_data['close'] < latest_data['BB_high'],
            'Stoch < 80': latest_data['Stoch'] < 80,
            'Volatility < 5': latest_data['Volatility'] < 5
        }
        
        print(f"🚦 Điều kiện tín hiệu mua:")
        for condition, result in conditions.items():
            status = "✅" if result else "❌"
            print(f"   {status} {condition}: {result}")
        
        buy_signal = all(conditions.values())
        print(f"🎯 Tín hiệu mua: {'CÓ' if buy_signal else 'KHÔNG'}")
        
        if buy_signal and profit_potential >= 0.1:
            print("🚀 Coin này có thể vào lệnh!")
        else:
            print("⏳ Coin này chưa phù hợp để vào lệnh")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_coin()
