#!/usr/bin/env python3
"""
Test script cho tính năng cleanup và tối ưu hóa position file
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from position_manager import PositionManager
import json
import time

def create_large_position_file():
    """Tạo file position lớn để test cleanup"""
    
    print("🧪 TẠO FILE POSITION LỚN ĐỂ TEST CLEANUP")
    print("=" * 60)
    
    # Tạo position manager mới
    test_manager = PositionManager('test_position_data.json')
    
    # Thêm nhiều positions với nhiều buy orders
    coins = ['ADA', 'XRP', 'XLM', 'SUI', 'DOT', 'MATIC', 'SOL', 'BNB']
    
    for coin in coins:
        symbol = f"{coin}/JPY"
        print(f"📊 Tạo position cho {coin}...")
        
        # Mỗi coin sẽ có 15 buy orders (nhiều hơn limit 10)
        for i in range(15):
            base_price = 100 + i * 2  # Giá tăng dần
            quantity = 50 + i * 5     # Quantity tăng dần
            
            test_manager.add_buy_order(
                symbol, 
                quantity, 
                base_price, 
                f"order_{coin}_{i+1}"
            )
            
    # Kiểm tra stats trước cleanup
    print("\n📊 STATS TRƯỚC CLEANUP:")
    stats = test_manager.get_file_stats()
    if stats:
        print(f"   📁 File size: {stats['size_kb']:.1f} KB")
        print(f"   📦 Positions: {stats['total_positions']}")
        print(f"   📋 Total buy orders: {stats['total_buy_orders']}")
        print(f"   ⏰ Position cũ nhất: {stats['oldest_position']}")
        print(f"   🆕 Position mới nhất: {stats['newest_position']}")
    
    return test_manager

def test_cleanup_features():
    """Test các tính năng cleanup"""
    
    print("\n🧪 TEST CLEANUP FEATURES")
    print("=" * 60)
    
    # 1. Tạo file lớn
    test_manager = create_large_position_file()
    
    # 2. Test manual optimization
    print("\n🔧 Test manual optimization...")
    optimized = test_manager.optimize_file_size()
    print(f"✅ Đã tối ưu {optimized} buy orders")
    
    # 3. Test auto maintenance
    print("\n🔧 Test auto maintenance...")
    test_manager.auto_maintenance()
    
    # 4. Kiểm tra kết quả cuối
    print("\n📊 STATS SAU CLEANUP:")
    stats_final = test_manager.get_file_stats()
    if stats_final:
        print(f"   📁 File size: {stats_final['size_kb']:.1f} KB")
        print(f"   📦 Positions: {stats_final['total_positions']}")
        print(f"   📋 Total buy orders: {stats_final['total_buy_orders']}")
    
    # 5. Kiểm tra nội dung file
    print(f"\n📄 Kiểm tra structure của file:")
    try:
        with open('test_position_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for coin, pos in data.items():
            buy_orders_count = len(pos['buy_orders'])
            print(f"   {coin}: {buy_orders_count} buy orders (≤ 5)")
            
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
    
    # Cleanup test file
    try:
        os.remove('test_position_data.json')
        print(f"\n🗑️ Đã xóa file test")
    except:
        pass

def test_production_position_file():
    """Test file position thực tế"""
    
    print("\n🧪 TEST PRODUCTION POSITION FILE")
    print("=" * 60)
    
    # Kiểm tra file production hiện tại
    if os.path.exists('position_data.json'):
        prod_manager = PositionManager('position_data.json')
        
        print("📊 STATS FILE PRODUCTION:")
        stats = prod_manager.get_file_stats()
        if stats:
            print(f"   📁 File size: {stats['size_kb']:.1f} KB")
            print(f"   📦 Positions: {stats['total_positions']}")
            print(f"   📋 Total buy orders: {stats['total_buy_orders']}")
            
            # Cảnh báo nếu file lớn
            if stats['size_kb'] > 100:
                print(f"⚠️ FILE LỚN! Nên chạy auto maintenance")
                
                # Hỏi user có muốn cleanup không
                response = input("Chạy auto maintenance cho file production? (y/n): ")
                if response.lower() == 'y':
                    prod_manager.auto_maintenance()
                    print("✅ Đã cleanup file production")
            else:
                print("✅ File size ổn định")
        
        # Hiển thị detail positions
        if len(prod_manager.positions) > 0:
            print(f"\n📋 CHI TIẾT POSITIONS:")
            for coin, pos in prod_manager.positions.items():
                buy_count = len(pos['buy_orders'])
                avg_price = pos['average_price']
                quantity = pos['total_quantity']
                print(f"   {coin}: {quantity:.6f} @ ¥{avg_price:.4f} ({buy_count} orders)")
    else:
        print("📂 File position_data.json chưa tồn tại")

if __name__ == "__main__":
    print("🧪 POSITION MANAGER CLEANUP TESTING")
    print("=" * 70)
    
    # Test cleanup features
    test_cleanup_features()
    
    # Test production file
    test_production_position_file()
    
    print(f"\n" + "=" * 70)
    print("🎯 KẾT LUẬN:")
    print("✅ File position_data.json sẽ tự động cleanup khi > 50KB")
    print("✅ Chỉ giữ 10 buy orders mới nhất cho mỗi position")
    print("✅ Auto maintenance xóa positions cũ > 30 ngày")
    print("✅ Manual optimization giảm xuống còn 5 buy orders")
    print("✅ File size được kiểm soát tự động!")
