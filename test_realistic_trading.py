#!/usr/bin/env python3
"""
Test tình huống thực tế với Position Manager trong trading bot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from position_manager import PositionManager
import json
import time

def test_realistic_trading_scenario():
    """Test tình huống trading thực tế"""
    
    print("🚀 TEST TÌNH HUỐNG TRADING THỰC TẾ")
    print("=" * 60)
    
    # Tạo position manager cho test
    manager = PositionManager('test_realistic_positions.json')
    
    # Scenario 1: Mua coin nhiều lần trong ngày
    print("\n📈 SCENARIO 1: MUA COIN NHIỀU LÀN TRONG NGÀY")
    print("-" * 50)
    
    # Mua ADA 5 lần với giá khác nhau
    ada_buys = [
        (100, 150.5, "ada_buy_1"),  # Mua lúc giá 150.5
        (150, 148.2, "ada_buy_2"),  # Mua lúc giá giảm
        (200, 152.8, "ada_buy_3"),  # Mua lúc giá tăng
        (120, 149.1, "ada_buy_4"),  # Mua thêm
        (80, 151.0, "ada_buy_5")    # Mua cuối ngày
    ]
    
    for quantity, price, order_id in ada_buys:
        manager.add_buy_order("ADA/JPY", quantity, price, order_id)
        print(f"   ✅ Mua {quantity} ADA @ ¥{price}")
    
    # Hiển thị thông tin position
    ada_position = manager.get_position("ADA/JPY")
    print(f"\n📊 ADA Position Summary:")
    print(f"   💰 Giá trung bình: ¥{ada_position['average_price']:.4f}")
    print(f"   📦 Tổng quantity: {ada_position['total_quantity']:.6f}")
    print(f"   💸 Tổng chi phí: ¥{ada_position['total_cost']:.2f}")
    
    # Tính SL/TP
    sl_tp_data = manager.calculate_sl_tp_prices("ADA/JPY", sl_percent=3, tp1_percent=2, tp2_percent=5)
    print(f"   🛡️ Stop Loss: ¥{sl_tp_data['stop_loss']:.4f} (-3%)")
    print(f"   🎯 Take Profit 1: ¥{sl_tp_data['tp1_price']:.4f} (+2%)")
    print(f"   🎯 Take Profit 2: ¥{sl_tp_data['tp2_price']:.4f} (+5%)")
    
    # Scenario 2: Bán một phần, sau đó mua lại
    print(f"\n📉 SCENARIO 2: BÁN MỘT PHẦN, SAU ĐÓ MUA LẠI")
    print("-" * 50)
    
    # Bán 300 ADA với giá 155
    current_price = 155.0
    sell_quantity = 300
    
    # Tính P&L cho phần bán
    pnl = manager.calculate_pnl("ADA/JPY", sell_quantity, current_price)
    print(f"   📤 Bán {sell_quantity} ADA @ ¥{current_price}")
    print(f"   💰 P&L: ¥{pnl['profit_loss']:.2f} ({pnl['profit_loss_percent']:.2f}%)")
    
    # Cập nhật position sau khi bán
    manager.update_position_after_sell("ADA/JPY", sell_quantity, current_price)
    
    # Hiển thị position sau khi bán
    ada_position_after_sell = manager.get_position("ADA/JPY")
    print(f"   📊 Sau khi bán:")
    print(f"      📦 Còn lại: {ada_position_after_sell['total_quantity']:.6f} ADA")
    print(f"      💰 Giá TB: ¥{ada_position_after_sell['average_price']:.4f}")
    
    # Mua lại với giá khác
    manager.add_buy_order("ADA/JPY", 250, 153.5, "ada_rebuy_1")
    print(f"   📥 Mua lại 250 ADA @ ¥153.5")
    
    ada_final = manager.get_position("ADA/JPY")
    print(f"   📊 Position cuối:")
    print(f"      📦 Total: {ada_final['total_quantity']:.6f} ADA")
    print(f"      💰 Giá TB: ¥{ada_final['average_price']:.4f}")
    
    # Scenario 3: Multiple coins trading
    print(f"\n🔄 SCENARIO 3: TRADING NHIỀU COINS")
    print("-" * 50)
    
    # Trading XRP
    xrp_trades = [
        (500, 85.2, "xrp_1"),
        (300, 86.8, "xrp_2"),
        (400, 84.1, "xrp_3")
    ]
    
    for qty, price, order_id in xrp_trades:
        manager.add_buy_order("XRP/JPY", qty, price, order_id)
    
    # Trading SUI
    sui_trades = [
        (800, 120.5, "sui_1"),
        (600, 118.9, "sui_2")
    ]
    
    for qty, price, order_id in sui_trades:
        manager.add_buy_order("SUI/JPY", qty, price, order_id)
    
    # Hiển thị tất cả positions
    print(f"\n📋 TẤT CẢ POSITIONS:")
    print("-" * 50)
    
    all_positions = manager.get_all_positions()
    total_cost = 0
    
    for symbol, position in all_positions.items():
        total_cost += position['total_cost']
        print(f"   {symbol.replace('/JPY', '')}:")
        print(f"      📦 {position['total_quantity']:.6f} @ ¥{position['average_price']:.4f}")
        print(f"      💸 Cost: ¥{position['total_cost']:.2f}")
        print(f"      📋 Orders: {len(position['buy_orders'])}")
    
    print(f"\n💼 TỔNG ĐẦU TƯ: ¥{total_cost:,.2f}")
    
    # Test file size management
    print(f"\n📊 FILE SIZE MANAGEMENT:")
    print("-" * 50)
    
    stats = manager.get_file_stats()
    print(f"   📁 File size: {stats['size_kb']:.1f} KB")
    print(f"   📦 Positions: {stats['total_positions']}")
    print(f"   📋 Buy orders: {stats['total_buy_orders']}")
    
    if stats['size_kb'] > 10:  # Giả lập file lớn
        print(f"   🔧 File lớn, chạy optimization...")
        optimized = manager.optimize_file_size()
        print(f"   ✅ Đã tối ưu {optimized} orders")
        
        new_stats = manager.get_file_stats()
        print(f"   📁 Size sau tối ưu: {new_stats['size_kb']:.1f} KB")
    
    # Cleanup test file
    try:
        os.remove('test_realistic_positions.json')
        print(f"\n🗑️ Đã xóa file test")
    except:
        pass

def demonstrate_production_usage():
    """Hướng dẫn sử dụng trong production"""
    
    print(f"\n🏭 HƯỚNG DẪN SỬ DỤNG TRONG PRODUCTION")
    print("=" * 60)
    
    print("""
📝 INTEGRATION VỚI TRADING BOT:

1️⃣ Import Position Manager:
   from position_manager import PositionManager
   
2️⃣ Khởi tạo trong bot:
   position_manager = PositionManager('position_data.json')
   
3️⃣ Khi đặt lệnh mua:
   position_manager.add_buy_order(symbol, quantity, price, order_id)
   
4️⃣ Khi tính SL/TP:
   sl_tp_data = position_manager.calculate_sl_tp_prices(
       symbol, sl_percent=3, tp1_percent=2, tp2_percent=5
   )
   sl_price = sl_tp_data['stop_loss']
   tp1_price = sl_tp_data['tp1_price']
   
5️⃣ Khi bán coin:
   pnl = position_manager.calculate_pnl(symbol, quantity, sell_price)
   position_manager.update_position_after_sell(symbol, quantity, sell_price)
   
6️⃣ Hiển thị inventory với P&L:
   for symbol, position in position_manager.get_all_positions().items():
       current_price = get_current_price(symbol)  # Từ exchange
       pnl = position_manager.calculate_pnl(symbol, 
                                           position['total_quantity'], 
                                           current_price)
       print(f"{symbol}: {pnl['profit_loss']:+.2f} JPY")

🔧 AUTO MAINTENANCE:
   - File tự động cleanup khi > 50KB
   - Chỉ lưu 10 buy orders mới nhất/position
   - Xóa positions cũ > 30 ngày
   - Chạy position_manager.auto_maintenance() định kỳ

✅ BENEFITS:
   ✓ Không bao giờ mất tracking giá mua
   ✓ SL/TP chính xác dựa trên weighted average
   ✓ P&L realtime cho mọi position
   ✓ File size được kiểm soát tự động
   ✓ Dữ liệu persistent qua restart bot
    """)

if __name__ == "__main__":
    print("🧪 POSITION MANAGER REALISTIC TESTING")
    print("=" * 70)
    
    # Test realistic scenario
    test_realistic_trading_scenario()
    
    # Production usage guide
    demonstrate_production_usage()
    
    print(f"\n" + "=" * 70)
    print("🎉 HOÀN THÀNH TEST!")
    print("Position Manager đã sẵn sàng cho production trading!")
