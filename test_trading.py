#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script cho Auto Trading System
Kiểm tra kết nối và cấu hình trước khi trading thật
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ccxt
import trading_config

def test_binance_connection():
    """Test kết nối Binance API"""
    print("🔍 Testing Binance API Connection...")
    
    try:
        # Kiểm tra cấu hình
        config = trading_config.BINANCE_CONFIG
        if config['apiKey'] == 'YOUR_TESTNET_API_KEY_HERE':
            print("❌ Chưa cấu hình API Key! Vui lòng cập nhật trading_config.py")
            return False
        
        # Tạo connection
        exchange = ccxt.binance(config)
        
        # Test kết nối
        balance = exchange.fetch_balance()
        print(f"✅ Kết nối thành công!")
        print(f"📊 Số dư USDT: ${balance.get('USDT', {}).get('free', 0):.2f}")
        
        # Kiểm tra sandbox mode
        if config.get('sandbox', False):
            print("✅ Đang sử dụng TESTNET (an toàn)")
        else:
            print("⚠️ CẢNH BÁO: Đang sử dụng LIVE TRADING!")
            
        return True
        
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return False

def test_market_data():
    """Test lấy dữ liệu thị trường"""
    print("\n🔍 Testing Market Data...")
    
    try:
        exchange = ccxt.binance(trading_config.BINANCE_CONFIG)
        
        # Test các cặp trading
        test_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        
        for pair in test_pairs:
            try:
                ticker = exchange.fetch_ticker(pair)
                print(f"✅ {pair}: ${ticker['last']:.4f}")
            except Exception as e:
                print(f"❌ {pair}: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Lỗi lấy dữ liệu: {e}")
        return False

def test_trading_config():
    """Test cấu hình trading"""
    print("\n🔍 Testing Trading Configuration...")
    
    config = trading_config.TRADING_CONFIG
    
    # Kiểm tra các cấu hình quan trọng
    checks = [
        ('enabled', config.get('enabled', False), "Trading enabled"),
        ('max_trades', config.get('max_trades', 0) > 0, "Max trades > 0"),
        ('min_order_value', config.get('min_order_value', 0) > 0, "Min order value > 0"),
        ('risk_per_trade', 0 < config.get('risk_per_trade', 0) <= 1, "Risk per trade valid"),
    ]
    
    all_good = True
    for key, condition, description in checks:
        if condition:
            print(f"✅ {description}: {config.get(key)}")
        else:
            print(f"❌ {description}: {config.get(key)}")
            all_good = False
    
    return all_good

def test_price_conversion():
    """Test chuyển đổi giá JPY <-> USDT"""
    print("\n🔍 Testing Price Conversion...")
    
    try:
        # Test conversion function (simulate)
        jpy_price = 150.0  # 150 JPY
        conversion_rate = trading_config.PRICE_CONVERSION['default_jpy_to_usd']
        usdt_price = jpy_price * conversion_rate
        
        print(f"✅ JPY to USDT conversion:")
        print(f"   ¥{jpy_price} -> ${usdt_price:.4f}")
        print(f"   Rate: {conversion_rate}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi chuyển đổi: {e}")
        return False

def run_comprehensive_test():
    """Chạy tất cả các test"""
    print("🚀 BẮT ĐẦU COMPREHENSIVE TEST")
    print("=" * 60)
    
    tests = [
        ("Binance Connection", test_binance_connection),
        ("Market Data", test_market_data),
        ("Trading Config", test_trading_config),
        ("Price Conversion", test_price_conversion),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Tổng kết
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ TEST")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Tổng kết: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 TẤT CẢ TESTS ĐỀU PASS!")
        print("✅ Hệ thống sẵn sàng cho trading")
        
        if trading_config.TRADING_CONFIG.get('enabled', False):
            print("\n⚠️ CẢNH BÁO: Auto trading đang BẬT")
            print("💡 Nếu đây là lần đầu, hãy:")
            print("   1. Kiểm tra lại tất cả cấu hình")
            print("   2. Test với số tiền nhỏ")
            print("   3. Theo dõi sát sao")
        else:
            print("\n💡 Auto trading đang TẮT")
            print("   Đặt TRADING_CONFIG['enabled'] = True để bật")
    else:
        print("❌ CÓ LỖI TRONG HỆ THỐNG")
        print("💡 Vui lòng sửa các lỗi trước khi trading")

if __name__ == "__main__":
    run_comprehensive_test()
