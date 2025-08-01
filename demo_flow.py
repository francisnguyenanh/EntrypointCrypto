#!/usr/bin/env python3
"""
Test script để mô phỏng tình huống có coin tồn kho lớn hơn
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import handle_inventory_coins, cancel_all_open_orders, get_account_balance

def demo_inventory_handling():
    """Demo flow xử lý tồn kho trong trading session"""
    
    print("🎬 DEMO: XỬ LÝ TỒN KHO TRONG TRADING SESSION")
    print("=" * 60)
    
    # Mô phỏng tình huống có lệnh cũ và coin tồn kho
    print("🔄 BƯỚC 1: XỬ LÝ LỆNH CŨ VÀ TỒN KHO")
    
    # 1. Kiểm tra số dư ban đầu
    initial_balance = get_account_balance()
    print(f"💰 Số dư JPY ban đầu: ¥{initial_balance:,.2f}")
    
    # 2. Hủy lệnh cũ
    print("\n🗑️ Hủy lệnh cũ...")
    cancel_all_open_orders()
    
    # 3. Xử lý tồn kho
    print("\n📦 Xử lý coin tồn kho...")
    inventory_result = handle_inventory_coins()
    
    # 4. Kiểm tra số dư sau xử lý
    final_balance = get_account_balance()
    print(f"💰 Số dư JPY sau xử lý: ¥{final_balance:,.2f}")
    
    # 5. Tổng kết
    balance_change = final_balance - initial_balance
    print(f"\n📊 KẾT QUẢ BƯỚC 1:")
    print(f"✅ Xử lý tồn kho: {'THÀNH CÔNG' if inventory_result else 'HOÀN TẤT'}")
    print(f"💰 Thay đổi số dư: ¥{balance_change:+,.2f}")
    
    if balance_change > 0:
        print("🏆 Đã thu về JPY từ việc bán tồn kho → Sẵn sàng trading mới")
    elif balance_change == 0:
        print("✅ Không có tồn kho bán được hoặc chỉ có dust → Tiếp tục với số dư hiện tại")
    
    print("\n🔄 BƯỚC 2: PHÂN TÍCH CƠ HỘI MỚI")
    print("(Sẽ tìm kiếm coin mới để đầu tư với toàn bộ số dư JPY)")
    
    print("\n🔄 BƯỚC 3: THỰC HIỆN TRADING MỚI")  
    print("(Sẽ đặt lệnh mua coin mới với SL + TP)")
    
    print("\n🎯 FLOW HOÀN CHỈNH:")
    print("1. Hủy lệnh cũ → 2. Thanh lý tồn kho → 3. Tìm cơ hội mới → 4. Trading mới")
    print("=" * 60)

if __name__ == "__main__":
    demo_inventory_handling()
