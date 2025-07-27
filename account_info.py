#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Account Info và Notification Functions
"""

import ccxt
import trading_config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_account_info():
    """Lấy thông tin tài khoản chi tiết"""
    try:
        binance = ccxt.binance(trading_config.BINANCE_CONFIG)
        
        print("=" * 80)
        print("💼 THÔNG TIN TÀI KHOẢN BINANCE")
        print("=" * 80)
        
        # Lấy balance
        balance = binance.fetch_balance()
        
        # Hiển thị số dư tiền tệ
        print("💰 SỐ DƯ TIỀN TỆ:")
        fiat_currencies = ['USDT', 'JPY', 'USD', 'EUR']
        total_fiat_value = 0
        
        for currency in fiat_currencies:
            free_balance = balance['free'].get(currency, 0)
            used_balance = balance['used'].get(currency, 0)
            total_balance = balance['total'].get(currency, 0)
            
            if total_balance > 0:
                print(f"   {currency}:")
                print(f"     • Khả dụng: {free_balance:,.2f}")
                print(f"     • Đang sử dụng: {used_balance:,.2f}")
                print(f"     • Tổng cộng: {total_balance:,.2f}")
                
                if currency == 'USDT':
                    total_fiat_value += total_balance
                elif currency == 'JPY':
                    total_fiat_value += total_balance / 150  # Convert to USD
        
        print(f"\n💵 TỔNG GIÁ TRỊ FIAT: ${total_fiat_value:,.2f}")
        
        # Hiển thị số dư crypto
        print("\n🪙 SỐ DƯ CRYPTOCURRENCY:")
        crypto_positions = []
        total_crypto_value = 0
        
        for symbol, amounts in balance['total'].items():
            if amounts > 0 and symbol not in fiat_currencies:
                try:
                    # Lấy giá hiện tại
                    ticker = binance.fetch_ticker(f"{symbol}/USDT")
                    current_price = ticker['last']
                    value_usd = amounts * current_price
                    
                    crypto_positions.append({
                        'symbol': symbol,
                        'amount': amounts,
                        'price': current_price,
                        'value': value_usd
                    })
                    total_crypto_value += value_usd
                    
                except:
                    # Nếu không lấy được giá USDT, thử JPY
                    try:
                        ticker = binance.fetch_ticker(f"{symbol}/JPY")
                        current_price = ticker['last']
                        value_usd = amounts * current_price / 150  # Convert JPY to USD
                        
                        crypto_positions.append({
                            'symbol': symbol,
                            'amount': amounts,
                            'price': current_price,
                            'value': value_usd,
                            'currency': 'JPY'
                        })
                        total_crypto_value += value_usd
                    except:
                        print(f"   {symbol}: {amounts:.6f} (Không lấy được giá)")
        
        # Sắp xếp theo giá trị
        crypto_positions.sort(key=lambda x: x['value'], reverse=True)
        
        for pos in crypto_positions:
            currency = pos.get('currency', 'USDT')
            symbol_pair = f"{pos['symbol']}/{currency}"
            if currency == 'JPY':
                print(f"   {pos['symbol']}:")
                print(f"     • Số lượng: {pos['amount']:.6f}")
                print(f"     • Giá hiện tại: ¥{pos['price']:,.2f}")
                print(f"     • Giá trị: ${pos['value']:,.2f}")
            else:
                print(f"   {pos['symbol']}:")
                print(f"     • Số lượng: {pos['amount']:.6f}")
                print(f"     • Giá hiện tại: ${pos['price']:,.4f}")
                print(f"     • Giá trị: ${pos['value']:,.2f}")
        
        print(f"\n🪙 TỔNG GIÁ TRỊ CRYPTO: ${total_crypto_value:,.2f}")
        
        # Tổng tài khoản
        total_account_value = total_fiat_value + total_crypto_value
        print(f"\n💎 TỔNG GIÁ TRỊ TÀI KHOẢN: ${total_account_value:,.2f}")
        
        # Kiểm tra orders đang mở
        print("\n📋 ORDERS ĐANG MỞ:")
        try:
            open_orders = binance.fetch_open_orders()
            if open_orders:
                print(f"   📊 Tổng cộng: {len(open_orders)} orders")
                for order in open_orders:
                    print(f"   • {order['symbol']}: {order['side'].upper()} {order['amount']:.6f} @ {order['price']:.4f}")
            else:
                print("   ✅ Không có orders đang mở")
        except Exception as e:
            print(f"   ⚠️ Không thể lấy thông tin orders: {e}")
        
        print("=" * 80)
        
        return {
            'fiat_value': total_fiat_value,
            'crypto_value': total_crypto_value,
            'total_value': total_account_value,
            'crypto_positions': crypto_positions
        }
        
    except Exception as e:
        print(f"❌ Lỗi lấy thông tin tài khoản: {e}")
        return None

def test_email_notification():
    """Test gửi email notification"""
    try:
        config = trading_config.NOTIFICATION_CONFIG
        
        if not config['email_enabled']:
            print("📧 Email notification đang TẮT")
            return False
        
        print("📧 KIỂM TRA EMAIL NOTIFICATION...")
        print(f"   • SMTP Server: {config['email_smtp']}:{config['email_port']}")
        print(f"   • Email gửi: {config['email_user']}")
        print(f"   • Email nhận: {config['email_to']}")
        
        # Tạo email test
        msg = MIMEMultipart()
        msg['From'] = config['email_user']
        msg['To'] = config['email_to']
        msg['Subject'] = "🧪 Test Auto Trading Notification"
        
        body = """
🚀 KIỂM TRA HỆ THỐNG NOTIFICATION

Đây là email test từ hệ thống Auto Trading.

📊 Thông tin:
• Thời gian: {}
• Trạng thái: Testing
• Platform: Binance Testnet

✅ Nếu bạn nhận được email này, hệ thống notification đã hoạt động!

--
Auto Trading System
        """.format("2025-07-27 18:51")
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Gửi email
        print("📤 Đang gửi email test...")
        server = smtplib.SMTP(config['email_smtp'], config['email_port'])
        server.starttls()
        server.login(config['email_user'], config['email_password'])
        
        text = msg.as_string()
        server.sendmail(config['email_user'], config['email_to'], text)
        server.quit()
        
        print("✅ Email test đã gửi thành công!")
        print(f"📬 Kiểm tra hộp thư: {config['email_to']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
        
        # Hướng dẫn sửa lỗi
        print("\n💡 HƯỚNG DẪN SỬA LỖI:")
        print("1. Kiểm tra App Password Gmail:")
        print("   - Vào Google Account Settings")
        print("   - Security > 2-Step Verification > App passwords") 
        print("   - Tạo App Password mới cho 'Mail'")
        print("   - Cập nhật vào trading_config.py")
        print("\n2. Kiểm tra email settings trong trading_config.py")
        print("3. Đảm bảo email_enabled = True")
        
        return False

def send_trading_notification(message, urgent=False):
    """Gửi thông báo trading"""
    try:
        config = trading_config.NOTIFICATION_CONFIG
        
        if not config['enabled'] or not config['email_enabled']:
            print(f"📱 Notification: {message}")
            return
        
        # Tạo email
        msg = MIMEMultipart()
        msg['From'] = config['email_user']
        msg['To'] = config['email_to']
        
        if urgent:
            msg['Subject'] = "🚨 URGENT - Auto Trading Alert"
        else:
            msg['Subject'] = "📊 Auto Trading Update"
        
        body = f"""
🤖 AUTO TRADING NOTIFICATION

{message}

📊 Platform: Binance Testnet
⏰ Thời gian: 2025-07-27 18:51

--
Auto Trading System
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Gửi email
        server = smtplib.SMTP(config['email_smtp'], config['email_port'])
        server.starttls()
        server.login(config['email_user'], config['email_password'])
        
        text = msg.as_string()
        server.sendmail(config['email_user'], config['email_to'], text)
        server.quit()
        
        print(f"📧 Đã gửi email: {message[:50]}...")
        
    except Exception as e:
        print(f"⚠️ Lỗi gửi notification: {e}")
        print(f"📱 Fallback: {message}")

if __name__ == "__main__":
    print("🧪 TEST ACCOUNT INFO & NOTIFICATIONS")
    print()
    
    # Test account info
    account_info = get_account_info()
    
    print()
    
    # Test email notification
    test_email_notification()
