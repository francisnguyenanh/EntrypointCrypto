#!/usr/bin/env python3
"""
Demo thực tế: Position Manager với Trading Bot
Mô phỏng scenario mua coin nhiều lần với giá khác nhau
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from position_manager import position_manager

def demo_real_trading_scenario():
    """Demo scenario thực tế với ADA/JPY"""
    
    print("🎬 DEMO: REAL TRADING SCENARIO WITH POSITION MANAGER")
    print("=" * 70)
    
    # Scenario: Bot mua ADA nhiều lần trong ngày
    print("📅 NGÀY TRADING 01/08/2025 - ADA/JPY")
    print("-" * 40)
    
    # Lần 1: 09:00 - Phát hiện tín hiệu mua đầu tiên
    print("🕘 09:00 - Tín hiệu BUY đầu tiên")
    pos1 = position_manager.add_buy_order('ADA/JPY', 150, 108.50, 'order_morning_1')
    sl_tp1 = position_manager.calculate_sl_tp_prices('ADA/JPY')
    
    print(f"   🎯 SL: ¥{sl_tp1['stop_loss']:.4f} | TP1: ¥{sl_tp1['tp1_price']:.4f} | TP2: ¥{sl_tp1['tp2_price']:.4f}")
    
    # Lần 2: 14:30 - Giá giảm, bot mua thêm (DCA)
    print("\n🕑 14:30 - Giá giảm → DCA thêm")
    pos2 = position_manager.add_buy_order('ADA/JPY', 100, 105.20, 'order_afternoon_1')
    sl_tp2 = position_manager.calculate_sl_tp_prices('ADA/JPY')
    
    print(f"   📉 Giá entry TB giảm: ¥{sl_tp1['average_entry']:.4f} → ¥{sl_tp2['average_entry']:.4f}")
    print(f"   🎯 SL mới: ¥{sl_tp2['stop_loss']:.4f} | TP1: ¥{sl_tp2['tp1_price']:.4f}")
    
    # Lần 3: 16:45 - Tín hiệu mạnh, mua thêm với giá cao hơn
    print("\n🕐 16:45 - Tín hiệu mạnh → Mua thêm")
    pos3 = position_manager.add_buy_order('ADA/JPY', 200, 109.80, 'order_evening_1')
    sl_tp3 = position_manager.calculate_sl_tp_prices('ADA/JPY')
    
    print(f"   📈 Giá entry TB tăng: ¥{sl_tp2['average_entry']:.4f} → ¥{sl_tp3['average_entry']:.4f}")
    print(f"   🎯 SL mới: ¥{sl_tp3['stop_loss']:.4f} | TP1: ¥{sl_tp3['tp1_price']:.4f}")
    
    # Hiển thị tổng quan position cuối ngày
    print(f"\n📊 TỔNG QUAN POSITION CUỐI NGÀY:")
    print(f"   📦 Tổng quantity: {sl_tp3['total_quantity']:.6f} ADA")
    print(f"   💰 Giá entry trung bình: ¥{sl_tp3['average_entry']:.4f}")
    print(f"   💸 Tổng đầu tư: ¥{sl_tp3['total_cost']:,.2f}")
    
    # Scenario bán vào ngày hôm sau
    print(f"\n📅 NGÀY TRADING 02/08/2025 - CHỐT LỜI")
    print("-" * 40)
    
    # TP1 được kích hoạt
    print("🎯 TP1 được kích hoạt tại ¥111.50")
    tp1_quantity = sl_tp3['total_quantity'] * 0.4  # Bán 40% tại TP1
    sell_result1 = position_manager.remove_position('ADA/JPY', tp1_quantity)
    
    # Tính P&L cho lệnh TP1
    pnl_tp1 = (111.50 - sl_tp3['average_entry']) * tp1_quantity
    pnl_percent_tp1 = (111.50 - sl_tp3['average_entry']) / sl_tp3['average_entry'] * 100
    
    print(f"   💰 Bán {tp1_quantity:.0f} ADA @ ¥111.50")
    print(f"   📈 P&L: ¥{pnl_tp1:+.2f} ({pnl_percent_tp1:+.2f}%)")
    
    # Giá tiếp tục tăng, TP2 được kích hoạt  
    print(f"\n🎯 TP2 được kích hoạt tại ¥115.20")
    remaining_pos = position_manager.get_position('ADA/JPY')
    if remaining_pos:
        tp2_quantity = remaining_pos['total_quantity'] * 0.6  # Bán 60% còn lại
        sell_result2 = position_manager.remove_position('ADA/JPY', tp2_quantity)
        
        pnl_tp2 = (115.20 - sl_tp3['average_entry']) * tp2_quantity
        pnl_percent_tp2 = (115.20 - sl_tp3['average_entry']) / sl_tp3['average_entry'] * 100
        
        print(f"   💰 Bán {tp2_quantity:.0f} ADA @ ¥115.20")
        print(f"   📈 P&L: ¥{pnl_tp2:+.2f} ({pnl_percent_tp2:+.2f}%)")
    
    # Giữ lại một phần để hold dài hạn
    final_pos = position_manager.get_position('ADA/JPY')
    if final_pos:
        print(f"\n🏦 Giữ lại để hold: {final_pos['total_quantity']:.0f} ADA @ ¥{final_pos['average_price']:.4f}")
        
        # Unrealized P&L nếu giá hiện tại là ¥118.0
        current_price = 118.0
        unrealized_pnl = (current_price - final_pos['average_price']) * final_pos['total_quantity']
        unrealized_percent = (current_price - final_pos['average_price']) / final_pos['average_price'] * 100
        
        print(f"   📊 Unrealized P&L @ ¥{current_price}: ¥{unrealized_pnl:+.2f} ({unrealized_percent:+.2f}%)")
    
    # Tổng kết P&L
    total_pnl = pnl_tp1 + pnl_tp2 + (unrealized_pnl if final_pos else 0)
    total_investment = sl_tp3['total_cost']
    total_return_percent = total_pnl / total_investment * 100
    
    print(f"\n🏆 TỔNG KẾT TRADING SESSION:")
    print(f"   💸 Tổng đầu tư: ¥{total_investment:,.2f}")
    print(f"   💰 Realized P&L: ¥{pnl_tp1 + pnl_tp2:+.2f}")
    print(f"   📊 Unrealized P&L: ¥{unrealized_pnl if final_pos else 0:+.2f}")
    print(f"   🎯 Total P&L: ¥{total_pnl:+.2f} ({total_return_percent:+.2f}%)")
    
    print(f"\n" + "=" * 70)
    print("💡 BENEFITS OF POSITION MANAGER:")
    print("✅ Chính xác: SL/TP luôn dựa trên giá entry trung bình")  
    print("✅ Tự động: Không cần tính toán thủ công")
    print("✅ An toàn: Tránh đặt SL/TP sai do mất dấu giá mua")
    print("✅ Minh bạch: P&L tracking chính xác từng giao dịch")
    print("✅ Linh hoạt: Có thể bán từng phần mà vẫn track đúng")

if __name__ == "__main__":
    demo_real_trading_scenario()
