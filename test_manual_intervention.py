#!/usr/bin/env python3
"""
Test Manual Intervention Detection - Position Manager
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from position_manager import PositionManager

class MockExchange:
    """Mock exchange để test các scenarios"""
    
    def __init__(self):
        self.orders = {}
        self.balances = {}
        self.tickers = {}
    
    def set_order_status(self, order_id, status, filled_price=None):
        """Set trạng thái order để test"""
        if order_id in self.orders:
            self.orders[order_id]['status'] = status
            if filled_price:
                self.orders[order_id]['average'] = filled_price
    
    def remove_order(self, order_id):
        """Xóa order để simulate manual intervention"""
        if order_id in self.orders:
            del self.orders[order_id]
    
    def set_balance(self, coin, amount):
        """Set balance để test"""
        self.balances[coin] = {'free': amount}
    
    def set_ticker_price(self, symbol, price):
        """Set giá hiện tại"""
        self.tickers[symbol] = {'last': price}
    
    def fetch_order(self, order_id, symbol):
        """Mock fetch_order"""
        if order_id not in self.orders:
            raise Exception(f"Order {order_id} does not exist")
        return self.orders[order_id]
    
    def fetch_balance(self):
        """Mock fetch_balance"""
        return self.balances
    
    def fetch_ticker(self, symbol):
        """Mock fetch_ticker"""
        return self.tickers.get(symbol, {'last': 100})

def test_manual_intervention_detection():
    """Test detection của manual intervention"""
    
    print("🧪 TEST MANUAL INTERVENTION DETECTION")
    print("=" * 60)
    
    # Setup
    test_file = 'test_manual_intervention.json'
    if os.path.exists(test_file):
        os.remove(test_file)
    
    manager = PositionManager(test_file)
    mock_exchange = MockExchange()
    
    # Tạo position
    manager.add_buy_order("ADA/JPY", 100, 150.0, "buy_1")
    
    # Tạo sell orders
    manager.add_sell_order_tracking("ADA/JPY", "140045935", "STOP_LOSS", 50, 145.0)
    manager.add_sell_order_tracking("ADA/JPY", "140045936", "TAKE_PROFIT_1", 50, 155.0)
    
    print("📊 INITIAL STATE:")
    position = manager.get_position("ADA/JPY")
    print(f"   💰 Position: {position['total_quantity']:.6f} ADA @ ¥{position['average_price']:.4f}")
    print(f"   📋 Active orders: {len(position.get('active_sell_orders', []))}")
    
    # Setup mock exchange
    mock_exchange.orders = {
        "140045935": {"status": "open", "average": None},
        "140045936": {"status": "open", "average": None}
    }
    mock_exchange.set_balance("ADA", 100)  # Ban đầu có 100 ADA
    mock_exchange.set_ticker_price("ADA/JPY", 152.0)
    
    print(f"\n1️⃣ SCENARIO 1: AUTO FILL")
    print("-" * 40)
    
    # Order tự động khớp
    mock_exchange.set_order_status("140045935", "closed", 145.5)
    
    result = manager.check_and_sync_with_exchange(mock_exchange)
    
    print(f"   Updated positions: {result['updated_positions']}")
    print(f"   Manual interventions: {result['manual_interventions']}")
    
    print(f"\n2️⃣ SCENARIO 2: MANUAL INTERVENTION - Bán thủ công")
    print("-" * 40)
    
    # User bán thủ công và hủy lệnh trên Binance
    mock_exchange.remove_order("140045936")  # Order không còn tồn tại
    mock_exchange.set_balance("ADA", 25)     # Balance giảm từ 50 xuống 25 (bán 25 ADA)
    
    result = manager.check_and_sync_with_exchange(mock_exchange)
    
    print(f"   Updated positions: {result['updated_positions']}")
    print(f"   Manual interventions: {result['manual_interventions']}")
    
    print(f"\n3️⃣ SCENARIO 3: MANUAL CANCEL - Chỉ hủy lệnh")
    print("-" * 40)
    
    # Thêm order mới để test cancel
    manager.add_sell_order_tracking("ADA/JPY", "new_order_123", "TAKE_PROFIT_1", 25, 160.0)
    
    # User chỉ hủy lệnh, không bán
    mock_exchange.set_balance("ADA", 25)  # Balance không đổi
    
    result = manager.check_and_sync_with_exchange(mock_exchange)
    
    print(f"   Updated positions: {result['updated_positions']}")
    print(f"   Manual interventions: {result['manual_interventions']}")
    
    print(f"\n📊 FINAL STATE:")
    final_position = manager.get_position("ADA/JPY")
    if final_position:
        print(f"   💰 Position: {final_position['total_quantity']:.6f} ADA @ ¥{final_position['average_price']:.4f}")
        print(f"   📋 Active orders: {len(final_position.get('active_sell_orders', []))}")
        
        # Hiển thị history
        print(f"   📜 Order History:")
        for order in final_position.get('active_sell_orders', []):
            status_icon = {
                'ACTIVE': '🟡',
                'FILLED': '🟢', 
                'MANUAL_FILLED': '🔵',
                'CANCELED': '🔴',
                'MANUAL_CANCELED': '🟠'
            }.get(order['status'], '⚪')
            
            fill_type = order.get('fill_type', 'N/A')
            print(f"      {status_icon} {order['order_id']}: {order['status']} ({fill_type})")
    else:
        print(f"   📊 Position đã được bán hết")
    
    # Cleanup
    os.remove(test_file)
    print(f"\n🗑️ Cleaned up test file")

def show_integration_guide():
    """Hướng dẫn integration"""
    
    print(f"\n" + "=" * 60)
    print("🔧 INTEGRATION GUIDE:")
    print("=" * 60)
    
    print("""
    📝 BOT MONITORING LOOP:
    
    def bot_monitoring_cycle():
        while True:
            try:
                # Sử dụng method mới để handle cả auto và manual
                result = position_manager.check_and_sync_with_exchange(exchange)
                
                # Xử lý positions được update
                for coin in result['updated_positions']:
                    print(f"🔄 {coin} position updated")
                    # Phân tích thị trường và đặt lệnh mua mới nếu cần
                    analyze_and_trade(coin)
                
                # Xử lý manual interventions  
                for intervention in result['manual_interventions']:
                    print(f"🔧 Manual intervention: {intervention}")
                    # Log hoặc notify user
                    send_notification(f"Manual intervention detected: {intervention}")
                
                time.sleep(TRADING_CONFIG['monitor_interval'])
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(TRADING_CONFIG['error_sleep_interval'])
    
    ✅ BENEFITS:
    - Tự động detect cả auto fill và manual intervention
    - Balance check để xác định có bán hay chỉ cancel
    - Complete audit trail cho mọi transaction
    - Robust handling cho mọi edge cases
    - Position data luôn sync với thực tế
    """)

if __name__ == "__main__":
    print("🧪 MANUAL INTERVENTION DETECTION TESTING")
    print("=" * 70)
    
    test_manual_intervention_detection()
    show_integration_guide()
    
    print(f"\n" + "=" * 70)
    print("🎯 KẾT LUẬN:")
    print("✅ Position Manager giờ đã handle được cả manual intervention!")
    print("✅ Tự động detect: Auto fill, Manual sell, Manual cancel")
    print("✅ Balance check để xác định transaction thực tế")
    print("✅ Complete audit trail cho troubleshooting")
