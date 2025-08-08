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
                
                # Kiểm tra kích thước file và tự động maintenance nếu cần
                file_size_kb = os.path.getsize(self.file_path) / 1024
                if file_size_kb > 50:  # Nếu file > 50KB thì cleanup
                    print(f"⚠️ File position lớn ({file_size_kb:.1f} KB) - Chạy auto maintenance...")
                    self.auto_maintenance()
                
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
                    'active_sell_orders': [],  # Track active sell orders
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
            
            # Lưu thông tin lệnh mua (CHỈ GIỮ 10 LỆNH GẦN NHẤT)
            buy_order_info = {
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now().isoformat(),
                'order_id': order_id
            }
            
            # Thêm lệnh mới và giữ tối đa 10 lệnh gần nhất
            self.positions[coin]['buy_orders'].append(buy_order_info)
            if len(self.positions[coin]['buy_orders']) > 10:
                # Xóa lệnh cũ nhất, giữ 10 lệnh mới nhất
                self.positions[coin]['buy_orders'] = self.positions[coin]['buy_orders'][-10:]
                print(f"🧹 Đã cleanup buy_orders cũ cho {coin}, giữ 10 lệnh mới nhất")
            
            # Lưu vào file
            self.save_positions()
            
            position_info = self.positions[coin]
            print(f"📊 Cập nhật position {coin}:")
            print(f"   💰 Giá trung bình: ¥{position_info['average_price']:.4f}")
            print(f"   📦 Tổng quantity: {position_info['total_quantity']:.6f}")
            print(f"   💸 Tổng chi phí: ¥{position_info['total_cost']:.2f}")
            print(f"   📋 Buy orders lưu trữ: {len(position_info['buy_orders'])}")
            
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
    
    def calculate_pnl(self, symbol, quantity, current_price):
        """
        Tính P&L cho một lượng coin với giá hiện tại
        
        Args:
            symbol: Symbol coin
            quantity: Số lượng coin để tính P&L
            current_price: Giá hiện tại
        
        Returns:
            dict: Thông tin P&L
        """
        try:
            position = self.get_position(symbol)
            if not position:
                return None
            
            if quantity > position['total_quantity']:
                quantity = position['total_quantity']
            
            avg_entry_price = position['average_price']
            
            # Tính chi phí mua
            cost_basis = quantity * avg_entry_price
            
            # Tính giá trị hiện tại (trừ phí giao dịch)
            trading_fee = 0.001  # 0.1% fee
            current_value = quantity * current_price * (1 - trading_fee)
            
            # P&L
            profit_loss = current_value - cost_basis
            profit_loss_percent = (profit_loss / cost_basis) * 100 if cost_basis > 0 else 0
            
            return {
                'symbol': symbol,
                'quantity': quantity,
                'avg_entry_price': avg_entry_price,
                'current_price': current_price,
                'cost_basis': cost_basis,
                'current_value': current_value,
                'profit_loss': profit_loss,
                'profit_loss_percent': profit_loss_percent,
                'trading_fee': quantity * current_price * trading_fee
            }
            
        except Exception as e:
            print(f"❌ Lỗi tính P&L: {e}")
            return None

    def update_position_after_sell(self, symbol, quantity_sold, sell_price):
        """
        Cập nhật position sau khi bán coin (FIFO - First In First Out)
        
        Args:
            symbol: Symbol coin
            quantity_sold: Số lượng đã bán
            sell_price: Giá bán
        """
        try:
            coin = symbol.split('/')[0]
            if coin not in self.positions:
                print(f"❌ Không tìm thấy position cho {coin}")
                return False
            
            position = self.positions[coin]
            remaining_to_sell = quantity_sold
            
            # FIFO: Bán từ buy order cũ nhất trước
            updated_buy_orders = []
            
            for buy_order in position['buy_orders']:
                if remaining_to_sell <= 0:
                    updated_buy_orders.append(buy_order)
                    continue
                
                if buy_order['quantity'] <= remaining_to_sell:
                    # Bán hết order này
                    remaining_to_sell -= buy_order['quantity']
                else:
                    # Bán một phần order này
                    buy_order['quantity'] -= remaining_to_sell
                    buy_order['total_cost'] = buy_order['quantity'] * buy_order['price']
                    updated_buy_orders.append(buy_order)
                    remaining_to_sell = 0
            
            # Cập nhật position
            position['buy_orders'] = updated_buy_orders
            
            # Tính lại totals
            total_quantity = sum(order['quantity'] for order in updated_buy_orders)
            total_cost = sum(order['quantity'] * order['price'] for order in updated_buy_orders)
            
            if total_quantity > 0:
                position['total_quantity'] = total_quantity
                position['total_cost'] = total_cost
                position['average_price'] = total_cost / total_quantity
                
                print(f"📊 Cập nhật {coin} sau khi bán:")
                print(f"   📤 Đã bán: {quantity_sold:.6f} @ ¥{sell_price:.4f}")
                print(f"   📦 Còn lại: {total_quantity:.6f}")
                print(f"   💰 Giá TB: ¥{position['average_price']:.4f}")
            else:
                # Xóa position nếu bán hết
                del self.positions[coin]
                print(f"✅ Đã bán hết {coin}, xóa position")
            
            # Lưu file
            self.save_positions()
            return True
            
        except Exception as e:
            print(f"❌ Lỗi cập nhật position sau khi bán: {e}")
            return False

    def add_sell_order_tracking(self, symbol, order_id, order_type, quantity, price):
        """
        Thêm tracking cho sell order (SL/TP)
        
        Args:
            symbol: Symbol coin 
            order_id: ID của sell order
            order_type: 'STOP_LOSS' hoặc 'TAKE_PROFIT_1' hoặc 'TAKE_PROFIT_2'
            quantity: Số lượng bán
            price: Giá bán
        """
        try:
            coin = symbol.split('/')[0]
            if coin not in self.positions:
                print(f"❌ Không tìm thấy position cho {coin}")
                return False
            
            # Đảm bảo position có active_sell_orders field
            if 'active_sell_orders' not in self.positions[coin]:
                self.positions[coin]['active_sell_orders'] = []
            
            sell_order_info = {
                'order_id': str(order_id),
                'order_type': order_type,
                'quantity': quantity,
                'price': price,
                'status': 'ACTIVE',
                'created_at': datetime.now().isoformat()
            }
            
            self.positions[coin]['active_sell_orders'].append(sell_order_info)
            self.positions[coin]['updated_at'] = datetime.now().isoformat()
            
            # Lưu file
            self.save_positions()
            
            print(f"📊 Đã track sell order {order_id} cho {coin}: {order_type} @ ¥{price}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi track sell order: {e}")
            return False

    def check_and_sync_with_exchange(self, exchange_api):
        """
        Kiểm tra và đồng bộ với exchange - Handle cả auto fill và manual intervention
        
        Args:
            exchange_api: Đối tượng API để kiểm tra trạng thái lệnh
        """
        try:
            updated_positions = []
            manual_interventions = []
            
            for coin, position in self.positions.items():
                if not position.get('active_sell_orders'):
                    continue
                
                # Kiểm tra từng sell order
                for sell_order in position['active_sell_orders'][:]:  # Copy list để safe remove
                    if sell_order.get('status') != 'ACTIVE':
                        continue
                    
                    order_id = sell_order['order_id']
                    
                    try:
                        # Kiểm tra order có còn tồn tại trên exchange không
                        order_status = exchange_api.fetch_order(order_id, position['symbol'])
                        
                        if order_status['status'] == 'closed':
                            # Case 1: Lệnh đã tự động khớp
                            filled_quantity = sell_order['quantity']
                            filled_price = order_status.get('average', sell_order['price'])
                            
                            print(f"✅ AUTO FILL: {order_id} - {filled_quantity} {coin} @ ¥{filled_price}")
                            
                            # Update position sau khi bán
                            self.update_position_after_sell(
                                position['symbol'], 
                                filled_quantity, 
                                filled_price
                            )
                            
                            # Đánh dấu order đã filled
                            sell_order['status'] = 'FILLED'
                            sell_order['filled_at'] = datetime.now().isoformat()
                            sell_order['filled_price'] = filled_price
                            sell_order['fill_type'] = 'AUTO'
                            
                            updated_positions.append(coin)
                            
                        elif order_status['status'] in ['canceled', 'expired']:
                            # Order bị cancel/expire
                            print(f"⚠️ ORDER CANCELED: {order_id} - {coin}")
                            sell_order['status'] = 'CANCELED'
                            sell_order['canceled_at'] = datetime.now().isoformat()
                            
                    except Exception as order_error:
                        # Case 2: Order không tồn tại trên exchange = Manual intervention
                        error_msg = str(order_error).lower()
                        if "does not exist" in error_msg or "not found" in error_msg or "order" in error_msg:
                            
                            print(f"🔧 MANUAL INTERVENTION DETECTED: Order {order_id} không tồn tại trên exchange")
                            print(f"   → Có thể: 1) Lệnh đã khớp thủ công, 2) User đã hủy lệnh")
                            
                            # Kiểm tra balance để xác định có bán hay không
                            try:
                                account_info = exchange_api.get_account()
                                balances = {b['asset']: float(b['free']) for b in account_info['balances']}
                                current_balance = balances.get(coin, 0.0)
                                expected_balance = position['total_quantity']
                                
                                if current_balance < expected_balance:
                                    # Balance giảm = có bán coin
                                    sold_quantity = expected_balance - current_balance
                                    
                                    print(f"   💰 Balance check: Đã bán {sold_quantity} {coin}")
                                    print(f"   📊 Expected: {expected_balance}, Actual: {current_balance}")
                                    
                                    # Lấy giá hiện tại làm estimate
                                    ticker = exchange_api.get_symbol_ticker(symbol=position['symbol'])
                                    current_price = float(ticker['price'])
                                    
                                    # Update position
                                    self.update_position_after_sell(
                                        position['symbol'],
                                        sold_quantity,
                                        current_price
                                    )
                                    
                                    # Đánh dấu manual intervention
                                    sell_order['status'] = 'MANUAL_FILLED'
                                    sell_order['filled_at'] = datetime.now().isoformat()
                                    sell_order['filled_price'] = current_price
                                    sell_order['fill_type'] = 'MANUAL'
                                    sell_order['note'] = 'Detected via balance check'
                                    
                                    manual_interventions.append({
                                        'coin': coin,
                                        'action': 'SELL',
                                        'quantity': sold_quantity,
                                        'estimated_price': current_price,
                                        'detection_method': 'balance_check'
                                    })
                                    
                                    updated_positions.append(coin)
                                    
                                else:
                                    # Balance không đổi = chỉ hủy lệnh
                                    print(f"   ❌ Order bị hủy, không có giao dịch")
                                    sell_order['status'] = 'MANUAL_CANCELED'
                                    sell_order['canceled_at'] = datetime.now().isoformat()
                                    sell_order['fill_type'] = 'MANUAL'
                                    
                                    manual_interventions.append({
                                        'coin': coin,
                                        'action': 'CANCEL',
                                        'order_id': order_id,
                                        'detection_method': 'order_not_found'
                                    })
                                    
                            except Exception as balance_error:
                                print(f"   ❌ Không thể kiểm tra balance: {balance_error}")
                                # Fallback: đánh dấu unknown
                                sell_order['status'] = 'UNKNOWN'
                                sell_order['note'] = 'Manual intervention detected but could not verify'
                        else:
                            print(f"⚠️ Lỗi kiểm tra order {order_id}: {order_error}")
                            continue
            
            # Cleanup và save
            self.cleanup_old_sell_orders()
            
            # Report results
            if updated_positions:
                print(f"\n🔄 POSITIONS UPDATED: {updated_positions}")
            
            if manual_interventions:
                print(f"\n🔧 MANUAL INTERVENTIONS DETECTED:")
                for intervention in manual_interventions:
                    print(f"   - {intervention['coin']}: {intervention['action']}")
            
            return {
                'updated_positions': updated_positions,
                'manual_interventions': manual_interventions
            }
            
        except Exception as e:
            print(f"❌ Lỗi sync với exchange: {e}")
            return {'updated_positions': [], 'manual_interventions': []}

    def check_and_update_filled_orders(self, exchange_api):
        """
        Wrapper method để backward compatibility
        """
        result = self.check_and_sync_with_exchange(exchange_api)
        return result['updated_positions']

    def cleanup_old_sell_orders(self):
        """Cleanup sell orders cũ (giữ 10 orders gần nhất)"""
        try:
            for coin, position in self.positions.items():
                sell_orders = position.get('active_sell_orders', [])
                
                if len(sell_orders) > 10:
                    # Sắp xếp theo thời gian tạo, giữ 10 orders mới nhất
                    sorted_orders = sorted(sell_orders, 
                                         key=lambda x: x.get('created_at', ''), 
                                         reverse=True)
                    position['active_sell_orders'] = sorted_orders[:10]
                    
            self.save_positions()
            
        except Exception as e:
            print(f"❌ Lỗi cleanup sell orders: {e}")

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
    
    def optimize_file_size(self):
        """Tối ưu hóa kích thước file position_data.json"""
        try:
            optimized_count = 0
            
            for coin, pos in self.positions.items():
                # Giữ tối đa 5 buy orders gần nhất cho mỗi position
                if len(pos['buy_orders']) > 5:
                    old_count = len(pos['buy_orders'])
                    pos['buy_orders'] = pos['buy_orders'][-5:]  # Giữ 5 lệnh mới nhất
                    optimized_count += old_count - 5
                    print(f"🧹 Tối ưu {coin}: {old_count} → 5 buy orders")
            
            if optimized_count > 0:
                self.save_positions()
                print(f"✅ Đã tối ưu {optimized_count} buy orders cũ")
                
                # Kiểm tra kích thước file
                if os.path.exists(self.file_path):
                    file_size_kb = os.path.getsize(self.file_path) / 1024
                    print(f"📁 Kích thước file sau tối ưu: {file_size_kb:.1f} KB")
            
            return optimized_count
            
        except Exception as e:
            print(f"⚠️ Lỗi tối ưu file: {e}")
            return 0
    
    def get_file_stats(self):
        """Lấy thống kê về file position_data.json"""
        try:
            stats = {
                'exists': os.path.exists(self.file_path),
                'size_kb': 0,
                'total_positions': len(self.positions),
                'total_buy_orders': 0,
                'oldest_position': None,
                'newest_position': None
            }
            
            if stats['exists']:
                stats['size_kb'] = os.path.getsize(self.file_path) / 1024
            
            # Đếm tổng số buy orders
            oldest_date = None
            newest_date = None
            
            for coin, pos in self.positions.items():
                stats['total_buy_orders'] += len(pos['buy_orders'])
                
                # Tìm position cũ nhất và mới nhất
                created_at = datetime.fromisoformat(pos['created_at'])
                if oldest_date is None or created_at < oldest_date:
                    oldest_date = created_at
                    stats['oldest_position'] = coin
                
                updated_at = datetime.fromisoformat(pos['updated_at'])
                if newest_date is None or updated_at > newest_date:
                    newest_date = updated_at
                    stats['newest_position'] = coin
            
            return stats
            
        except Exception as e:
            print(f"⚠️ Lỗi lấy file stats: {e}")
            return None
    
    def auto_maintenance(self):
        """Tự động bảo trì file position_data.json"""
        try:
            print("🔧 Bắt đầu auto maintenance...")
            
            # 1. Lấy thống kê trước khi cleanup
            stats_before = self.get_file_stats()
            if stats_before:
                print(f"📊 Trước cleanup:")
                print(f"   📁 File size: {stats_before['size_kb']:.1f} KB")
                print(f"   📦 Positions: {stats_before['total_positions']}")
                print(f"   📋 Buy orders: {stats_before['total_buy_orders']}")
            
            # 2. Dọn dẹp positions cũ (30 ngày)
            cleaned_positions = self.cleanup_old_positions(30)
            
            # 3. Tối ưu hóa buy orders
            optimized_orders = self.optimize_file_size()
            
            # 4. Thống kê sau cleanup
            stats_after = self.get_file_stats()
            if stats_after:
                print(f"📊 Sau cleanup:")
                print(f"   📁 File size: {stats_after['size_kb']:.1f} KB")
                print(f"   📦 Positions: {stats_after['total_positions']}")
                print(f"   📋 Buy orders: {stats_after['total_buy_orders']}")
                
                if stats_before:
                    size_saved = stats_before['size_kb'] - stats_after['size_kb']
                    if size_saved > 0:
                        print(f"💾 Tiết kiệm: {size_saved:.1f} KB")
            
            print(f"✅ Auto maintenance hoàn thành!")
            print(f"   🗑️ Xóa {cleaned_positions} positions cũ")
            print(f"   🧹 Tối ưu {optimized_orders} buy orders")
            
        except Exception as e:
            print(f"❌ Lỗi auto maintenance: {e}")

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
