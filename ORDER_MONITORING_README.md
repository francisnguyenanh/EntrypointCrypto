# 🎯 Hệ Thống Theo Dõi Lệnh Bán Tự Động

## 📋 Tổng Quan

Hệ thống này được thêm vào bot trading để tự động theo dõi các lệnh bán (Stop Loss, Take Profit) và gửi thông báo email khi lệnh được khớp.

## 🚀 Tính Năng Chính

### 1. Theo Dõi Lệnh Tự Động
- ✅ Theo dõi tất cả lệnh bán (SL/TP) đã đặt
- ✅ Kiểm tra trạng thái lệnh mỗi 30 giây
- ✅ Phát hiện khi lệnh được khớp hoàn toàn hoặc một phần
- ✅ Lưu trữ danh sách lệnh vào file `active_orders.json`

### 2. Thông Báo Email Tự Động
- ✅ Gửi email khi lệnh bán được khớp
- ✅ Thông tin chi tiết về lệnh (giá, số lượng, lợi nhuận)
- ✅ Tính toán % lợi nhuận/lỗ so với giá mua

### 3. Quản Lý Lệnh
- ✅ Thêm/xóa lệnh khỏi danh sách theo dõi
- ✅ Xem trạng thái tất cả lệnh đang theo dõi
- ✅ Backup/restore danh sách lệnh

## 🔧 Cách Hoạt Động

### Khi Đặt Lệnh
```python
# Bot tự động thêm lệnh vào danh sách theo dõi
add_order_to_monitor(
    order_id="12345",
    symbol="ADA/JPY", 
    order_type="TAKE_PROFIT",
    buy_price=100.50
)
```

### Khi Lệnh Được Khớp
1. 🔍 System phát hiện lệnh đã khớp
2. 📊 Tính toán lợi nhuận/lỗ
3. 📧 Gửi email thông báo chi tiết
4. 🗑️ Xóa lệnh khỏi danh sách theo dõi

### Email Thông Báo Mẫu
```
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
```

## 🛠️ Cài Đặt & Sử Dụng

### 1. Cấu Hình Email
Đảm bảo email notification đã được cấu hình trong `trading_config.py`:

```python
NOTIFICATION_CONFIG = {
    'enabled': True,
    'email_enabled': True,
    'telegram_enabled': False,
    # ... các cấu hình email khác
}
```

### 2. Khởi Động Hệ Thống
```python
# Hệ thống tự khởi động khi import app.py
from app import *

# Hoặc khởi động thủ công
initialize_order_monitoring()
```

### 3. Kiểm Tra Trạng Thái
```python
# Xem danh sách lệnh đang theo dõi
show_active_orders()

# Kiểm tra trạng thái tất cả lệnh ngay
check_all_orders_now()

# Thêm lệnh thủ công (nếu cần)
add_order_to_monitor("order_id", "ADA/JPY", "STOP_LOSS", 100.0)

# Xóa lệnh khỏi theo dõi
remove_order_from_monitor("order_id")
```

## 🧪 Test Hệ Thống

Chạy script test để kiểm tra:

```bash
python test_order_monitoring.py
```

Script test cung cấp menu tương tác để:
- ✅ Test thêm/xóa lệnh
- ✅ Test gửi email thông báo
- ✅ Kiểm tra trạng thái hệ thống
- ✅ Xem danh sách lệnh đang theo dõi

## 📁 Files Quan Trọng

### `app.py`
- Chứa tất cả logic theo dõi lệnh
- Functions: `monitor_active_orders()`, `send_order_filled_notification()`, etc.

### `active_orders.json`
- File backup danh sách lệnh đang theo dõi
- Tự động tạo và cập nhật
- Format JSON với thông tin chi tiết mỗi lệnh

### `test_order_monitoring.py`
- Script test các chức năng
- Menu tương tác để debug

## 🔄 Quy Trình Hoạt Động

```
1. Bot đặt lệnh mua → Thành công
   ↓
2. Bot đặt lệnh SL/TP → add_order_to_monitor()
   ↓
3. Background thread kiểm tra mỗi 30s
   ↓
4. Phát hiện lệnh khớp → Gửi email
   ↓
5. Xóa lệnh khỏi danh sách theo dõi
```

## ⚠️ Lưu Ý Quan Trọng

### Thread Safety
- ✅ Sử dụng background thread để không block main process
- ✅ Thread tự động dừng khi program exit

### Error Handling
- ✅ Retry logic khi API call thất bại
- ✅ Fallback khi không thể gửi email
- ✅ Log lỗi chi tiết

### Performance
- ✅ Kiểm tra mỗi 30s (có thể điều chỉnh)
- ✅ Batch check nhiều lệnh cùng lúc
- ✅ Tự động cleanup lệnh đã hoàn thành

### Backup & Recovery
- ✅ Tự động lưu danh sách lệnh vào file
- ✅ Restore khi restart bot
- ✅ Manual backup/restore nếu cần

## 🎯 Ví Dụ Sử Dụng

```python
# Import và sử dụng
from app import *

# Bot tự động thêm lệnh khi trading
# Không cần can thiệp thủ công

# Chỉ cần kiểm tra khi muốn
show_active_orders()

# Email sẽ tự động được gửi khi lệnh khớp
```

## 📞 Support

Nếu có vấn đề:
1. 🔍 Kiểm tra log trong console
2. 📧 Kiểm tra cấu hình email 
3. 🧪 Chạy test script
4. 📁 Kiểm tra file `active_orders.json`
