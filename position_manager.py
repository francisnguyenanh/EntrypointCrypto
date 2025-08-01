#!/usr/bin/env python3
"""
Position Manager - Quản lý giá mua trung bình cho từng coin
"""

import json
import time
from datetime import datetime
import os

class PositionManager:
    def __init__(self, file_path='position_data.json'):
        self.file_path = file_path
        self.positions = {}
        self.load_positions()
    
    def load_positions(self):
        """Đọc dữ liệu position từ file"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.positions = json.load(f)
                print(f"📂 Đã tải {len(self.positions)} position từ {self.file_path}")
            else:
                self.positions = {}
                self.save_positions()
                print(f"📂 Tạo file position mới: {self.file_path}")
        except Exception as e:
            print(f"⚠️ Lỗi đọc position file: {e}")
            self.positions = {}
    
    def save_positions(self):
        """Lưu dữ liệu position vào file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.positions, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"⚠️ Lỗi lưu position file: {e}")
    
    def add_buy_order(self, symbol, quantity, price, order_id=None):
        """
        Thêm lệnh mua mới và cập nhật giá trung bình
        
        Args:
            symbol: Symbol coin (VD: 'ADA/JPY')
            quantity: Số lượng mua
            price: Giá mua
            order_id: ID lệnh (optional)
        
        Returns:
            dict: Thông tin position cập nhật
        """
        try:
            coin = symbol.split('/')[0]  # Lấy ADA từ ADA/JPY
            
            if coin not in self.positions:
                # Position mới
                self.positions[coin] = {
                    'symbol': symbol,
                    'total_quantity': quantity,
                    'total_cost': quantity * price,
                    'average_price': price,
                    'buy_orders': [],
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            else:
                # Cập nhật position hiện có
                current_pos = self.positions[coin]
                
                # Tính toán giá trung bình mới
                old_total_cost = current_pos['total_cost']
                old_total_quantity = current_pos['total_quantity']
                
                new_total_quantity = old_total_quantity + quantity
                new_total_cost = old_total_cost + (quantity * price)
                new_average_price = new_total_cost / new_total_quantity
                
                # Cập nhật position
                current_pos['total_quantity'] = new_total_quantity
                current_pos['total_cost'] = new_total_cost
                current_pos['average_price'] = new_average_price
                current_pos['updated_at'] = datetime.now().isoformat()
            
            # Lưu thông tin lệnh mua
            buy_order_info = {
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now().isoformat(),
                'order_id': order_id
            }
            self.positions[coin]['buy_orders'].append(buy_order_info)
            
            # Lưu vào file
            self.save_positions()
            
            position_info = self.positions[coin]
            print(f"📊 Cập nhật position {coin}:")
            print(f"   💰 Giá trung bình: ¥{position_info['average_price']:.4f}")
            print(f"   📦 Tổng quantity: {position_info['total_quantity']:.6f}")
            print(f"   💸 Tổng chi phí: ¥{position_info['total_cost']:.2f}")
            
            return position_info
            
        except Exception as e:
            print(f"❌ Lỗi thêm buy order: {e}")
            return None
    
    def get_position(self, symbol):
        """
        Lấy thông tin position của coin
        
        Args:
            symbol: Symbol coin (VD: 'ADA/JPY')
        
        Returns:
            dict: Thông tin position hoặc None
        """
        coin = symbol.split('/')[0]
        return self.positions.get(coin, None)
    
    def remove_position(self, symbol, quantity_sold=None):
        """
        Xóa hoặc giảm position khi bán coin
        
        Args:
            symbol: Symbol coin
            quantity_sold: Số lượng bán (None = bán hết)
        
        Returns:
            dict: Thông tin position còn lại hoặc None
        """
        try:
            coin = symbol.split('/')[0]
            
            if coin not in self.positions:
                print(f"⚠️ Không tìm thấy position cho {coin}")
                return None
            
            if quantity_sold is None:
                # Bán hết
                removed_position = self.positions.pop(coin)
                print(f"🗑️ Đã xóa position {coin} (bán hết)")
                self.save_positions()
                return None
            else:
                # Bán một phần
                current_pos = self.positions[coin]
                remaining_quantity = current_pos['total_quantity'] - quantity_sold
                
                if remaining_quantity <= 0:
                    # Bán hết
                    removed_position = self.positions.pop(coin)
                    print(f"🗑️ Đã xóa position {coin} (bán hết)")
                    self.save_positions()
                    return None
                else:
                    # Còn lại một phần
                    # Tính lại cost (giữ nguyên average price)
                    current_pos['total_quantity'] = remaining_quantity
                    current_pos['total_cost'] = remaining_quantity * current_pos['average_price']
                    current_pos['updated_at'] = datetime.now().isoformat()
                    
                    print(f"📉 Giảm position {coin}:")
                    print(f"   📦 Còn lại: {remaining_quantity:.6f}")
                    print(f"   💰 Giá TB: ¥{current_pos['average_price']:.4f}")
                    
                    self.save_positions()
                    return current_pos
                    
        except Exception as e:
            print(f"❌ Lỗi xóa position: {e}")
            return None
    
    def calculate_sl_tp_prices(self, symbol, sl_percent=3, tp1_percent=2, tp2_percent=5):
        """
        Tính toán giá SL và TP dựa trên giá trung bình
        
        Args:
            symbol: Symbol coin
            sl_percent: % stop loss (default 3%)
            tp1_percent: % take profit 1 (default 2%)  
            tp2_percent: % take profit 2 (default 5%)
        
        Returns:
            dict: Giá SL, TP1, TP2
        """
        try:
            position = self.get_position(symbol)
            if not position:
                return None
            
            avg_price = position['average_price']
            
            # Tính giá có tính phí giao dịch (0.1% mỗi lệnh)
            trading_fee = 0.001  # 0.1%
            
            sl_price = avg_price * (1 - sl_percent / 100)
            tp1_price = avg_price * (1 + (tp1_percent + trading_fee * 2 * 100) / 100)  # +phí
            tp2_price = avg_price * (1 + (tp2_percent + trading_fee * 2 * 100) / 100)  # +phí
            
            return {
                'average_entry': avg_price,
                'stop_loss': sl_price,
                'tp1_price': tp1_price,
                'tp2_price': tp2_price,
                'total_quantity': position['total_quantity'],
                'total_cost': position['total_cost']
            }
            
        except Exception as e:
            print(f"❌ Lỗi tính SL/TP: {e}")
            return None
    
    def get_all_positions(self):
        """Lấy tất cả positions hiện có"""
        return self.positions
    
    def get_position_summary(self):
        """Tóm tắt tất cả positions"""
        if not self.positions:
            return "✅ Không có position nào"
        
        summary = f"📊 TỔNG QUAN POSITIONS ({len(self.positions)} coin):\n"
        total_value = 0
        
        for coin, pos in self.positions.items():
            value = pos['total_cost']
            total_value += value
            summary += f"   💰 {coin}: {pos['total_quantity']:.6f} @ ¥{pos['average_price']:.4f} = ¥{value:.2f}\n"
        
        summary += f"💸 Tổng giá trị: ¥{total_value:.2f}"
        return summary
    
    def cleanup_old_positions(self, days=30):
        """Dọn dẹp positions cũ không hoạt động"""
        try:
            current_time = datetime.now()
            positions_to_remove = []
            
            for coin, pos in self.positions.items():
                updated_at = datetime.fromisoformat(pos['updated_at'])
                days_diff = (current_time - updated_at).days
                
                if days_diff > days:
                    positions_to_remove.append(coin)
            
            for coin in positions_to_remove:
                self.positions.pop(coin)
                print(f"🗑️ Dọn dẹp position cũ: {coin}")
            
            if positions_to_remove:
                self.save_positions()
                return len(positions_to_remove)
            
            return 0
            
        except Exception as e:
            print(f"⚠️ Lỗi dọn dẹp positions: {e}")
            return 0

# Khởi tạo global position manager
position_manager = PositionManager()

if __name__ == "__main__":
    # Test position manager
    print("🧪 Testing Position Manager")
    print("=" * 40)
    
    # Test thêm lệnh mua
    position_manager.add_buy_order('ADA/JPY', 100, 110.5, 'order_1')
    position_manager.add_buy_order('ADA/JPY', 50, 115.0, 'order_2')  # Giá cao hơn
    
    # Test tính SL/TP
    sl_tp = position_manager.calculate_sl_tp_prices('ADA/JPY')
    if sl_tp:
        print(f"\n📊 SL/TP cho ADA:")
        print(f"   🎯 Entry TB: ¥{sl_tp['average_entry']:.4f}")
        print(f"   🛡️ Stop Loss: ¥{sl_tp['stop_loss']:.4f}")
        print(f"   🎯 TP1: ¥{sl_tp['tp1_price']:.4f}")
        print(f"   🎯 TP2: ¥{sl_tp['tp2_price']:.4f}")
    
    # Test summary
    print(f"\n{position_manager.get_position_summary()}")
