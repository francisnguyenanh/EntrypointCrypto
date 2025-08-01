# 🧹 HƯỚNG DẪN BẢO TRÌ WORKSPACE

## Dọn dẹp tự động

### Chạy script cleanup
```bash
python3 cleanup.py
```

Script sẽ:
- ✅ Xóa `__pycache__/` và các file `.pyc`
- ✅ Xóa `.DS_Store` (macOS)
- ✅ Dọn dẹp log files lớn hơn 10MB
- ✅ Xóa backup files cũ hơn 30 ngày
- ✅ Xóa file tạm thời

### Dọn dẹp thủ công

#### Xóa cache Python:
```bash
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
```

#### Xóa file macOS:
```bash
find . -name ".DS_Store" -delete
```

#### Xóa file backup cũ:
```bash
find . -name "*.backup*" -mtime +30 -delete
```

## Files quan trọng (KHÔNG XÓA)

### Core files:
- `app.py` - Main trading application
- `trading_config.py` - Cấu hình trading
- `position_manager.py` - Quản lý vị thế
- `account_info.py` - Thông tin tài khoản
- `requirements.txt` - Dependencies

### Documentation:
- `FEATURES_SUMMARY.md` - Tóm tắt tính năng
- `POSITION_MANAGER_SUMMARY.md` - Hướng dẫn position manager
- `INVENTORY_HANDLING.md` - Xử lý tồn kho
- `MANUAL_INTERVENTION_GUIDE.md` - Hướng dẫn can thiệp thủ công

### Data files (được tạo tự động):
- `trading_log.txt` - Log giao dịch
- `position_data.json` - Dữ liệu vị thế
- `active_orders.json` - Lệnh đang hoạt động

## Thói quen bảo trì

### Hàng ngày:
- Chạy `python3 cleanup.py` trước khi bắt đầu trading

### Hàng tuần:
- Kiểm tra kích thước `trading_log.txt`
- Backup dữ liệu quan trọng

### Hàng tháng:
- Xóa backup files cũ thủ công
- Kiểm tra và cập nhật dependencies

## Git workflow

### Trước khi commit:
```bash
python3 cleanup.py
git add .
git status  # Kiểm tra chỉ commit files cần thiết
git commit -m "message"
```

### Files được gitignore:
- Cache files (`__pycache__/`, `*.pyc`)
- Log files (`*.log`, `trading_log.txt`)
- Data files (`*.json`)
- System files (`.DS_Store`)
- Backup files (`*.backup*`)
- Test files (`test_*.py`, `demo_*.py`)
