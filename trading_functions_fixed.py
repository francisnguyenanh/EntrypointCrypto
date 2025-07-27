#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixed Trading Functions - Chỉ hỗ trợ JPY pairs
"""

def place_buy_order_with_sl_tp_fixed(symbol, quantity, entry_price, stop_loss, tp1_price, tp2_price):
    """
    ĐẶT LỆNH MUA VỚI STOP LOSS VÀ TAKE PROFIT - JPY ONLY
    
    Bao gồm:
    1. Kiểm tra số dư trước khi mua
    2. Đặt lệnh mua
    3. Kiểm tra lệnh mua thành công
    4. Đặt stop loss và take profit
    """
    import ccxt
    import trading_config
    
    # Khởi tạo exchange
    binance = ccxt.binance(trading_config.BINANCE_CONFIG)
    
    try:
        trading_symbol = symbol  # Trade trực tiếp JPY
        
        print(f"\n🔄 Đang đặt lệnh mua {trading_symbol}...")
        print(f"📊 Số lượng: {quantity:.6f}")
        print(f"💰 Giá entry: ¥{entry_price:.2f}")
        
        # ===== 1. KIỂM TRA SỐ DƯ TRƯỚC KHI MUA =====
        print("💰 Kiểm tra số dư...")
        balance = binance.fetch_balance()
        
        # Kiểm tra số dư JPY hoặc USDT
        jpy_balance = balance['free'].get('JPY', 0)
        usdt_balance = balance['free'].get('USDT', 0)
        
        if jpy_balance > 0:
            available_balance = jpy_balance
            currency = 'JPY'
            print(f"💰 Số dư JPY: ¥{jpy_balance:.2f}")
        elif usdt_balance > 0:
            # Chuyển đổi USDT sang JPY để tính toán
            available_balance = usdt_balance * 150  # 1 USD ≈ 150 JPY
            currency = 'USDT (converted)'
            print(f"💰 Số dư USDT: ${usdt_balance:.2f} ≈ ¥{available_balance:.2f}")
        else:
            return {
                'status': 'failed',
                'error': 'Không có số dư JPY hoặc USDT'
            }
        
        # Tính giá trị lệnh cần thiết
        order_value = quantity * entry_price
        print(f"💰 Giá trị lệnh cần: ¥{order_value:.2f}")
        
        if order_value > available_balance:
            return {
                'status': 'failed',
                'error': f'Không đủ số dư. Cần ¥{order_value:.2f}, có ¥{available_balance:.2f}'
            }
        
        # ===== 2. ĐẶT LỆNH MUA =====
        print("💸 Đang thực hiện lệnh mua...")
        buy_order = binance.create_market_buy_order(trading_symbol, quantity)
        print(f"✅ Lệnh mua thành công - ID: {buy_order['id']}")
        
        # ===== 3. KIỂM TRA LỆNH MUA ĐÃ THÀNH CÔNG =====
        actual_price = float(buy_order['average']) if buy_order['average'] else entry_price
        actual_quantity = float(buy_order['filled'])
        
        if actual_quantity == 0:
            return {
                'status': 'failed',
                'error': 'Lệnh mua không được thực hiện (quantity = 0)'
            }
        
        print(f"📈 Giá mua thực tế: ¥{actual_price:.2f}")
        print(f"📊 Số lượng thực tế: {actual_quantity:.6f}")
        
        # ===== 4. ĐẶT STOP LOSS VÀ TAKE PROFIT =====
        orders_placed = []
        
        try:
            # Đặt Stop Loss cho 70% số lượng
            sl_quantity = actual_quantity * 0.7
            print(f"🛡️ Đang đặt Stop Loss: ¥{stop_loss:.2f} cho {sl_quantity:.6f}")
            
            stop_loss_order = binance.create_order(
                symbol=trading_symbol,
                type='STOP_LOSS_LIMIT',
                side='sell',
                amount=sl_quantity,
                price=stop_loss * 0.999,  # Giá limit thấp hơn stop price
                params={
                    'stopPrice': stop_loss,
                    'timeInForce': 'GTC'
                }
            )
            orders_placed.append(stop_loss_order)
            print(f"✅ Stop Loss đặt thành công")
            
        except Exception as sl_error:
            print(f"⚠️ Lỗi đặt stop loss: {sl_error}")
        
        try:
            # Đặt Take Profit 1 cho 20% số lượng
            tp1_quantity = actual_quantity * 0.2
            print(f"🎯 Đang đặt Take Profit 1: ¥{tp1_price:.2f} cho {tp1_quantity:.6f}")
            
            tp1_order = binance.create_limit_sell_order(trading_symbol, tp1_quantity, tp1_price)
            orders_placed.append(tp1_order)
            print(f"✅ Take Profit 1 đặt thành công")
            
        except Exception as tp1_error:
            print(f"⚠️ Lỗi đặt TP1: {tp1_error}")
        
        try:
            # Đặt Take Profit 2 cho 10% số lượng còn lại
            if abs(tp2_price - tp1_price) > 1:  # Chỉ đặt nếu TP2 khác TP1
                tp2_quantity = actual_quantity * 0.1
                tp2_value = tp2_quantity * tp2_price
                
                # Kiểm tra giá trị tối thiểu (thường 10-11 USDT)
                if tp2_value < 15:  # Skip nếu order quá nhỏ
                    print(f"⚠️ TP2 order quá nhỏ (¥{tp2_value:.2f}), bỏ qua")
                else:
                    print(f"🎯 Đang đặt Take Profit 2: ¥{tp2_price:.2f} cho {tp2_quantity:.6f}")
                    
                    tp2_order = binance.create_limit_sell_order(trading_symbol, tp2_quantity, tp2_price)
                    orders_placed.append(tp2_order)
                    print(f"✅ Take Profit 2 đặt thành công")
            
        except Exception as tp2_error:
            print(f"⚠️ Lỗi đặt TP2: {tp2_error}")
        
        # ===== 5. TRẢ VỀ KẾT QUẢ =====
        print(f"🎉 Hoàn thành! Đã đặt {len(orders_placed)} orders bổ sung")
        
        return {
            'status': 'success',
            'buy_order': buy_order,
            'sl_tp_orders': orders_placed,
            'actual_price': actual_price,
            'actual_quantity': actual_quantity,
            'trading_symbol': trading_symbol,
            'total_orders': len(orders_placed) + 1,
            'breakdown': {
                'stop_loss': f"70% @ ¥{stop_loss:.2f}",
                'take_profit_1': f"20% @ ¥{tp1_price:.2f}",
                'take_profit_2': f"10% @ ¥{tp2_price:.2f}" if abs(tp2_price - tp1_price) > 1 else "Không đặt"
            }
        }
        
    except Exception as e:
        error_msg = f"Lỗi đặt lệnh: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'status': 'failed',
            'error': error_msg
        }

if __name__ == "__main__":
    print("🧪 Test Fixed Trading Functions")
    
    # Test với SUI/JPY
    result = place_buy_order_with_sl_tp_fixed(
        symbol='SUI/JPY',
        quantity=1.0,  # Test nhỏ
        entry_price=620.0,
        stop_loss=600.0,
        tp1_price=640.0,
        tp2_price=660.0
    )
    
    print(f"\n📊 Kết quả test: {result['status']}")
    if result['status'] == 'success':
        print(f"✅ Breakdown: {result['breakdown']}")
    else:
        print(f"❌ Lỗi: {result['error']}")
