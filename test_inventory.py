#!/usr/bin/env python3
"""
Test script để kiểm tra hàm xử lý tồn kho
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import handle_inventory_coins, get_account_balance
import trading_config

def test_inventory_handling():
    """Test hàm xử lý tồn kho"""
    
    print("🧪 TESTING INVENTORY HANDLING")
    print("=" * 50)
    
    # 1. Kiểm tra số dư ban đầu
    initial_jpy_balance = get_account_balance()
    print(f"💰 Số dư JPY ban đầu: ¥{initial_jpy_balance:,.2f}")
    
    # 2. Test hàm xử lý tồn kho
    print("\n🔄 Testing handle_inventory_coins()...")
    result = handle_inventory_coins()
    
    # 3. Kiểm tra số dư sau xử lý
    final_jpy_balance = get_account_balance()
    print(f"💰 Số dư JPY sau xử lý: ¥{final_jpy_balance:,.2f}")
    
    # 4. Tổng kết
    difference = final_jpy_balance - initial_jpy_balance
    print(f"\n📊 TỔNG KẾT TEST:")
    print(f"✅ Hàm chạy: {'SUCCESS' if result else 'FAILED'}")
    print(f"💰 Thay đổi số dư: ¥{difference:+,.2f}")
    
    if difference > 0:
        print("🏆 Đã thu về JPY từ việc bán coin tồn kho")
    elif difference == 0:
        print("✅ Không có coin tồn kho hoặc không thay đổi số dư")
    else:
        print("⚠️ Số dư giảm - có thể do phí giao dịch")
    
    print("=" * 50)

if __name__ == "__main__":
    test_inventory_handling()
