#!/usr/bin/env python3
"""
Integration example: Position Manager với Active Orders Tracking
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from position_manager import PositionManager

def integrate_with_trading_bot():
    """Ví dụ integration với trading bot"""
    
    print("🤖 INTEGRATION: POSITION MANAGER + ACTIVE ORDERS TRACKING")
    print("=" * 70)
    
    # Khởi tạo position manager
    position_manager = PositionManager('position_data.json')
    
    print("\n1️⃣ FLOW KHI ĐẶT LỆNH MUA:")
    print("-" * 50)
    
    # Bot đặt lệnh mua thành công
    symbol = "ADA/JPY"
    buy_quantity = 100
    buy_price = 150.0
    buy_order_id = "buy_123"
    
    # 1. Track position
    position_manager.add_buy_order(symbol, buy_quantity, buy_price, buy_order_id)
    
    print(f"✅ Đã track buy order: {buy_quantity} {symbol.split('/')[0]} @ ¥{buy_price}")
    
    print("\n2️⃣ FLOW KHI ĐẶT LỆNH BÁN (SL/TP):")
    print("-" * 50)
    
    # Bot tính SL/TP từ position
    sl_tp = position_manager.calculate_sl_tp_prices(symbol, sl_percent=3, tp1_percent=0.4, tp2_percent=5)
    
    # Giả lập đặt lệnh SL/TP thành công trên exchange
    sl_order_id = "140045935"  # Từ active_orders.json
    tp_order_id = "140045936"
    
    # 2. Track sell orders
    position_manager.add_sell_order_tracking(
        symbol, sl_order_id, "STOP_LOSS", 
        buy_quantity, sl_tp['stop_loss']
    )
    
    position_manager.add_sell_order_tracking(
        symbol, tp_order_id, "TAKE_PROFIT_1", 
        buy_quantity, sl_tp['tp1_price']
    )
    
    print(f"✅ Đã track SL order: {sl_order_id} @ ¥{sl_tp['stop_loss']:.4f}")
    print(f"✅ Đã track TP order: {tp_order_id} @ ¥{sl_tp['tp1_price']:.4f}")
    
    print("\n3️⃣ MONITORING LOOP (Chạy định kỳ trong bot):")
    print("-" * 50)
    
    print("""
    🔄 Bot monitoring loop:
    
    def bot_monitoring_cycle():
        while True:
            try:
                # 1. Kiểm tra các lệnh bán đã khớp chưa
                updated_positions = position_manager.check_and_update_filled_orders(exchange)
                
                if updated_positions:
                    print(f"🎉 Có lệnh bán khớp cho: {updated_positions}")
                    
                    # 2. Nếu có lệnh khớp, phân tích thị trường và đặt lệnh mua mới
                    for coin in updated_positions:
                        analyze_and_place_new_buy_order(coin)
                
                # 3. Sleep theo config
                time.sleep(TRADING_CONFIG['monitor_interval'])
                
            except Exception as e:
                print(f"❌ Lỗi monitoring: {e}")
                time.sleep(TRADING_CONFIG['error_sleep_interval'])
    """)
    
    print("\n4️⃣ HIỂN THỊ POSITION VỚI ACTIVE ORDERS:")
    print("-" * 50)
    
    # Hiển thị position với sell orders
    positions = position_manager.get_all_positions()
    
    for symbol, pos in positions.items():
        coin = symbol.replace('/JPY', '')
        print(f"\n📊 {coin} Position:")
        print(f"   💰 {pos['total_quantity']:.6f} @ ¥{pos['average_price']:.4f}")
        print(f"   💸 Cost: ¥{pos['total_cost']:,.2f}")
        
        # Hiển thị active sell orders
        active_orders = pos.get('active_sell_orders', [])
        if active_orders:
            print(f"   📋 Active Sell Orders:")
            for order in active_orders:
                status_icon = "🟡" if order['status'] == 'ACTIVE' else "🟢"
                print(f"      {status_icon} {order['order_type']}: {order['quantity']:.6f} @ ¥{order['price']:.4f}")
        else:
            print(f"   📋 No active sell orders")

def show_integration_benefits():
    """Hiển thị lợi ích của integration"""
    
    print(f"\n" + "=" * 70)
    print("🎯 BENEFITS CỦA INTEGRATION:")
    print("=" * 70)
    
    print("""
    ✅ AUTOMATIC POSITION UPDATES:
       - Bot tự động update position_data.json khi lệnh bán khớp
       - Không cần manual intervention
       - Luôn đồng bộ với thực tế trên exchange
    
    ✅ COMPLETE TRACKING:
       - Track cả buy orders (position) và sell orders (active)
       - Liên kết chặt chẽ giữa position và orders
       - History đầy đủ cho mọi transaction
    
    ✅ SMART MONITORING:
       - Bot chỉ kiểm tra orders có liên quan đến positions
       - Efficient API usage (không check tất cả orders)
       - Auto cleanup orders cũ
    
    ✅ SEAMLESS WORKFLOW:
       1. Mua coin → Track position
       2. Đặt SL/TP → Track sell orders  
       3. Lệnh khớp → Auto update position
       4. Phân tích thị trường → Đặt lệnh mua mới
       5. Repeat...
    
    ✅ DATA INTEGRITY:
       - Position data luôn chính xác
       - SL/TP calculation dựa trên weighted average đúng
       - P&L tracking realtime
       - File size được kiểm soát (auto cleanup)
    """)

if __name__ == "__main__":
    print("🧪 POSITION MANAGER + ACTIVE ORDERS INTEGRATION")  
    print("=" * 70)
    
    integrate_with_trading_bot()
    show_integration_benefits()
    
    print(f"\n" + "=" * 70)
    print("✅ READY FOR PRODUCTION!")
    print("Position Manager giờ đã có thể tự động update khi lệnh bán khớp!")
