#!/usr/bin/env python3
"""
Manual Stop Loss Checker
========================

Script để kiểm tra manual stop loss triggers mà không cần chạy full bot.
Sử dụng khi bot không chạy liên tục nhưng vẫn muốn monitor SL.

Usage:
    python3 check_sl.py
"""

import sys
import os

# Thêm thư mục hiện tại vào Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import check_manual_stop_loss_triggers, load_active_orders_from_file
    
    def main():
        print("🛡️ CHECKING MANUAL STOP LOSS TRIGGERS")
        print("=" * 50)
        
        # Load active orders
        load_active_orders_from_file()
        
        # Check SL triggers
        check_manual_stop_loss_triggers()
        
        print("✅ SL check completed")
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Đảm bảo app.py có thể import được")
except Exception as e:
    print(f"❌ Error: {e}")
