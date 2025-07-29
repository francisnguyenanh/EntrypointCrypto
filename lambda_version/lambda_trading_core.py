"""
Lambda Trading Core - Phiên bản tối ưu cho AWS Lambda
- Không sử dụng threading (Lambda không hỗ trợ tốt)
- Sử dụng DynamoDB thay vì file storage
- Tối ưu thời gian thực thi
"""

import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

from lambda_config import LAMBDA_CONFIG, BINANCE_CONFIG
from lambda_dynamodb import DynamoDBManager
from lambda_notifications import LambdaNotificationManager

logger = logging.getLogger(__name__)

class LambdaTradingBot:
    """Trading Bot tối ưu cho AWS Lambda"""
    
    def __init__(self):
        """Initialize Lambda Trading Bot"""
        try:
            # Initialize Binance API
            self.binance = ccxt.binance(BINANCE_CONFIG)
            
            # Initialize DynamoDB
            self.db = DynamoDBManager()
            
            # Initialize notifications
            self.notifications = LambdaNotificationManager()
            
            # Trading config
            self.config = LAMBDA_CONFIG
            
            logger.info("Lambda Trading Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Lambda Trading Bot: {e}")
            raise
    
    def check_emergency_stop(self) -> bool:
        """Kiểm tra emergency stop từ DynamoDB"""
        try:
            emergency_status = self.db.get_system_status('emergency_stop')
            return emergency_status.get('value', False)
        except Exception as e:
            logger.error(f"Error checking emergency stop: {e}")
            return False
    
    def get_account_info(self) -> Optional[Dict]:
        """Lấy thông tin tài khoản"""
        try:
            balance = self.binance.fetch_balance()
            
            # Lấy số dư JPY
            jpy_balance = balance.get('JPY', {}).get('free', 0)
            
            # Lấy open orders
            open_orders = self.binance.fetch_open_orders()
            
            # Lấy lịch sử trading từ DynamoDB
            recent_trades = self.db.get_recent_trades(limit=10)
            
            account_info = {
                'jpy_balance': jpy_balance,
                'open_orders_count': len(open_orders),
                'open_orders': open_orders,
                'recent_trades': recent_trades,
                'last_updated': datetime.now().isoformat()
            }
            
            # Lưu vào DynamoDB để tracking
            self.db.save_account_snapshot(account_info)
            
            return account_info
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def analyze_market(self) -> Dict:
        """Phân tích thị trường - version tối ưu cho Lambda"""
        try:
            # Lấy danh sách symbols để phân tích
            symbols = self.config['symbols_to_analyze']
            
            recommendations = []
            analysis_summary = {
                'total_symbols': len(symbols),
                'analyzed_count': 0,
                'opportunities_found': 0,
                'analysis_time': datetime.now().isoformat()
            }
            
            for symbol in symbols:
                try:
                    # Giới hạn thời gian phân tích mỗi symbol
                    start_time = time.time()
                    
                    # Lấy dữ liệu nhanh (ít hơn so với EC2 version)
                    df = self.get_market_data(symbol, limit=1000)  # Giảm từ 5000 xuống 1000
                    
                    if df is None or len(df) < 100:
                        continue
                    
                    # Phân tích nhanh
                    analysis = self.quick_technical_analysis(symbol, df)
                    
                    if analysis and analysis.get('signal') == 'BUY':
                        recommendations.append(analysis)
                        analysis_summary['opportunities_found'] += 1
                    
                    analysis_summary['analyzed_count'] += 1
                    
                    # Timeout protection - mỗi symbol tối đa 30 giây
                    if time.time() - start_time > 30:
                        logger.warning(f"Analysis timeout for {symbol}")
                        break
                        
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    continue
            
            # Sắp xếp theo độ ưu tiên
            recommendations = sorted(
                recommendations, 
                key=lambda x: x.get('confidence_score', 0), 
                reverse=True
            )
            
            # Giới hạn số lượng recommendations
            max_recommendations = self.config.get('max_recommendations', 3)
            recommendations = recommendations[:max_recommendations]
            
            result = {
                'recommendations': recommendations,
                'analysis_summary': analysis_summary
            }
            
            # Lưu kết quả phân tích vào DynamoDB
            self.db.save_analysis_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {'recommendations': [], 'error': str(e)}
    
    def get_market_data(self, symbol: str, limit: int = 1000) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu thị trường"""
        try:
            # Sử dụng timeframe lớn hơn để giảm số lượng data points
            timeframe = '5m'  # Thay vì 1m
            
            ohlcv = self.binance.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv:
                return None
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def quick_technical_analysis(self, symbol: str, df: pd.DataFrame) -> Optional[Dict]:
        """Phân tích kỹ thuật nhanh cho Lambda"""
        try:
            if len(df) < 50:
                return None
            
            # Tính toán indicators cơ bản
            df['sma_20'] = df['close'].rolling(20).mean()
            df['sma_50'] = df['close'].rolling(50).mean()
            
            # RSI đơn giản
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Lấy giá trị hiện tại
            current_price = df['close'].iloc[-1]
            sma_20 = df['sma_20'].iloc[-1]
            sma_50 = df['sma_50'].iloc[-1]
            rsi = df['rsi'].iloc[-1]
            
            # Phân tích order book nhanh
            order_book = self.get_order_book_quick(symbol)
            
            # Tính toán entry/exit points
            analysis = self.calculate_entry_exit(
                symbol, current_price, sma_20, sma_50, rsi, order_book
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Quick technical analysis failed for {symbol}: {e}")
            return None
    
    def get_order_book_quick(self, symbol: str) -> Optional[Dict]:
        """Lấy order book nhanh"""
        try:
            order_book = self.binance.fetch_order_book(symbol, limit=10)  # Giảm từ 20 xuống 10
            
            if not order_book or not order_book.get('bids') or not order_book.get('asks'):
                return None
            
            bids = order_book['bids'][:5]  # Chỉ lấy top 5
            asks = order_book['asks'][:5]
            
            best_bid = bids[0][0] if bids else 0
            best_ask = asks[0][0] if asks else 0
            
            spread = (best_ask - best_bid) / best_bid * 100 if best_bid > 0 else 0
            
            return {
                'best_bid': best_bid,
                'best_ask': best_ask,
                'spread': spread,
                'bid_volume': sum(bid[1] for bid in bids),
                'ask_volume': sum(ask[1] for ask in asks)
            }
            
        except Exception as e:
            logger.error(f"Error getting order book for {symbol}: {e}")
            return None
    
    def calculate_entry_exit(self, symbol: str, current_price: float, 
                           sma_20: float, sma_50: float, rsi: float, 
                           order_book: Optional[Dict]) -> Optional[Dict]:
        """Tính toán entry/exit points"""
        try:
            # Simple signal logic
            signal = 'HOLD'
            confidence_score = 0
            
            # Bullish conditions
            bullish_signals = 0
            if current_price > sma_20:
                bullish_signals += 1
            if sma_20 > sma_50:
                bullish_signals += 1
            if rsi < 70 and rsi > 30:  # Không quá mua/quá bán
                bullish_signals += 1
            if order_book and order_book['spread'] < 0.5:  # Spread tốt
                bullish_signals += 1
            
            if bullish_signals >= 3:
                signal = 'BUY'
                confidence_score = bullish_signals * 25  # Max 100
            
            if signal != 'BUY':
                return None
            
            # Tính entry/exit points
            entry_price = current_price
            stop_loss = entry_price * 0.97  # 3% stop loss
            tp1_price = entry_price * 1.02   # 2% take profit 1
            tp2_price = entry_price * 1.05   # 5% take profit 2
            
            return {
                'coin': symbol.replace('/JPY', ''),
                'symbol': symbol,
                'signal': signal,
                'current_price': current_price,
                'optimal_entry': entry_price,
                'stop_loss': stop_loss,
                'tp1_price': tp1_price,
                'tp2_price': tp2_price,
                'confidence_score': confidence_score,
                'analysis_type': 'QUICK_TECHNICAL',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating entry/exit for {symbol}: {e}")
            return None
    
    def execute_trading(self, recommendations: List[Dict]) -> Dict:
        """Thực hiện trading"""
        try:
            if not recommendations:
                return {'message': 'No recommendations to execute'}
            
            # Lấy số dư
            balance = self.binance.fetch_balance()
            jpy_balance = balance.get('JPY', {}).get('free', 0)
            
            if jpy_balance <= 0:
                return {'error': 'Insufficient JPY balance'}
            
            results = []
            total_invested = 0
            
            # Chia đều vốn cho các recommendations
            num_trades = len(recommendations)
            allocation_per_trade = jpy_balance * 0.95 / num_trades  # 95% balance
            
            for i, rec in enumerate(recommendations):
                try:
                    # Tính toán quantity
                    quantity = allocation_per_trade / rec['current_price']
                    
                    # Thực hiện buy order
                    trade_result = self.place_buy_order(
                        rec['symbol'], 
                        quantity, 
                        rec['optimal_entry'],
                        rec['stop_loss'],
                        rec['tp1_price'],
                        rec['tp2_price']
                    )
                    
                    if trade_result['status'] == 'success':
                        total_invested += allocation_per_trade
                        
                        # Lưu trade vào DynamoDB
                        self.db.save_trade_record(trade_result)
                        
                        # Gửi notification
                        self.notifications.send_trade_notification(trade_result)
                    
                    results.append(trade_result)
                    
                except Exception as e:
                    logger.error(f"Error executing trade {i+1}: {e}")
                    results.append({
                        'symbol': rec.get('symbol', 'Unknown'),
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return {
                'total_trades': len(results),
                'successful_trades': len([r for r in results if r.get('status') == 'success']),
                'total_invested': total_invested,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Trading execution failed: {e}")
            return {'error': str(e)}
    
    def place_buy_order(self, symbol: str, quantity: float, entry_price: float,
                       stop_loss: float, tp1_price: float, tp2_price: float) -> Dict:
        """Đặt lệnh mua với SL/TP"""
        try:
            # Validate minimum order value
            min_notional = 1500  # JPY
            order_value = quantity * entry_price
            
            if order_value < min_notional:
                return {
                    'status': 'failed',
                    'error': f'Order value {order_value:.2f} < minimum {min_notional}',
                    'symbol': symbol
                }
            
            # Place market buy order
            buy_order = self.binance.create_market_buy_order(symbol, quantity)
            
            if not buy_order:
                return {
                    'status': 'failed',
                    'error': 'Failed to place buy order',
                    'symbol': symbol
                }
            
            actual_price = float(buy_order.get('average', entry_price))
            actual_quantity = float(buy_order.get('filled', quantity))
            
            # Place stop loss (simplified for Lambda)
            try:
                sl_order = self.binance.create_order(
                    symbol=symbol,
                    type='STOP_LOSS_LIMIT',
                    side='sell',
                    amount=actual_quantity,
                    price=stop_loss * 0.999,  # Slightly below stop price
                    params={
                        'stopPrice': stop_loss,
                        'timeInForce': 'GTC'
                    }
                )
            except Exception as sl_error:
                logger.error(f"Failed to place stop loss: {sl_error}")
                sl_order = None
            
            return {
                'status': 'success',
                'symbol': symbol,
                'buy_order_id': buy_order['id'],
                'sl_order_id': sl_order['id'] if sl_order else None,
                'quantity': actual_quantity,
                'price': actual_price,
                'total_cost': actual_quantity * actual_price,
                'stop_loss': stop_loss,
                'tp1_price': tp1_price,
                'tp2_price': tp2_price,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error placing buy order for {symbol}: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'symbol': symbol
            }
    
    def monitor_orders(self) -> Dict:
        """Monitor active orders"""
        try:
            # Lấy open orders từ Binance
            open_orders = self.binance.fetch_open_orders()
            
            # Lấy active orders từ DynamoDB
            db_orders = self.db.get_active_orders()
            
            results = []
            
            for order in open_orders:
                order_id = order['id']
                symbol = order['symbol']
                status = order['status']
                
                # Cập nhật status trong DynamoDB
                self.db.update_order_status(order_id, status, order)
                
                results.append({
                    'order_id': order_id,
                    'symbol': symbol,
                    'status': status,
                    'side': order['side'],
                    'type': order['type'],
                    'amount': order['amount'],
                    'filled': order['filled']
                })
            
            return {
                'total_orders': len(results),
                'orders': results,
                'last_checked': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Order monitoring failed: {e}")
            return {'error': str(e)}
    
    def activate_emergency_stop(self) -> Dict:
        """Kích hoạt emergency stop"""
        try:
            # Set emergency stop flag trong DynamoDB
            self.db.set_system_status('emergency_stop', True)
            
            # Cancel tất cả open orders
            open_orders = self.binance.fetch_open_orders()
            cancelled_orders = []
            
            for order in open_orders:
                try:
                    cancel_result = self.binance.cancel_order(order['id'], order['symbol'])
                    cancelled_orders.append(order['id'])
                except Exception as e:
                    logger.error(f"Failed to cancel order {order['id']}: {e}")
            
            # Gửi emergency notification
            self.notifications.send_emergency_notification(
                f"Emergency stop activated. Cancelled {len(cancelled_orders)} orders."
            )
            
            return {
                'emergency_stop_activated': True,
                'cancelled_orders': cancelled_orders,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
            return {'error': str(e)}
