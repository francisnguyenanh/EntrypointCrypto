"""
AWS Lambda Trading Core - Complete Trading Bot Implementation
Based on app.py functionality, optimized for serverless execution
Handles: Market Analysis, Order Placement, Risk Management, Notifications
"""

import json
import logging
import os
import sys
import time
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Core libraries
import ccxt
import pandas as pd
import numpy as np

# Technical analysis
try:
    from ta.trend import SMAIndicator, MACD, EMAIndicator
    from ta.momentum import RSIIndicator, StochasticOscillator
    from ta.volatility import BollingerBands
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False

# AWS services (will be imported conditionally)
try:
    import boto3
    from boto3.dynamodb.conditions import Key
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

# Suppress warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lambda configuration
LAMBDA_CONFIG = {
    'enabled': True,
    'emergency_stop': False,
    'symbols_to_analyze': ['ADA/JPY', 'XRP/JPY', 'XLM/JPY', 'SUI/JPY'],
    'max_analysis_time': 45,  # seconds (Lambda timeout buffer)
    'max_trades_per_execution': 3,
    'auto_trading_enabled': True,
    'risk_management': {
        'max_risk_per_trade': 0.02,  # 2%
        'max_total_risk': 0.10,      # 10%
        'stop_loss_percent': 0.02,   # 2%
        'take_profit_1': 0.03,       # 3%
        'take_profit_2': 0.05,       # 5%
        'min_confidence_score': 60   # Minimum confidence for trade
    },
    'notifications': {
        'sns_topic_arn': os.environ.get('SNS_TOPIC_ARN'),
        'email_enabled': True,
        'urgent_only': False
    }
}

# Binance configuration for Lambda
BINANCE_CONFIG = {
    'apiKey': os.environ.get('BINANCE_API_KEY'),
    'secret': os.environ.get('BINANCE_SECRET_KEY'),
    'sandbox': os.environ.get('BINANCE_TESTNET', 'true').lower() == 'true',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot'
    }
}

class LambdaTradingCore:
    """Complete Lambda Trading Core - Serverless Trading Bot"""
    
    def __init__(self):
        """Initialize Lambda Trading Core"""
        try:
            # Initialize Binance API
            self.binance = ccxt.binance(BINANCE_CONFIG)
            logger.info("✅ Binance API initialized")
            
            # Initialize AWS services if available
            if AWS_AVAILABLE:
                self.dynamodb = boto3.resource('dynamodb')
                self.sns = boto3.client('sns')
                logger.info("✅ AWS services initialized")
            else:
                self.dynamodb = None
                self.sns = None
                logger.warning("⚠️ AWS services not available - using in-memory storage")
            
            self.config = LAMBDA_CONFIG
            self.start_time = time.time()
            self.active_orders = {}  # In-memory order tracking for Lambda
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Lambda Trading Core: {e}")
            raise
    
    def get_account_balance(self) -> float:
        """Get JPY account balance"""
        try:
            balance = self.binance.fetch_balance()
            jpy_balance = balance.get('JPY', {}).get('free', 0)
            logger.info(f"💰 Current JPY balance: ¥{jpy_balance:,.2f}")
            return jpy_balance
        except Exception as e:
            logger.error(f"❌ Error getting balance: {e}")
            return 0
    
    def get_account_info(self) -> Dict:
        """Get comprehensive account information"""
        try:
            balance = self.binance.fetch_balance()
            
            # Get JPY balance
            jpy_balance = balance.get('JPY', {}).get('free', 0)
            
            # Get open orders
            open_orders = []
            try:
                self.binance.options["warnOnFetchOpenOrdersWithoutSymbol"] = False
                open_orders = self.binance.fetch_open_orders()
            except Exception as e:
                logger.warning(f"Could not fetch open orders: {e}")
            
            # Get positions (if any)
            positions = []
            for currency, info in balance.items():
                if info['total'] > 0 and currency != 'JPY':
                    positions.append({
                        'currency': currency,
                        'total': info['total'],
                        'free': info['free'],
                        'used': info['used']
                    })
            
            account_info = {
                'jpy_balance': jpy_balance,
                'open_orders_count': len(open_orders),
                'open_orders': [
                    {
                        'id': order['id'],
                        'symbol': order['symbol'],
                        'type': order['type'],
                        'side': order['side'],
                        'amount': order['amount'],
                        'price': order['price'],
                        'status': order['status']
                    } for order in open_orders
                ],
                'positions': positions,
                'total_positions': len(positions),
                'last_updated': datetime.now().isoformat()
            }
            
            return account_info
            
        except Exception as e:
            logger.error(f"❌ Error getting account info: {e}")
            return {'error': str(e)}
    
    def get_crypto_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[pd.DataFrame]:
        """Get cryptocurrency price data"""
        try:
            ohlcv = self.binance.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"❌ Error getting data for {symbol}: {e}")
            return None
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """Get order book data"""
        try:
            order_book = self.binance.fetch_order_book(symbol, limit=limit)
            return order_book
        except Exception as e:
            logger.error(f"❌ Error getting order book for {symbol}: {e}")
            return None
    
    def analyze_order_book(self, order_book: Dict) -> Optional[Dict]:
        """Analyze order book for liquidity and spread"""
        if not order_book or not order_book.get('bids') or not order_book.get('asks'):
            return None
        
        bids = order_book['bids']
        asks = order_book['asks']
        
        # Best bid and ask
        best_bid = bids[0][0] if bids else 0
        best_ask = asks[0][0] if asks else 0
        
        if best_bid == 0 or best_ask == 0:
            return None
        
        # Calculate spread
        spread = (best_ask - best_bid) / best_bid * 100
        
        # Calculate volumes
        total_bid_volume = sum(bid[1] for bid in bids[:10])
        total_ask_volume = sum(ask[1] for ask in asks[:10])
        
        # Bid/Ask ratio
        bid_ask_ratio = total_bid_volume / total_ask_volume if total_ask_volume > 0 else 0
        
        # Available liquidity within reasonable price range (±2%)
        price_range_buy = best_ask * 1.02
        price_range_sell = best_bid * 0.98
        
        available_liquidity_buy = sum(ask[1] for ask in asks if ask[0] <= price_range_buy)
        available_liquidity_sell = sum(bid[1] for bid in bids if bid[0] >= price_range_sell)
        
        return {
            'best_bid': best_bid,
            'best_ask': best_ask,
            'spread': spread,
            'bid_ask_ratio': bid_ask_ratio,
            'total_bid_volume': total_bid_volume,
            'total_ask_volume': total_ask_volume,
            'available_liquidity_buy': available_liquidity_buy,
            'available_liquidity_sell': available_liquidity_sell
        }
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators"""
        if not TA_AVAILABLE or df is None or len(df) < 20:
            return {'error': 'Insufficient data or TA library not available'}
        
        try:
            indicators = {}
            
            # Moving averages
            sma_20 = SMAIndicator(close=df['close'], window=20)
            sma_50 = SMAIndicator(close=df['close'], window=50)
            indicators['sma_20'] = sma_20.sma_indicator().iloc[-1]
            indicators['sma_50'] = sma_50.sma_indicator().iloc[-1]
            
            # RSI
            rsi = RSIIndicator(close=df['close'], window=14)
            indicators['rsi'] = rsi.rsi().iloc[-1]
            
            # MACD
            macd_indicator = MACD(close=df['close'])
            indicators['macd'] = macd_indicator.macd().iloc[-1]
            indicators['macd_signal'] = macd_indicator.macd_signal().iloc[-1]
            indicators['macd_histogram'] = macd_indicator.macd_diff().iloc[-1]
            
            # Bollinger Bands
            bb = BollingerBands(close=df['close'], window=20)
            indicators['bb_upper'] = bb.bollinger_hband().iloc[-1]
            indicators['bb_middle'] = bb.bollinger_mavg().iloc[-1]
            indicators['bb_lower'] = bb.bollinger_lband().iloc[-1]
            
            # Current price position
            current_price = df['close'].iloc[-1]
            indicators['current_price'] = current_price
            
            # Generate signals
            signals = []
            confidence = 0
            
            # RSI signals
            if indicators['rsi'] < 30:
                signals.append("RSI_OVERSOLD")
                confidence += 20
            elif indicators['rsi'] > 70:
                signals.append("RSI_OVERBOUGHT")
                confidence -= 20
            
            # MACD signals
            if indicators['macd'] > indicators['macd_signal'] and indicators['macd_histogram'] > 0:
                signals.append("MACD_BULLISH")
                confidence += 15
            elif indicators['macd'] < indicators['macd_signal'] and indicators['macd_histogram'] < 0:
                signals.append("MACD_BEARISH")
                confidence -= 15
            
            # Moving average signals
            if current_price > indicators['sma_20'] > indicators['sma_50']:
                signals.append("MA_UPTREND")
                confidence += 10
            elif current_price < indicators['sma_20'] < indicators['sma_50']:
                signals.append("MA_DOWNTREND")
                confidence -= 10
            
            # Bollinger Bands signals
            if current_price <= indicators['bb_lower']:
                signals.append("BB_OVERSOLD")
                confidence += 15
            elif current_price >= indicators['bb_upper']:
                signals.append("BB_OVERBOUGHT")
                confidence -= 15
            
            indicators['signals'] = signals
            indicators['confidence_score'] = max(0, min(100, confidence + 50))  # Normalize to 0-100
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Error calculating technical indicators: {e}")
            return {'error': str(e)}
    
    def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """Analyze a single symbol for trading opportunities"""
        try:
            logger.info(f"📊 Analyzing {symbol}")
            
            # Get price data
            df = self.get_crypto_data(symbol, timeframe='1h', limit=100)
            if df is None or len(df) < 20:
                logger.warning(f"❌ Insufficient data for {symbol}")
                return None
            
            # Get current price
            current_price = df['close'].iloc[-1]
            
            # Get order book
            order_book = self.get_order_book(symbol)
            order_book_analysis = self.analyze_order_book(order_book)
            
            # Calculate technical indicators
            tech_indicators = self.calculate_technical_indicators(df)
            
            if 'error' in tech_indicators:
                logger.warning(f"❌ Technical analysis failed for {symbol}: {tech_indicators['error']}")
                return None
            
            # Generate trading recommendation
            confidence_score = tech_indicators.get('confidence_score', 0)
            signals = tech_indicators.get('signals', [])
            
            # Calculate entry, stop loss, and take profit levels
            entry_price = current_price
            stop_loss = entry_price * (1 - self.config['risk_management']['stop_loss_percent'])
            tp1_price = entry_price * (1 + self.config['risk_management']['take_profit_1'])
            tp2_price = entry_price * (1 + self.config['risk_management']['take_profit_2'])
            
            # Risk/Reward calculation
            risk_percent = self.config['risk_management']['stop_loss_percent'] * 100
            reward_percent = self.config['risk_management']['take_profit_1'] * 100
            risk_reward_ratio = reward_percent / risk_percent if risk_percent > 0 else 0
            
            # Add order book factors to confidence
            if order_book_analysis:
                if order_book_analysis['spread'] < 0.1:  # Low spread is good
                    confidence_score += 5
                if order_book_analysis['bid_ask_ratio'] > 1.2:  # More buying pressure
                    confidence_score += 10
                elif order_book_analysis['bid_ask_ratio'] < 0.8:  # More selling pressure
                    confidence_score -= 10
            
            # Ensure confidence is within bounds
            confidence_score = max(0, min(100, confidence_score))
            
            analysis = {
                'coin': symbol.replace('/JPY', ''),
                'symbol': symbol,
                'current_price': current_price,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'tp1_price': tp1_price,
                'tp2_price': tp2_price,
                'risk_percent': risk_percent,
                'reward_percent': reward_percent,
                'risk_reward_ratio': risk_reward_ratio,
                'confidence_score': confidence_score,
                'signals': signals,
                'technical_indicators': tech_indicators,
                'order_book_analysis': order_book_analysis,
                'spread': order_book_analysis['spread'] if order_book_analysis else 999,
                'total_volume': (order_book_analysis['total_bid_volume'] + order_book_analysis['total_ask_volume']) if order_book_analysis else 0,
                'analysis_time': datetime.now().isoformat()
            }
            
            logger.info(f"✅ {symbol} analysis complete - Confidence: {confidence_score}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing {symbol}: {e}")
            return None
    
    def get_trading_recommendations(self) -> List[Dict]:
        """Get trading recommendations for all configured symbols"""
        try:
            logger.info("🔍 Starting market analysis...")
            
            recommendations = []
            min_confidence = self.config['risk_management']['min_confidence_score']
            
            for symbol in self.config['symbols_to_analyze']:
                # Check execution time
                if time.time() - self.start_time > self.config['max_analysis_time']:
                    logger.warning("⏰ Analysis time limit reached")
                    break
                
                analysis = self.analyze_symbol(symbol)
                if analysis and analysis['confidence_score'] >= min_confidence:
                    recommendations.append(analysis)
                    logger.info(f"✅ {symbol} added to recommendations (confidence: {analysis['confidence_score']})")
            
            # Sort by confidence score
            recommendations.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            logger.info(f"📈 Found {len(recommendations)} trading opportunities")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error getting recommendations: {e}")
            return []
    
    def validate_balance_for_order(self, symbol: str, quantity: float, price: float) -> Dict:
        """Validate if balance is sufficient for order"""
        try:
            current_balance = self.get_account_balance()
            order_value = quantity * price
            required_balance = order_value * 1.01  # Add 1% buffer for fees
            
            return {
                'valid': current_balance >= required_balance,
                'current_balance': current_balance,
                'required': required_balance,
                'order_value': order_value,
                'shortage': max(0, required_balance - current_balance)
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def calculate_position_size(self, balance: float, num_trades: int, price: float) -> float:
        """Calculate position size based on available balance"""
        try:
            # Reserve 5% as buffer
            usable_balance = balance * 0.95
            
            # Divide equally among trades
            balance_per_trade = usable_balance / max(1, num_trades)
            
            # Calculate quantity
            quantity = balance_per_trade / price
            
            return quantity
        except Exception as e:
            logger.error(f"❌ Error calculating position size: {e}")
            return 0
    
    def place_buy_order(self, recommendation: Dict) -> Dict:
        """Place buy order with stop loss and take profit"""
        try:
            symbol = recommendation['symbol']
            entry_price = recommendation['current_price']
            stop_loss = recommendation['stop_loss']
            tp1_price = recommendation['tp1_price']
            tp2_price = recommendation['tp2_price']
            
            logger.info(f"🔄 Placing buy order for {symbol}")
            
            # Get current balance
            balance = self.get_account_balance()
            if balance <= 0:
                return {'status': 'failed', 'error': 'Insufficient balance'}
            
            # Calculate position size (assuming 1 trade for simplicity)
            quantity = self.calculate_position_size(balance, 1, entry_price)
            
            # Validate balance
            balance_check = self.validate_balance_for_order(symbol, quantity, entry_price)
            if not balance_check['valid']:
                return {
                    'status': 'failed', 
                    'error': 'insufficient_balance',
                    'details': balance_check
                }
            
            logger.info(f"📊 Order details: {quantity:.6f} @ ¥{entry_price:.4f}")
            
            # Place market buy order
            buy_order = self.binance.create_market_buy_order(symbol, quantity)
            
            actual_price = float(buy_order['average']) if buy_order['average'] else entry_price
            actual_quantity = float(buy_order['filled'])
            
            logger.info(f"✅ Buy order successful - ID: {buy_order['id']}")
            
            # Place stop loss order
            try:
                stop_order = self.binance.create_order(
                    symbol=symbol,
                    type='STOP_LOSS_LIMIT',
                    side='sell',
                    amount=actual_quantity,
                    price=stop_loss * 0.999,  # Slight buffer
                    params={
                        'stopPrice': stop_loss,
                        'timeInForce': 'GTC'
                    }
                )
                logger.info(f"✅ Stop loss placed: ¥{stop_loss:.4f}")
            except Exception as sl_error:
                logger.error(f"❌ Failed to place stop loss: {sl_error}")
                stop_order = None
            
            # Place take profit orders
            tp_orders = []
            try:
                # TP1 - 70% of position
                tp1_quantity = actual_quantity * 0.7
                tp1_order = self.binance.create_limit_sell_order(symbol, tp1_quantity, tp1_price)
                tp_orders.append(tp1_order)
                logger.info(f"✅ Take profit 1 placed: ¥{tp1_price:.4f}")
                
                # TP2 - 30% of position
                tp2_quantity = actual_quantity * 0.3
                tp2_order = self.binance.create_limit_sell_order(symbol, tp2_quantity, tp2_price)
                tp_orders.append(tp2_order)
                logger.info(f"✅ Take profit 2 placed: ¥{tp2_price:.4f}")
                
            except Exception as tp_error:
                logger.error(f"❌ Failed to place take profit orders: {tp_error}")
            
            # Track orders (in Lambda, we'd save to DynamoDB)
            order_info = {
                'symbol': symbol,
                'buy_order_id': buy_order['id'],
                'stop_loss_order_id': stop_order['id'] if stop_order else None,
                'tp_orders': [order['id'] for order in tp_orders],
                'actual_price': actual_price,
                'actual_quantity': actual_quantity,
                'timestamp': datetime.now().isoformat()
            }
            
            self.active_orders[buy_order['id']] = order_info
            
            return {
                'status': 'success',
                'buy_order': buy_order,
                'stop_loss_order': stop_order,
                'tp_orders': tp_orders,
                'order_info': order_info
            }
            
        except Exception as e:
            logger.error(f"❌ Error placing buy order for {symbol}: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def execute_trading_strategy(self, recommendations: List[Dict]) -> Dict:
        """Execute trading strategy based on recommendations"""
        try:
            if not recommendations:
                return {
                    'status': 'no_opportunities',
                    'message': 'No trading opportunities found',
                    'trades_executed': 0
                }
            
            logger.info(f"🚀 Executing trading strategy for {len(recommendations)} opportunities")
            
            max_trades = self.config['max_trades_per_execution']
            selected_recommendations = recommendations[:max_trades]
            
            execution_results = []
            successful_trades = 0
            
            for i, recommendation in enumerate(selected_recommendations):
                logger.info(f"📈 Executing trade {i+1}/{len(selected_recommendations)}")
                
                result = self.place_buy_order(recommendation)
                execution_results.append({
                    'symbol': recommendation['symbol'],
                    'confidence': recommendation['confidence_score'],
                    'result': result
                })
                
                if result['status'] == 'success':
                    successful_trades += 1
                    logger.info(f"✅ Trade {i+1} successful")
                else:
                    logger.error(f"❌ Trade {i+1} failed: {result.get('error', 'Unknown error')}")
            
            # Get final balance
            final_balance = self.get_account_balance()
            
            strategy_result = {
                'status': 'completed',
                'total_opportunities': len(recommendations),
                'trades_attempted': len(selected_recommendations),
                'trades_successful': successful_trades,
                'trades_failed': len(selected_recommendations) - successful_trades,
                'final_balance': final_balance,
                'execution_results': execution_results,
                'active_orders_count': len(self.active_orders),
                'execution_time': time.time() - self.start_time
            }
            
            logger.info(f"📊 Trading strategy completed: {successful_trades}/{len(selected_recommendations)} successful")
            return strategy_result
            
        except Exception as e:
            logger.error(f"❌ Error executing trading strategy: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'trades_executed': 0
            }
    
    def send_notification(self, message: str, urgent: bool = False) -> bool:
        """Send notification via SNS"""
        try:
            if not self.sns or not self.config['notifications']['sns_topic_arn']:
                logger.info(f"📱 NOTIFICATION: {message}")
                return True
            
            subject = "🚨 URGENT TRADING ALERT" if urgent else "📈 Trading Notification"
            
            response = self.sns.publish(
                TopicArn=self.config['notifications']['sns_topic_arn'],
                Subject=subject,
                Message=message
            )
            
            logger.info(f"📧 Notification sent: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")
            return False

def emergency_debug_response():
    """Emergency debug function to check layer mounting and imports"""
    import sys
    
    debug_info = {
        'python_version': sys.version,
        'python_executable': sys.executable,
        'python_paths': sys.path[:10]  # Limit paths shown
    }
    
    # Check if layers are mounted
    layer_info = {
        'opt_python_exists': os.path.exists('/opt/python'),
        'opt_python_files': []
    }
    
    if layer_info['opt_python_exists']:
        try:
            layer_info['opt_python_files'] = os.listdir('/opt/python')[:10]
        except:
            layer_info['opt_python_files'] = ['Error reading directory']
    
    # Check site-packages directory
    site_packages_path = '/opt/python/lib/python3.9/site-packages'
    layer_info['site_packages_exists'] = os.path.exists(site_packages_path)
    if layer_info['site_packages_exists']:
        try:
            site_packages_files = os.listdir(site_packages_path)
            layer_info['site_packages_count'] = len(site_packages_files)
            layer_info['site_packages_files'] = [f for f in site_packages_files if 'ccxt' in f.lower()][:5]
        except:
            layer_info['site_packages_files'] = ['Error reading site-packages']
    
    # Test imports
    import_results = {}
    
    # Test CCXT
    try:
        import ccxt
        import_results['ccxt'] = {
            'status': '✅ SUCCESS',
            'version': ccxt.__version__,
            'exchanges_count': len(ccxt.exchanges)
        }
    except Exception as e:
        import_results['ccxt'] = {
            'status': '❌ FAILED',
            'error': str(e)
        }
    
    # Test pandas/numpy
    try:
        import pandas as pd
        import numpy as np
        import_results['data_analysis'] = {
            'status': '✅ SUCCESS',
            'pandas_version': pd.__version__,
            'numpy_version': np.__version__
        }
    except Exception as e:
        import_results['data_analysis'] = {
            'status': '❌ FAILED',
            'error': str(e)
        }
    
    # Test technical analysis
    try:
        from ta.trend import SMAIndicator
        import_results['technical_analysis'] = {
            'status': '✅ SUCCESS',
            'ta_available': True
        }
    except Exception as e:
        import_results['technical_analysis'] = {
            'status': '❌ FAILED',
            'error': str(e)
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'timestamp': datetime.now().isoformat(),
            'debug_info': debug_info,
            'layer_info': layer_info,
            'import_results': import_results
        }, indent=2)
    }

def lambda_handler(event, context):
    """Main Lambda handler - Complete trading bot functionality"""
    try:
        logger.info(f"🚀 Lambda Trading Bot started. Request ID: {context.aws_request_id}")
        logger.info(f"📥 Event: {event}")
        
        # Check for emergency debug mode
        if event.get('emergency_debug'):
            return emergency_debug_response()
        
        # Initialize trading core
        trading_bot = LambdaTradingCore()
        
        # Handle different event types
        event_type = event.get('action', 'analyze_and_trade')
        
        if event_type == 'get_account_info':
            # Just return account information
            account_info = trading_bot.get_account_info()
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': 'get_account_info',
                    'account_info': account_info,
                    'timestamp': datetime.now().isoformat()
                })
            }
        
        elif event_type == 'analyze_market':
            # Just analyze market, don't trade
            recommendations = trading_bot.get_trading_recommendations()
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': 'analyze_market',
                    'recommendations_count': len(recommendations),
                    'recommendations': recommendations,
                    'timestamp': datetime.now().isoformat()
                })
            }
        
        elif event_type == 'analyze_and_trade':
            # Full trading workflow
            logger.info("🤖 Starting full trading workflow...")
            
            # Check if emergency stop is enabled
            if trading_bot.config['emergency_stop']:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'emergency_stop',
                        'message': 'Emergency stop is enabled - trading disabled'
                    })
                }
            
            # Check if trading is enabled
            if not trading_bot.config['enabled'] or not trading_bot.config['auto_trading_enabled']:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'trading_disabled',
                        'message': 'Auto trading is disabled in configuration'
                    })
                }
            
            # Get account info first
            account_info = trading_bot.get_account_info()
            
            # Get trading recommendations
            recommendations = trading_bot.get_trading_recommendations()
            
            if not recommendations:
                result = {
                    'status': 'no_opportunities',
                    'message': 'No trading opportunities found',
                    'account_info': account_info,
                    'analysis_time': time.time() - trading_bot.start_time
                }
                
                # Send notification
                trading_bot.send_notification(
                    f"💡 Lambda Trading Bot - No opportunities found\n"
                    f"📊 Balance: ¥{account_info.get('jpy_balance', 0):,.2f}\n"
                    f"⏱️ Analysis time: {result['analysis_time']:.2f}s"
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(result)
                }
            
            # Execute trading strategy
            execution_result = trading_bot.execute_trading_strategy(recommendations)
            
            # Prepare final response
            final_result = {
                'status': execution_result['status'],
                'account_info': account_info,
                'recommendations_found': len(recommendations),
                'trades_attempted': execution_result.get('trades_attempted', 0),
                'trades_successful': execution_result.get('trades_successful', 0),
                'trades_failed': execution_result.get('trades_failed', 0),
                'final_balance': execution_result.get('final_balance', 0),
                'active_orders': execution_result.get('active_orders_count', 0),
                'execution_time': execution_result.get('execution_time', 0),
                'execution_details': execution_result.get('execution_results', []),
                'timestamp': datetime.now().isoformat()
            }
            
            # Send comprehensive notification
            notification_msg = (
                f"🤖 Lambda Trading Bot Execution Complete\n\n"
                f"📊 Results:\n"
                f"• Opportunities found: {final_result['recommendations_found']}\n"
                f"• Trades attempted: {final_result['trades_attempted']}\n"
                f"• Successful: {final_result['trades_successful']}\n"
                f"• Failed: {final_result['trades_failed']}\n"
                f"• Active orders: {final_result['active_orders']}\n"
                f"• Final balance: ¥{final_result['final_balance']:,.2f}\n"
                f"• Execution time: {final_result['execution_time']:.2f}s\n\n"
                f"⏰ {final_result['timestamp']}"
            )
            
            urgent = final_result['trades_failed'] > 0 or final_result['trades_successful'] > 0
            trading_bot.send_notification(notification_msg, urgent=urgent)
            
            return {
                'statusCode': 200,
                'body': json.dumps(final_result)
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid action',
                    'supported_actions': ['get_account_info', 'analyze_market', 'analyze_and_trade', 'emergency_debug']
                })
            }
        
    except Exception as e:
        logger.error(f"❌ Lambda execution failed: {e}")
        
        # Try to send error notification
        try:
            if 'trading_bot' in locals():
                trading_bot.send_notification(
                    f"🚨 Lambda Trading Bot Error\n\n"
                    f"❌ Error: {str(e)}\n"
                    f"⏰ Time: {datetime.now().isoformat()}\n"
                    f"🔍 Request ID: {context.aws_request_id}",
                    urgent=True
                )
        except:
            pass
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Lambda execution failed',
                'details': str(e),
                'request_id': context.aws_request_id,
                'timestamp': datetime.now().isoformat()
            })
        }
