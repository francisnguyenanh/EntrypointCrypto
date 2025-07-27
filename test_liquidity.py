#!/usr/bin/env python3
"""
Test script cho tính năng thanh khoản thông minh
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import (
    binance, 
    get_order_book, 
    analyze_order_book, 
    calculate_max_quantity_from_liquidity,
    check_market_impact
)

def test_liquidity_analysis():
    """Test phân tích thanh khoản"""
    print("🧪 Testing Liquidity Analysis...")
    print("=" * 50)
    
    # Test symbols
    test_symbols = ['BTC/JPY', 'ETH/JPY', 'BNB/JPY']
    test_quantities = [0.001, 0.01, 0.1]  # Các size khác nhau
    
    for symbol in test_symbols:
        print(f"\n📊 Testing {symbol}")
        print("-" * 30)
        
        try:
            # Lấy order book
            order_book = get_order_book(symbol, limit=20)
            if not order_book:
                print(f"❌ Không thể lấy order book cho {symbol}")
                continue
            
            # Phân tích order book
            analysis = analyze_order_book(order_book)
            if not analysis:
                print(f"❌ Không thể phân tích order book cho {symbol}")
                continue
            
            print(f"✅ Order Book Analysis:")
            print(f"   💧 Buy liquidity: {analysis['available_liquidity_buy']:.6f}")
            print(f"   💧 Sell liquidity: {analysis['available_liquidity_sell']:.6f}")
            print(f"   📊 Bid volume: {analysis['total_bid_volume']:.6f}")
            print(f"   📊 Ask volume: {analysis['total_ask_volume']:.6f}")
            print(f"   📏 Spread: {analysis['spread']:.3f}%")
            
            # Test với các quantity khác nhau
            for quantity in test_quantities:
                print(f"\n   🎯 Testing quantity: {quantity}")
                
                # Test BUY
                safe_buy_qty, buy_reason = calculate_max_quantity_from_liquidity(
                    symbol, quantity, analysis, side='buy'
                )
                buy_impact = check_market_impact(symbol, safe_buy_qty, analysis, side='buy')
                
                print(f"   📈 BUY: {quantity:.6f} → {safe_buy_qty:.6f} ({buy_impact['impact']}) - {buy_reason}")
                
                # Test SELL
                safe_sell_qty, sell_reason = calculate_max_quantity_from_liquidity(
                    symbol, quantity, analysis, side='sell'
                )
                sell_impact = check_market_impact(symbol, safe_sell_qty, analysis, side='sell')
                
                print(f"   📉 SELL: {quantity:.6f} → {safe_sell_qty:.6f} ({sell_impact['impact']}) - {sell_reason}")
                
        except Exception as e:
            print(f"❌ Lỗi test {symbol}: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Liquidity test completed!")

def test_extreme_cases():
    """Test các trường hợp cực đoan"""
    print("\n🔬 Testing Extreme Cases...")
    print("=" * 50)
    
    # Test với số lượng rất lớn
    symbol = 'BTC/JPY'
    extreme_quantity = 10.0  # 10 BTC - rất lớn
    
    try:
        order_book = get_order_book(symbol, limit=20)
        analysis = analyze_order_book(order_book)
        
        if analysis:
            print(f"\n📊 Testing extreme quantity: {extreme_quantity}")
            
            # Test BUY với số lượng lớn
            safe_buy, buy_reason = calculate_max_quantity_from_liquidity(
                symbol, extreme_quantity, analysis, side='buy'
            )
            buy_impact = check_market_impact(symbol, safe_buy, analysis, side='buy')
            
            print(f"📈 Extreme BUY: {extreme_quantity} → {safe_buy:.6f}")
            print(f"   Reason: {buy_reason}")
            print(f"   Impact: {buy_impact['impact']}")
            print(f"   Warnings: {buy_impact.get('warnings', [])}")
            
            # Test SELL với số lượng lớn
            safe_sell, sell_reason = calculate_max_quantity_from_liquidity(
                symbol, extreme_quantity, analysis, side='sell'
            )
            sell_impact = check_market_impact(symbol, safe_sell, analysis, side='sell')
            
            print(f"📉 Extreme SELL: {extreme_quantity} → {safe_sell:.6f}")
            print(f"   Reason: {sell_reason}")
            print(f"   Impact: {sell_impact['impact']}")
            print(f"   Warnings: {sell_impact.get('warnings', [])}")
            
    except Exception as e:
        print(f"❌ Lỗi test extreme cases: {e}")

if __name__ == "__main__":
    print("🚀 Starting Liquidity System Tests")
    print("=" * 50)
    
    try:
        # Kiểm tra kết nối
        if binance:
            print("✅ Binance connection OK")
            
            # Chạy tests
            test_liquidity_analysis()
            test_extreme_cases()
            
            print("\n🎉 All tests completed!")
            
        else:
            print("❌ Không thể kết nối Binance")
            
    except Exception as e:
        print(f"❌ Lỗi chung: {e}")
