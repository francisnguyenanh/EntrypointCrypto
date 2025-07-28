#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST EMAIL NOTIFICATIONS
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from account_info import (
    test_email_notification, 
    send_buy_success_notification,
    send_sell_order_placed_notification,
    send_sell_success_notification
)
from datetime import datetime

def test_all_email_functions():
    """Test tất cả email notification functions"""
    
    print("🧪 TESTING ALL EMAIL NOTIFICATIONS")
    print("=" * 60)
    
    # 1. Test kết nối
    print("1️⃣ Testing email connection...")
    connection_result = test_email_notification()
    if not connection_result:
        print("❌ Email connection failed - Dừng test")
        return
    
    print("\n" + "=" * 60)
    
    # 2. Test buy success email
    print("2️⃣ Testing buy success email...")
    try:
        buy_data = {
            'symbol': 'ADA/JPY',
            'quantity': 100.000000,
            'price': 5000.0000,
            'total': 500000.00,
            'order_id': 'TEST_BUY_12345',
            'balance_before': 1000000.00,
            'balance_after': 500000.00,
            'stop_loss': 4750.0000,
            'tp1': 5250.0000,
            'tp2': 5500.0000,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        send_buy_success_notification(buy_data)
        print("✅ Buy success email sent!")
        
    except Exception as e:
        print(f"❌ Buy email error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    
    # 3. Test sell order placed email
    print("3️⃣ Testing sell order placed email...")
    try:
        sell_order_data = {
            'symbol': 'ADA/JPY',
            'original_quantity': 100.000000,
            'buy_price': 5000.0000,
            'stop_loss': 4750.0000,
            'sl_order_id': 'TEST_SL_67890',
            'tp1_order_id': 'TEST_TP1_11111',
            'tp1_price': 5250.0000,
            'tp1_quantity': 70.000000,
            'tp2_order_id': 'TEST_TP2_22222',
            'tp2_price': 5500.0000,
            'tp2_quantity': 30.000000,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        send_sell_order_placed_notification(sell_order_data)
        print("✅ Sell order placed email sent!")
        
    except Exception as e:
        print(f"❌ Sell order email error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    
    # 4. Test sell success email
    print("4️⃣ Testing sell success email...")
    try:
        sell_success_data = {
            'symbol': 'ADA/JPY',
            'order_type': 'TAKE_PROFIT',
            'filled_price': 5250.0000,
            'buy_price': 5000.0000,
            'quantity': 70.000000,
            'profit_loss': 17500.00,
            'profit_percent': 5.00,
            'order_id': 'TEST_TP1_11111',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        send_sell_success_notification(sell_success_data)
        print("✅ Sell success email sent!")
        
    except Exception as e:
        print(f"❌ Sell success email error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎉 EMAIL TESTING COMPLETED!")
    print("📧 Kiểm tra hộp thư của bạn để xem emails")

if __name__ == "__main__":
    test_all_email_functions()
