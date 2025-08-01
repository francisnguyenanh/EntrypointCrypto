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
        
        # Lấy balance
        balance = binance.fetch_balance()
        
        # Hiển thị số dư tiền tệ
        print("  SỐ DƯ TIỀN TỆ:")
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
        
        # Tính tổng giá trị crypto (không in chi tiết từng coin)
        total_crypto_value = 0
        for symbol, amounts in balance['total'].items():
            if amounts > 0 and symbol not in fiat_currencies:
                try:
                    ticker = binance.fetch_ticker(f"{symbol}/USDT")
                    current_price = ticker['last']
                    value_usd = amounts * current_price
                    total_crypto_value += value_usd
                except:
                    try:
                        ticker = binance.fetch_ticker(f"{symbol}/JPY")
                        current_price = ticker['last']
                        value_usd = amounts * current_price / 150
                        total_crypto_value += value_usd
                    except:
                        pass
        
        # Tổng tài khoản
        total_account_value = total_fiat_value + total_crypto_value
        
        # Kiểm tra orders đang mở
        print("\n  ORDERS ĐANG MỞ:")
        try:
            # Tắt cảnh báo về fetchOpenOrders không có symbol
            binance.options["warnOnFetchOpenOrdersWithoutSymbol"] = False
            open_orders = binance.fetch_open_orders()
            if open_orders:
                print(f"   📊 Tổng cộng: {len(open_orders)} orders")
                for order in open_orders:
                    print(f"   • {order['symbol']}: {order['side'].upper()} {order['amount']:.6f} @ {order['price']:.4f}")

        except Exception as e:
            print(f"   ⚠️ Không thể lấy thông tin orders: {e}")
        
        print("=" * 80)
        
        return {
            'fiat_value': total_fiat_value,
            'crypto_value': total_crypto_value,
            'total_value': total_account_value,
            # Không trả về danh sách crypto_positions nữa
        }
        
    except Exception as e:
        print(f"❌ Lỗi lấy thông tin tài khoản: {e}")
        return None

def test_email_notification():
    """Test gửi email notification - CHỈ để kiểm tra cấu hình"""
    try:
        config = trading_config.NOTIFICATION_CONFIG
        
        if not config['email_enabled']:
            print("📧 Email notification đang TẮT")
            return False
        
        
        # CHỈ test connection, KHÔNG gửi email
        try:
            server = smtplib.SMTP(config['email_smtp_server'], config['email_smtp_port'])
            server.starttls()
            server.login(config['email_sender'], config['email_password'])
            server.quit()
            
            return True
            
        except Exception as conn_error:
            print(f"❌ Lỗi kết nối email: {conn_error}")
            return False
        
    except Exception as e:
        print(f"❌ Lỗi kiểm tra email: {e}")
        
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
        msg['From'] = config['email_sender']
        msg['To'] = config['email_recipient']
        
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
        server = smtplib.SMTP(config['email_smtp_server'], config['email_smtp_port'])
        server.starttls()
        server.login(config['email_sender'], config['email_password'])
        
        text = msg.as_string()
        server.sendmail(config['email_sender'], config['email_recipient'], text)
        server.quit()
        
        print(f"📧 Đã gửi email: {message[:50]}...")
        
    except Exception as e:
        print(f"⚠️ Lỗi gửi notification: {e}")
        print(f"📱 Fallback: {message}")

def send_buy_success_notification(order_details):
    """Gửi email thông báo mua thành công"""
    try:
        config = trading_config.NOTIFICATION_CONFIG
        
        if not config['enabled'] or not config['email_enabled']:
            print(f"📱 Buy Success: {order_details['symbol']} - {order_details['quantity']:,.6f} @ ${order_details['price']:,.4f}")
            return
        
        # Tạo email
        msg = MIMEMultipart()
        msg['From'] = config['email_sender']
        msg['To'] = config['email_recipient']
        msg['Subject'] = f"✅ MUA THÀNH CÔNG - {order_details['symbol']}"
        
        body = f"""
✅ LỆNH MUA THÀNH CÔNG

📊 Chi tiết lệnh:
• Symbol: {order_details['symbol']}
• Số lượng: {order_details['quantity']:,.6f}
• Giá mua: ${order_details['price']:,.4f}
• Tổng tiền: ${order_details['total']:,.2f}
• Order ID: {order_details.get('order_id', 'N/A')}

  Thông tin tài khoản:
• Số dư trước: ${order_details.get('balance_before', 'N/A') if isinstance(order_details.get('balance_before'), str) else f"{order_details.get('balance_before', 0):,.2f}"}
• Số dư sau: ${order_details.get('balance_after', 'N/A') if isinstance(order_details.get('balance_after'), str) else f"{order_details.get('balance_after', 0):,.2f}"}

🎯 Lệnh bán tự động:
• Stop Loss: ${order_details.get('stop_loss', 'N/A') if isinstance(order_details.get('stop_loss'), str) else f"{order_details.get('stop_loss', 0):,.4f}"}
• Take Profit 1: ${order_details.get('tp1', 'N/A') if isinstance(order_details.get('tp1'), str) else f"{order_details.get('tp1', 0):,.4f}"}
• Take Profit 2: ${order_details.get('tp2', 'N/A') if isinstance(order_details.get('tp2'), str) else f"{order_details.get('tp2', 0):,.4f}"}

📊 Platform: Binance Testnet
⏰ Thời gian: {order_details.get('timestamp', '2025-07-28')}

--
Auto Trading System
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Gửi email
        server = smtplib.SMTP(config['email_smtp_server'], config['email_smtp_port'])
        server.starttls()
        server.login(config['email_sender'], config['email_password'])
        
        text = msg.as_string()
        server.sendmail(config['email_sender'], config['email_recipient'], text)
        server.quit()
        
        print(f"📧 Đã gửi email mua thành công: {order_details['symbol']}")
        
    except Exception as e:
        print(f"⚠️ Lỗi gửi email mua thành công: {e}")

def send_sell_order_placed_notification(order_details):
    """Gửi email thông báo đặt lệnh bán thành công"""
    try:
        config = trading_config.NOTIFICATION_CONFIG
        
        if not config['enabled'] or not config['email_enabled']:
            print(f"📱 Sell Orders Placed: {order_details['symbol']} - SL: ${order_details['stop_loss']:,.4f}")
            return
        
        # Tạo email
        msg = MIMEMultipart()
        msg['From'] = config['email_sender']
        msg['To'] = config['email_recipient']
        msg['Subject'] = f"🎯 ĐẶT LỆNH BÁN - {order_details['symbol']}"
        
        body = f"""
🎯 LỆNH BÁN ĐÃ ĐẶT THÀNH CÔNG

📊 Chi tiết:
• Symbol: {order_details['symbol']}
• Số lượng gốc: {order_details['original_quantity']:,.6f}
• Giá mua gốc: ${order_details['buy_price']:,.4f}

🛡️ Stop Loss:
• Order ID: {order_details.get('sl_order_id', 'N/A')}
• Giá: ${order_details['stop_loss']:,.4f}
• Số lượng: {order_details['original_quantity']:,.6f}

🎯 Take Profit Orders:
• TP1 ID: {order_details.get('tp1_order_id', 'N/A')}
• TP1 Giá: ${order_details.get('tp1_price', 0):,.4f}
• TP1 Số lượng: {order_details.get('tp1_quantity', 0):,.6f}

• TP2 ID: {order_details.get('tp2_order_id', 'N/A')}
• TP2 Giá: ${order_details.get('tp2_price', 0):,.4f}
• TP2 Số lượng: {order_details.get('tp2_quantity', 0):,.6f}

💡 Các lệnh này sẽ được bot theo dõi tự động.

📊 Platform: Binance Testnet
⏰ Thời gian: {order_details.get('timestamp', '2025-07-28')}

--
Auto Trading System
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Gửi email
        server = smtplib.SMTP(config['email_smtp_server'], config['email_smtp_port'])
        server.starttls()
        server.login(config['email_sender'], config['email_password'])
        
        text = msg.as_string()
        server.sendmail(config['email_sender'], config['email_recipient'], text)
        server.quit()
        
        print(f"📧 Đã gửi email đặt lệnh bán: {order_details['symbol']}")
        
    except Exception as e:
        print(f"⚠️ Lỗi gửi email đặt lệnh bán: {e}")

def send_sell_success_notification(order_details):
    """Gửi email thông báo bán thành công"""
    try:
        config = trading_config.NOTIFICATION_CONFIG
        
        if not config['enabled'] or not config['email_enabled']:
            print(f"📱 Sell Success: {order_details['symbol']} - Profit: ${order_details.get('profit_loss', 0):,.2f} ({order_details.get('profit_percent', 0):+.2f}%)")
            return
        
        # Tạo email
        msg = MIMEMultipart()
        msg['From'] = config['email_sender']
        msg['To'] = config['email_recipient']
        msg['Subject'] = f"  BÁN THÀNH CÔNG - {order_details['symbol']}"
        
        profit_emoji = "📈" if order_details.get('profit_amount', 0) > 0 else "📉"
        
        body = f"""
  LỆNH BÁN THÀNH CÔNG

📊 Chi tiết lệnh:
• Symbol: {order_details['symbol']}
• Loại lệnh: {order_details.get('order_type', 'N/A')}
• Số lượng bán: {order_details['quantity']:,.6f}
• Giá bán: ${order_details['filled_price']:,.4f}
• Tổng tiền nhận: ${order_details.get('total_received', order_details['quantity'] * order_details['filled_price']):,.2f}
• Order ID: {order_details.get('order_id', 'N/A')}

💹 Kết quả giao dịch:
• Giá mua gốc: ${order_details.get('buy_price', 0):,.4f}
• Giá bán: ${order_details['filled_price']:,.4f}
• {profit_emoji} Lợi nhuận: ${order_details.get('profit_loss', 0):,.2f}
• 📊 % Thay đổi: {order_details.get('profit_percent', 0):+.2f}%

  Tài khoản:
• Số dư sau bán: ${order_details.get('balance_after', 'N/A') if isinstance(order_details.get('balance_after'), str) else f"{order_details.get('balance_after', 0):,.2f}"}

🔄 Bot sẽ tự động tìm cơ hội đầu tư tiếp theo...

📊 Platform: Binance Testnet
⏰ Thời gian: {order_details.get('timestamp', '2025-07-28')}

--
Auto Trading System
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Gửi email
        server = smtplib.SMTP(config['email_smtp_server'], config['email_smtp_port'])
        server.starttls()
        server.login(config['email_sender'], config['email_password'])
        
        text = msg.as_string()
        server.sendmail(config['email_sender'], config['email_recipient'], text)
        server.quit()
        
        print(f"📧 Đã gửi email bán thành công: {order_details['symbol']}")
        
    except Exception as e:
        print(f"⚠️ Lỗi gửi email bán thành công: {e}")

if __name__ == "__main__":
    print("🧪 TEST ACCOUNT INFO & NOTIFICATIONS")
    print()
    
    # Test account info
    account_info = get_account_info()
    
    print()
    
    # Test email notification
    test_email_notification()
