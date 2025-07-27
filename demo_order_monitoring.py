#!/usr/bin/env python3
"""
🎯 DEMO: Hệ Thống Theo Dõi Lệnh Bán Tự Động

Cách sử dụng hệ thống theo dõi lệnh đã được thêm vào bot trading
"""

print("🎯 HỆ THỐNG THEO DÕI LỆNH BÁN TỰ ĐỘNG")
print("=" * 60)

print("""
📋 TÍNH NĂNG ĐÃ THÊM:

1. 🔄 Theo dõi lệnh tự động (mỗi 30 giây)
   • Kiểm tra trạng thái Stop Loss
   • Kiểm tra trạng thái Take Profit  
   • Phát hiện khi lệnh được khớp

2. 📧 Thông báo email tự động
   • Gửi email khi lệnh bán được khớp
   • Thông tin chi tiết (giá, số lượng, lợi nhuận)
   • Tính % lợi nhuận so với giá mua

3. 💾 Lưu trữ & Backup
   • Lưu danh sách lệnh vào file JSON
   • Tự động restore khi restart bot
   • Thread-safe operations

🔧 CÁC HÀM MỚI ĐÃ THÊM:

📊 Quản lý lệnh:
   • show_active_orders()          - Xem danh sách lệnh đang theo dõi
   • add_order_to_monitor()        - Thêm lệnh vào danh sách  
   • remove_order_from_monitor()   - Xóa lệnh khỏi danh sách
   • check_all_orders_now()        - Kiểm tra trạng thái ngay

📧 Thông báo:
   • send_order_filled_notification() - Gửi email khi lệnh khớp
   • send_trading_notification()      - Gửi thông báo trading

🔄 Monitoring:
   • monitor_active_orders()       - Thread theo dõi liên tục
   • initialize_order_monitoring() - Khởi tạo hệ thống
   • stop_order_monitor()          - Dừng hệ thống

💽 Backup:
   • save_active_orders_to_file()  - Lưu vào file JSON
   • load_active_orders_from_file() - Đọc từ file JSON

🚀 CÁCH SỬ DỤNG:

1. Khi đặt lệnh mua, bot sẽ tự động:
   ✅ Đặt lệnh Stop Loss/Take Profit
   ✅ Thêm vào danh sách theo dõi 
   ✅ Bắt đầu monitor trong background

2. Khi lệnh bán được khớp:
   ✅ System tự phát hiện
   ✅ Tính toán lợi nhuận/lỗ  
   ✅ Gửi email thông báo chi tiết
   ✅ Xóa khỏi danh sách theo dõi

3. File backup 'active_orders.json':
   ✅ Tự động lưu danh sách lệnh
   ✅ Restore khi restart bot
   ✅ Có thể edit thủ công nếu cần

📧 MẪU EMAIL THÔNG BÁO:

Subject: 🎯 LỆNH BÁN ĐÃ KHỚP - ADA/JPY

🎯 THÔNG BÁO LỆNH BÁN ĐÃ KHỚP

📊 Thông tin lệnh:
• Symbol: ADA/JPY  
• Loại lệnh: TAKE_PROFIT
• Order ID: 12345
• Số lượng: 1000.000000
• Giá khớp: $105.50
• Tổng tiền nhận: $105500.00
• Thời gian khớp: 2025-01-28 10:30:00

💰 Thống kê:
• Giá mua ban đầu: $100.00
• Lợi nhuận/Lỗ: $5500.00  
• % Thay đổi: +5.50%

🔔 Lệnh đã được thực hiện thành công!

🧪 CÁCH TEST:

1. Chạy test script:
   python3 test_order_monitoring.py

2. Hoặc import và test thủ công:
   from app import show_active_orders
   show_active_orders()

📁 FILES MỚI:

• app.py                    - Đã update với order monitoring
• test_order_monitoring.py  - Script test tương tác
• ORDER_MONITORING_README.md - Hướng dẫn chi tiết
• active_orders.json        - File backup (tự tạo)

⚠️  QUAN TRỌNG:

• Đảm bảo email đã được cấu hình trong trading_config.py
• Hệ thống tự khởi động khi import app.py  
• Thread monitoring chạy background, không block main process
• File backup tự động update mỗi khi có thay đổi

✅ HỆ THỐNG ĐÃ SẴন SÀNG SỬ DỤNG!
""")

print("\n" + "=" * 60)
print("📖 Đọc ORDER_MONITORING_README.md để biết thêm chi tiết")
print("🧪 Chạy test_order_monitoring.py để test hệ thống")
print("=" * 60)
