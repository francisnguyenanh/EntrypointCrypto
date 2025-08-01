#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 SCRIPT RESET TÀI KHOẢN - BÁN TẤT CẢ CRYPTO
==========================================

Script này sẽ:
1. Hủy tất cả lệnh đang mở
2. Bán tất cả crypto holdings về JPY
3. Hiển thị số dư cuối cùng
4. Gửi email thông báo kết quả

⚠️ CẢNH BÁO: Script này sẽ bán TẤT CẢ crypto trong tài khoản!
Chỉ chạy khi bạn chắc chắn muốn reset hoàn toàn.
"""

import ccxt
import time
import json
import sys
import os
from datetime import datetime
import traceback

# Import config và notification
try:
    import trading_config
    from account_info import send_trading_notification, get_account_info
except ImportError as e:
    print(f"❌ Lỗi import: {e}")
    print("💡 Đảm bảo file trading_config.py và account_info.py tồn tại")
    sys.exit(1)

# Khởi tạo Binance API
try:
    binance = ccxt.binance(trading_config.BINANCE_CONFIG)
    print("✅ Kết nối Binance API thành công")
except Exception as e:
    print(f"❌ Lỗi kết nối Binance API: {e}")
    sys.exit(1)

def send_notification(message, urgent=False):
    """Gửi thông báo với fallback"""
    try:
        print(f"📱 {message}")
        send_trading_notification(message, urgent)
    except Exception as e:
        print(f"⚠️ Lỗi gửi email: {e}")

def get_all_balances():
    """Lấy tất cả số dư trong tài khoản"""
    try:
        balance = binance.fetch_balance()
        # Lọc ra các coin có số dư > 0, chỉ lấy các key là dict và có trường 'free'
        non_zero_balances = {}
        for currency, amounts in balance.items():
            if (
                isinstance(amounts, dict)
                and 'free' in amounts
                and currency not in ['info', 'free', 'used', 'total']
            ):
                free_amount = amounts['free']
                if free_amount > 0:
                    non_zero_balances[currency] = {
                        'free': free_amount,
                        'used': amounts.get('used', 0),
                        'total': amounts.get('total', 0)
                    }
        return non_zero_balances
    except Exception as e:
        print(f"❌ Lỗi lấy số dư: {e}")
        return {}

def cancel_all_orders():
    """Hủy tất cả lệnh đang mở"""
    try:
        print("\n🔄 Đang hủy tất cả lệnh đang mở...")
        
        # Tắt cảnh báo
        binance.options["warnOnFetchOpenOrdersWithoutSymbol"] = False
        
        open_orders = binance.fetch_open_orders()
        
        if not open_orders:
            print("✅ Không có lệnh nào đang mở")
            return 0
        
        cancelled_count = 0
        for order in open_orders:
            try:
                binance.cancel_order(order['id'], order['symbol'])
                print(f"✅ Hủy lệnh {order['id']} - {order['symbol']}")
                cancelled_count += 1
            except Exception as e:
                print(f"⚠️ Không thể hủy lệnh {order['id']}: {e}")
        
        print(f"📊 Đã hủy {cancelled_count}/{len(open_orders)} lệnh")
        return cancelled_count
        
    except Exception as e:
        print(f"❌ Lỗi hủy lệnh: {e}")
        return 0

def get_jpy_pair_for_currency(currency):
    """Tìm cặp JPY cho currency"""
    possible_pairs = [
        f"{currency}/JPY",
        f"{currency}JPY"
    ]
    
    try:
        markets = binance.load_markets()
        for pair in possible_pairs:
            if pair in markets:
                return pair
    except Exception as e:
        print(f"⚠️ Lỗi load markets: {e}")
    
    return None

def sell_currency_to_jpy(currency, amount):
    """Bán một currency cụ thể về JPY"""
    try:
        # Tìm cặp JPY
        jpy_pair = get_jpy_pair_for_currency(currency)
        
        if not jpy_pair:
            print(f"⚠️ Không tìm thấy cặp JPY cho {currency}")
            return False
        
        print(f"📊 Đang bán {amount:.6f} {currency} qua cặp {jpy_pair}...")
        
        # Kiểm tra market info để đảm bảo quantity hợp lệ
        try:
            market = binance.market(jpy_pair)
            min_amount = market['limits']['amount']['min']
            
            if amount < min_amount:
                print(f"⚠️ Số lượng {amount:.6f} nhỏ hơn minimum {min_amount} - Bỏ qua")
                return False
                
        except Exception as market_error:
            print(f"⚠️ Không thể kiểm tra market info: {market_error}")
        
        # Đặt lệnh bán market
        sell_order = binance.create_market_sell_order(jpy_pair, amount)
        
        # Lấy thông tin thực tế
        filled_amount = float(sell_order['filled'])
        avg_price = float(sell_order['average']) if sell_order['average'] else 0
        total_jpy = filled_amount * avg_price
        
        print(f"✅ Bán thành công {filled_amount:.6f} {currency} @ ¥{avg_price:.4f}")
        print(f"💰 Nhận được: ¥{total_jpy:,.2f}")
        
        return {
            'success': True,
            'currency': currency,
            'amount_sold': filled_amount,
            'price': avg_price,
            'jpy_received': total_jpy,
            'order_id': sell_order['id']
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Xử lý các loại lỗi phổ biến
        if 'insufficient' in error_msg or 'balance' in error_msg:
            print(f"⚠️ Số dư {currency} không đủ để bán")
        elif 'min notional' in error_msg:
            print(f"⚠️ Giá trị lệnh bán {currency} quá nhỏ")
        elif 'invalid symbol' in error_msg:
            print(f"⚠️ Cặp {jpy_pair} không hợp lệ")
        else:
            print(f"❌ Lỗi bán {currency}: {e}")
        
        return False

def sell_all_crypto():
    """Bán tất cả crypto về JPY"""
    print("\n" + "=" * 60)
    print("🔥 BẮT ĐẦU BÁN TẤT CẢ CRYPTO")
    print("=" * 60)
    
    # 1. Lấy số dư ban đầu
    print("📊 Đang lấy thông tin số dư hiện tại...")
    initial_balances = get_all_balances()
    
    if not initial_balances:
        print("❌ Không thể lấy thông tin số dư")
        return
    
    print(f"💰 Tìm thấy {len(initial_balances)} loại coin có số dư:")
    initial_jpy = initial_balances.get('JPY', {}).get('free', 0)
    
    for currency, balance_info in initial_balances.items():
        free_amount = balance_info['free']
        print(f"   {currency}: {free_amount:,.6f}")
    
    print(f"\n💴 Số dư JPY ban đầu: ¥{initial_jpy:,.2f}")
    
    # 2. Hủy tất cả lệnh
    cancelled_orders = cancel_all_orders()
    
    # 3. Bán tất cả crypto (trừ JPY)
    print(f"\n🔄 Bắt đầu bán tất cả crypto...")
    
    sell_results = []
    total_jpy_received = 0
    
    for currency, balance_info in initial_balances.items():
        if currency == 'JPY':
            continue  # Bỏ qua JPY
        
        free_amount = balance_info['free']
        
        if free_amount <= 0:
            continue
        
        print(f"\n--- Xử lý {currency} ---")
        result = sell_currency_to_jpy(currency, free_amount)
        
        if result and result != False:
            sell_results.append(result)
            total_jpy_received += result['jpy_received']
            time.sleep(1)  # Delay để tránh rate limit
        
    
    # 4. Kiểm tra số dư cuối cùng
    print(f"\n🔄 Đang kiểm tra số dư cuối cùng...")
    time.sleep(2)  # Chờ để balances cập nhật
    
    final_balances = get_all_balances()
    final_jpy = final_balances.get('JPY', {}).get('free', 0)
    
    # 5. Tổng kết kết quả
    print(f"\n" + "=" * 60)
    print("📊 KẾT QUẢ RESET TÀI KHOẢN")
    print("=" * 60)
    
    success_count = len(sell_results)
    total_attempted = len([c for c in initial_balances.keys() if c != 'JPY'])
    
    print(f"🎯 Lệnh hủy: {cancelled_orders} lệnh")
    print(f"🎯 Bán thành công: {success_count}/{total_attempted} loại coin")
    print(f"💴 JPY ban đầu: ¥{initial_jpy:,.2f}")
    print(f"💰 JPY từ bán crypto: ¥{total_jpy_received:,.2f}")
    print(f"💵 Tổng JPY cuối: ¥{final_jpy:,.2f}")
    
    # Chi tiết từng lệnh bán
    if sell_results:
        print(f"\n📋 CHI TIẾT CÁC LỆNH BÁN:")
        for result in sell_results:
            print(f"   {result['currency']}: {result['amount_sold']:.6f} @ ¥{result['price']:.4f} = ¥{result['jpy_received']:,.2f}")
    
    # Kiểm tra còn crypto nào không
    remaining_crypto = []
    for currency, balance_info in final_balances.items():
        if currency != 'JPY' and balance_info['free'] > 0:
            remaining_crypto.append(f"{currency}: {balance_info['free']:.6f}")
    
    if remaining_crypto:
        print(f"\n⚠️ CRYPTO CHƯA BÁN ĐƯỢC:")
        for crypto in remaining_crypto:
            print(f"   {crypto}")
    else:
        print(f"\n✅ TẤT CẢ CRYPTO ĐÃ ĐƯỢC BÁN")
    
    # 6. Gửi email thông báo
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        email_message = f"""
🔥 RESET TÀI KHOẢN HOÀN TẤT

⏰ Thời gian: {timestamp}
🎯 Lệnh hủy: {cancelled_orders}
🎯 Bán thành công: {success_count}/{total_attempted}

💰 KẾT QUẢ TÀI CHÍNH:
• JPY ban đầu: ¥{initial_jpy:,.2f}
• JPY từ bán: ¥{total_jpy_received:,.2f}
• Tổng JPY cuối: ¥{final_jpy:,.2f}
• Tăng: ¥{final_jpy - initial_jpy:,.2f}

{"✅ TẤT CẢ CRYPTO ĐÃ ĐƯỢC BÁN" if not remaining_crypto else f"⚠️ Còn lại: {len(remaining_crypto)} loại"}
        """
        
        send_notification(email_message, urgent=True)
        
    except Exception as e:
        print(f"⚠️ Lỗi gửi email: {e}")
    
    # 7. Lưu log chi tiết
    try:
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'cancelled_orders': cancelled_orders,
            'initial_balances': initial_balances,
            'final_balances': final_balances,
            'sell_results': sell_results,
            'summary': {
                'initial_jpy': initial_jpy,
                'jpy_from_sales': total_jpy_received,
                'final_jpy': final_jpy,
                'profit': final_jpy - initial_jpy,
                'successful_sales': success_count,
                'total_attempted': total_attempted
            }
        }
        
        with open('reset_account_log.json', 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Đã lưu log chi tiết vào reset_account_log.json")
        
    except Exception as e:
        print(f"⚠️ Lỗi lưu log: {e}")
    
    print(f"\n🎉 RESET TÀI KHOẢN HOÀN TẤT!")
    return {
        'success': True,
        'final_jpy': final_jpy,
        'profit': final_jpy - initial_jpy,
        'successful_sales': success_count
    }

def main():
    """Hàm main với xác nhận từ user"""
    print("🔥 SCRIPT RESET TÀI KHOẢN - BÁN TẤT CẢ CRYPTO")
    print("=" * 50)
    
    # Hiển thị thông tin tài khoản hiện tại
    try:
        print("📊 Thông tin tài khoản hiện tại:")
        account_info = get_account_info()
        if account_info:
            print("✅ Kết nối tài khoản thành công")
        else:
            print("⚠️ Không thể lấy thông tin tài khoản")
    except Exception as e:
        print(f"⚠️ Lỗi kiểm tra tài khoản: {e}")
    
    # Hiển thị số dư hiện tại
    current_balances = get_all_balances()
    if current_balances:
        print(f"\n� Số dư hiện tại:")
        for currency, balance_info in current_balances.items():
            free_amount = balance_info['free']
            if free_amount > 0:
                print(f"   {currency}: {free_amount:,.6f}")
    
    # Xác nhận từ user
    print(f"\n⚠️ CẢNH BÁO: Script này sẽ:")
    print(f"   1. Hủy TẤT CẢ lệnh đang mở")
    print(f"   2. Bán TẤT CẢ crypto về JPY")
    print(f"   3. Không thể hoàn tác!")
    
    confirm = input(f"\n❓ Bạn có chắc chắn muốn tiếp tục? (Gõ 'YES' để xác nhận): ")
    
    if confirm.strip().upper() != 'YES':
        print("🛑 Đã hủy bỏ reset tài khoản")
        return
    
    # Xác nhận lần 2
    confirm2 = input(f"❓ Xác nhận lần cuối - Gõ 'RESET' để bắt đầu: ")
    
    if confirm2.strip().upper() != 'RESET':
        print("🛑 Đã hủy bỏ reset tài khoản")
        return
    
    print(f"\n🚀 Bắt đầu reset tài khoản...")
    
    try:
        result = sell_all_crypto()
        
        if result and result['success']:
            print(f"\n🎉 RESET THÀNH CÔNG!")
            print(f"💵 Số dư cuối: ¥{result['final_jpy']:,.2f}")
            if result['profit'] > 0:
                print(f"📈 Lãi: ¥{result['profit']:,.2f}")
            elif result['profit'] < 0:
                print(f"📉 Lỗ: ¥{abs(result['profit']):,.2f}")
        else:
            print(f"⚠️ Reset hoàn tất nhưng có một số vấn đề")
            
    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng: {e}")
        traceback.print_exc()
        
        # Gửi email cảnh báo lỗi
        try:
            send_notification(f"� LỖI RESET TÀI KHOẢN: {e}", urgent=True)
        except:
            pass

if __name__ == "__main__":
    main()
