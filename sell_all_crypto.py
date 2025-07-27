#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script bán tất cả crypto trong tài khoản để reset về USDT
Sử dụng để mô phỏng việc trade từ ban đầu
"""

import ccxt
import trading_config
import time

def sell_all_crypto():
    """Bán tất cả crypto về USDT"""
    try:
        # Khởi tạo Binance API
        binance = ccxt.binance(trading_config.BINANCE_CONFIG)
        
        # Tắt cảnh báo
        binance.options["warnOnFetchOpenOrdersWithoutSymbol"] = False
        
        print("🔄 ĐANG BÁN TẤT CẢ CRYPTO VỀ USDT...")
        print("=" * 60)
        
        # Lấy balance hiện tại
        balance = binance.fetch_balance()
        
        # Danh sách tiền tệ fiat không bán
        fiat_currencies = ['USDT', 'JPY', 'USD', 'EUR', 'BTC', 'ETH']  # Giữ lại một số coin chính
        
        # Danh sách crypto cần bán
        crypto_to_sell = []
        total_value_estimate = 0
        
        print("📊 PHÂN TÍCH TÀI KHOẢN:")
        for symbol, amount in balance['total'].items():
            if amount > 0 and symbol not in ['USDT']:  # Chỉ giữ lại USDT
                crypto_to_sell.append({
                    'symbol': symbol,
                    'amount': amount
                })
                print(f"   • {symbol}: {amount:.6f}")
        
        if not crypto_to_sell:
            print("✅ Không có crypto nào để bán. Tài khoản đã sạch.")
            return
        
        print(f"\n🎯 SẼ BÁN {len(crypto_to_sell)} LOẠI CRYPTO")
        print("-" * 40)
        
        successful_sales = 0
        failed_sales = 0
        
        for crypto in crypto_to_sell:
            symbol = crypto['symbol']
            amount = crypto['amount']
            
            try:
                # Thử bán về USDT trước
                trading_pair = f"{symbol}/USDT"
                
                # Kiểm tra xem pair có tồn tại không
                markets = binance.load_markets()
                if trading_pair not in markets:
                    print(f"⚠️ {trading_pair} không tồn tại, thử JPY...")
                    trading_pair = f"{symbol}/JPY"
                    if trading_pair not in markets:
                        print(f"❌ Không tìm thấy pair cho {symbol}")
                        failed_sales += 1
                        continue
                
                # Lấy thông tin market
                market = markets[trading_pair]
                min_amount = market['limits']['amount']['min']
                
                # Kiểm tra số lượng tối thiểu
                if amount < min_amount:
                    print(f"⚠️ {symbol}: Số lượng {amount:.6f} < minimum {min_amount:.6f}")
                    failed_sales += 1
                    continue
                
                # Lấy giá hiện tại
                ticker = binance.fetch_ticker(trading_pair)
                current_price = ticker['last']
                estimated_value = amount * current_price
                
                print(f"🔄 Đang bán {symbol}:")
                print(f"   • Số lượng: {amount:.6f}")
                print(f"   • Pair: {trading_pair}")
                print(f"   • Giá hiện tại: {current_price:.4f}")
                print(f"   • Giá trị ước tính: {estimated_value:.2f}")
                
                # Đặt lệnh bán market
                order = binance.create_market_sell_order(trading_pair, amount)
                
                print(f"✅ Đã bán {symbol} thành công!")
                print(f"   • Order ID: {order['id']}")
                print(f"   • Giá thực tế: {order.get('average', 'N/A')}")
                print(f"   • Số lượng bán: {order.get('filled', amount)}")
                
                successful_sales += 1
                total_value_estimate += estimated_value
                
                # Nghỉ một chút giữa các lệnh
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Lỗi bán {symbol}: {e}")
                failed_sales += 1
                continue
        
        print("\n" + "=" * 60)
        print("📊 KẾT QUẢ BÁN CRYPTO:")
        print(f"✅ Thành công: {successful_sales} coins")
        print(f"❌ Thất bại: {failed_sales} coins")
        print(f"💰 Tổng giá trị ước tính đã bán: {total_value_estimate:.2f}")
        
        # Kiểm tra balance sau khi bán
        print("\n🔍 KIỂM TRA BALANCE SAU KHI BÁN:")
        new_balance = binance.fetch_balance()
        usdt_balance = new_balance['USDT']['free'] if 'USDT' in new_balance else 0
        jpy_balance = new_balance['JPY']['free'] if 'JPY' in new_balance else 0
        
        print(f"💰 USDT khả dụng: {usdt_balance:,.2f}")
        print(f"💰 JPY khả dụng: {jpy_balance:,.2f}")
        
        # Kiểm tra crypto còn lại
        remaining_crypto = []
        for symbol, amount in new_balance['total'].items():
            if amount > 0.001 and symbol not in ['USDT', 'JPY']:  # Threshold để bỏ qua dust
                remaining_crypto.append(f"{symbol}: {amount:.6f}")
        
        if remaining_crypto:
            print(f"\n⚠️ CRYPTO CÒN LẠI:")
            for crypto in remaining_crypto:
                print(f"   • {crypto}")
        else:
            print(f"\n✅ TÀI KHOẢN ĐÃ SẠCH - CHỈ CÒN FIAT")
        
        print("\n🎉 HOÀN THÀNH RESET TÀI KHOẢN!")
        print("Bây giờ bạn có thể bắt đầu trade từ đầu với số dư USDT/JPY.")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình bán crypto: {e}")

def confirm_sell_all():
    """Xác nhận trước khi bán tất cả"""
    print("⚠️ CẢNH BÁO: BÁN TẤT CẢ CRYPTO")
    print("=" * 50)
    print("Script này sẽ bán TẤT CẢ crypto trong tài khoản về USDT/JPY")
    print("Điều này KHÔNG THỂ HOÀN TÁC!")
    print()
    print("Chỉ sử dụng trong môi trường TESTNET để test!")
    print()
    
    confirm = input("Bạn có chắc chắn muốn tiếp tục? (gõ 'YES' để xác nhận): ")
    
    if confirm.upper() == 'YES':
        print("\n✅ Đã xác nhận. Bắt đầu bán...")
        return True
    else:
        print("\n❌ Đã hủy. Không bán crypto nào.")
        return False

if __name__ == "__main__":
    print("🚀 SCRIPT RESET TÀI KHOẢN - BÁN TẤT CẢ CRYPTO")
    print()
    
    # Xác nhận trước khi thực hiện
    if confirm_sell_all():
        sell_all_crypto()
    else:
        print("Thoát script.")
