#!/usr/bin/env python3
"""
Script dọn dẹp workspace tự động
Chạy script này để xóa các file cache, log cũ và file tạm thời
"""

import os
import glob
import shutil
from datetime import datetime, timedelta

def cleanup_workspace():
    """Dọn dẹp workspace"""
    print("🧹 Bắt đầu dọn dẹp workspace...")
    
    # 1. Xóa __pycache__
    if os.path.exists('__pycache__'):
        shutil.rmtree('__pycache__')
        print("✅ Đã xóa __pycache__/")
    
    # 2. Xóa .DS_Store
    for ds_store in glob.glob('**/.DS_Store', recursive=True):
        os.remove(ds_store)
        print(f"✅ Đã xóa {ds_store}")
    
    # 3. Xóa .pyc files
    pyc_files = glob.glob('**/*.pyc', recursive=True)
    for pyc_file in pyc_files:
        os.remove(pyc_file)
        print(f"✅ Đã xóa {pyc_file}")
    
    # 4. Dọn dẹp log cũ (giữ lại 7 ngày gần nhất)
    log_files = glob.glob('*.log') + ['trading_log.txt']
    for log_file in log_files:
        if os.path.exists(log_file):
            # Kiểm tra kích thước file
            file_size_mb = os.path.getsize(log_file) / (1024 * 1024)
            if file_size_mb > 10:  # Nếu > 10MB
                # Backup và giữ lại 1000 dòng cuối
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) > 1000:
                    # Backup file cũ
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_file = f"{log_file}.backup_{timestamp}"
                    os.rename(log_file, backup_file)
                    
                    # Tạo file mới với 1000 dòng cuối
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.writelines(lines[-1000:])
                    
                    print(f"✅ Đã dọn dẹp {log_file} - backup: {backup_file}")
    
    # 5. Xóa backup files cũ hơn 30 ngày
    cutoff_date = datetime.now() - timedelta(days=30)
    backup_files = glob.glob('*.backup_*')
    for backup_file in backup_files:
        try:
            file_time = datetime.fromtimestamp(os.path.getmtime(backup_file))
            if file_time < cutoff_date:
                os.remove(backup_file)
                print(f"✅ Đã xóa backup cũ {backup_file}")
        except Exception as e:
            print(f"⚠️ Lỗi xóa {backup_file}: {e}")
    
    # 6. Xóa file tạm thời
    temp_files = glob.glob('*.tmp') + glob.glob('*.temp') + glob.glob('*~')
    for temp_file in temp_files:
        os.remove(temp_file)
        print(f"✅ Đã xóa {temp_file}")
    
    print("🎉 Dọn dẹp workspace hoàn tất!")
    
    # Hiển thị thống kê
    total_files = len(glob.glob('*'))
    print(f"📊 Workspace hiện có {total_files} files")

if __name__ == "__main__":
    cleanup_workspace()
