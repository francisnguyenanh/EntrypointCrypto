"""
Script để kiểm tra và test các thư viện
"""
import sys

def test_imports():
    """Test tất cả các imports cần thiết"""
    
    print("🔍 Đang kiểm tra các thư viện...")
    
    # Test basic imports
    try:
        import pandas as pd
        print("✅ pandas: OK")
    except ImportError as e:
        print(f"❌ pandas: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ numpy: OK")
    except ImportError as e:
        print(f"❌ numpy: {e}")
        return False
    
    try:
        import ccxt
        print("✅ ccxt: OK")
    except ImportError as e:
        print(f"❌ ccxt: {e}")
        return False
    
    try:
        import ta
        print("✅ ta: OK")
    except ImportError as e:
        print(f"❌ ta: {e}")
        return False
    
    try:
        from sklearn.preprocessing import MinMaxScaler
        print("✅ sklearn: OK")
    except ImportError as e:
        print(f"❌ sklearn: {e}")
        return False
    
    try:
        import tensorflow as tf
        print(f"✅ tensorflow: OK (version {tf.__version__})")
    except ImportError as e:
        print(f"❌ tensorflow: {e}")
        return False
    
    try:
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        print("✅ tensorflow.keras: OK")
    except ImportError as e:
        print(f"❌ tensorflow.keras: {e}")
        return False
    
    try:
        import vectorbt as vbt
        print("✅ vectorbt: OK")
    except ImportError as e:
        print(f"❌ vectorbt: {e}")
        return False
    
    print("\n🎉 Tất cả thư viện đã được cài đặt thành công!")
    return True

def test_binance_connection():
    """Test kết nối Binance"""
    try:
        import ccxt
        binance = ccxt.binance()
        markets = binance.load_markets()
        jpy_pairs = [symbol for symbol in markets if symbol.endswith('/JPY')]
        print(f"🌐 Kết nối Binance: OK ({len(jpy_pairs)} cặp JPY)")
        return True
    except Exception as e:
        print(f"❌ Lỗi kết nối Binance: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("KIỂM TRA HỆ THỐNG EntrypointCrypto")
    print("=" * 50)
    
    if test_imports():
        test_binance_connection()
    else:
        print("\n📦 Vui lòng cài đặt các thư viện thiếu:")
        print("pip install -r requirements.txt")
    
    print("\n" + "=" * 50)
