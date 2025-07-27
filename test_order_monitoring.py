#!/usr/bin/env python3
"""
Test script để kiểm tra hệ thống theo dõi lệnh bán
"""

import time
import sys
import os

# Thêm đường dẫn để import từ module chính
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import các hàm từ app.py
try:
    from app import (
        show_active_orders, 
        check_all_orders_now, 
        add_order_to_monitor,
        remove_order_from_monitor,
        stop_order_monitor,
        ACTIVE_ORDERS
    )
    print("✅ Import thành công từ app.py")
except ImportError as e:
    print(f"❌ Lỗi import: {e}")
    sys.exit(1)

def test_order_monitoring():
    """Test các chức năng theo dõi lệnh"""
    
    print("\n" + "="*60)
    print("🧪 KIỂM TRA HỆ THỐNG THEO DÕI LỆNH")
    print("="*60)
    
    # 1. Hiển thị danh sách lệnh hiện tại
    print("\n1️⃣ Kiểm tra danh sách lệnh hiện tại:")
    show_active_orders()
    
    # 2. Thêm lệnh test (giả lập)
    print("\n2️⃣ Thêm lệnh test vào danh sách theo dõi:")
    test_order_id = "test_order_123456"
    add_order_to_monitor(
        order_id=test_order_id,
        symbol="ADA/JPY", 
        order_type="TAKE_PROFIT",
        buy_price=100.5
    )
    
    # 3. Hiển thị lại sau khi thêm
    print("\n3️⃣ Danh sách sau khi thêm lệnh test:")
    show_active_orders()
    
    # 4. Kiểm tra trạng thái tất cả lệnh
    print("\n4️⃣ Kiểm tra trạng thái tất cả lệnh:")
    check_all_orders_now()
    
    # 5. Xóa lệnh test
    print("\n5️⃣ Xóa lệnh test:")
    remove_order_from_monitor(test_order_id)
    
    # 6. Hiển thị lại sau khi xóa
    print("\n6️⃣ Danh sách sau khi xóa lệnh test:")
    show_active_orders()
    
    print("\n✅ Test hoàn thành!")

def test_email_notification():
    """Test chức năng gửi email thông báo"""
    print("\n" + "="*60)
    print("📧 KIỂM TRA CHỨC NĂNG EMAIL THÔNG báo")
    print("="*60)
    
    # Import hàm gửi email từ app.py
    try:
        from app import send_order_filled_notification
        
        # Tạo thông tin lệnh test
        test_order_info = {
            'order_id': 'TEST_12345',
            'symbol': 'ADA/JPY',
            'order_type': 'TAKE_PROFIT',
            'filled_quantity': 1000.0,
            'filled_price': 105.50,
            'total_received': 105500.0,
            'filled_time': '2025-01-28 10:30:00',
            'buy_price': 100.0,
            'profit_loss': '$5500.00',
            'profit_percentage': '+5.50%'
        }
        
        print("📧 Đang gửi email test...")
        send_order_filled_notification(test_order_info)
        print("✅ Email test đã được gửi!")
        
    except Exception as e:
        print(f"❌ Lỗi test email: {e}")

def show_monitoring_status():
    """Hiển thị trạng thái hệ thống monitoring"""
    print("\n" + "="*60)
    print("📊 TRẠNG THÁI HỆ THỐNG MONITORING")
    print("="*60)
    
    from app import MONITOR_RUNNING, ORDER_MONITOR_THREAD
    
    print(f"🔄 Monitor đang chạy: {'✅ CÓ' if MONITOR_RUNNING else '❌ KHÔNG'}")
    print(f"🧵 Thread hoạt động: {'✅ CÓ' if ORDER_MONITOR_THREAD and ORDER_MONITOR_THREAD.is_alive() else '❌ KHÔNG'}")
    print(f"📋 Số lệnh đang theo dõi: {len(ACTIVE_ORDERS)}")
    
    if ACTIVE_ORDERS:
        print("\n📝 Chi tiết lệnh:")
        for order_id, info in ACTIVE_ORDERS.items():
            print(f"   • {order_id}: {info['symbol']} ({info['order_type']})")

def interactive_menu():
    """Menu tương tác để test các chức năng"""
    while True:
        print("\n" + "="*60)
        print("🎛️  MENU KIỂM TRA HỆ THỐNG THEO DÕI LỆNH")
        print("="*60)
        print("1. Hiển thị danh sách lệnh đang theo dõi")
        print("2. Kiểm tra trạng thái tất cả lệnh")
        print("3. Thêm lệnh test vào danh sách")
        print("4. Xóa lệnh khỏi danh sách")
        print("5. Test gửi email thông báo")
        print("6. Hiển thị trạng thái hệ thống")
        print("7. Chạy test tự động")
        print("0. Thoát")
        print("-" * 60)
        
        choice = input("🎯 Chọn chức năng (0-7): ").strip()
        
        if choice == "1":
            show_active_orders()
        elif choice == "2":
            check_all_orders_now()
        elif choice == "3":
            symbol = input("Nhập symbol (VD: ADA/JPY): ").strip() or "ADA/JPY"
            order_id = input("Nhập order ID: ").strip() or f"test_{int(time.time())}"
            order_type = input("Nhập loại lệnh (VD: TAKE_PROFIT): ").strip() or "TAKE_PROFIT"
            buy_price = float(input("Nhập giá mua (VD: 100.5): ").strip() or "100.5")
            add_order_to_monitor(order_id, symbol, order_type, buy_price)
        elif choice == "4":
            order_id = input("Nhập order ID cần xóa: ").strip()
            if order_id:
                remove_order_from_monitor(order_id)
        elif choice == "5":
            test_email_notification()
        elif choice == "6":
            show_monitoring_status()
        elif choice == "7":
            test_order_monitoring()
        elif choice == "0":
            print("👋 Tạm biệt!")
            break
        else:
            print("❌ Lựa chọn không hợp lệ!")
        
        input("\n⏸️  Nhấn Enter để tiếp tục...")

if __name__ == "__main__":
    print("🚀 Khởi động test hệ thống theo dõi lệnh...")
    
    try:
        # Kiểm tra trạng thái ban đầu
        show_monitoring_status()
        
        # Chạy menu tương tác
        interactive_menu()
        
    except KeyboardInterrupt:
        print("\n🛑 Đã dừng bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
    finally:
        # Dừng monitoring thread khi thoát
        try:
            stop_order_monitor()
        except:
            pass
        print("✅ Test hoàn thành")
