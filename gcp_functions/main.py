"""
Google Cloud Functions - Crypto Trading Bot
Tối ưu cho GCP: Tiết kiệm tài nguyên, logic đơn giản, cost-effective
"""

import os
import json
import logging
import time
from datetime import datetime
import functions_framework
from flask import Request

# Core imports - only load when needed
import ccxt
import pandas as pd
import numpy as np

# Technical analysis - lazy import
TA_AVAILABLE = False
try:
    from ta.trend import SMAIndicator, MACD
    from ta.momentum import RSIIndicator
    from ta.volatility import BollingerBands
    TA_AVAILABLE = True
except ImportError:
    pass

# GCP imports
try:
    from google.cloud import firestore
    from google.cloud import logging as gcp_logging
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False

# Local imports
try:
    from notifications import send_trade_notification, send_error_notification, send_simple_notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for connection reuse
_binance_client = None
_firestore_client = None

# Configuration - Environment variables
CONFIG = {
    'binance': {
        'apiKey': os.environ.get('BINANCE_API_KEY'),
        'secret': os.environ.get('BINANCE_SECRET'),
        'sandbox': os.environ.get('BINANCE_SANDBOX', 'True').lower() == 'true',
        'enableRateLimit': True,
        'timeout': 15000,  # 15s timeout for GCP
        'options': {'defaultType': 'spot'}
    },
    'trading': {
        'enabled': os.environ.get('TRADING_ENABLED', 'False').lower() == 'true',
        'symbols': ['ADA/JPY', 'XRP/JPY', 'XLM/JPY', 'SUI/JPY'],  # Giới hạn 4 symbols
        'max_trades': 2,  # 2 trades để cân bằng accuracy và cost
        'allocation_percentage': 0.5,  # 50% balance
        'stop_loss_percent': 3.0,
        'take_profit_percent': 2.0,
        'min_order_value_jpy': 1000,
        'max_execution_time': 540  # 9 minutes (GCP timeout 10 min)
    },
    'firestore': {
        'project_id': os.environ.get('GCP_PROJECT_ID'),
        'collection': 'crypto_trading'
    }
}

def get_binance_client():
    """Get cached Binance client"""
    global _binance_client
    if _binance_client is None:
        _binance_client = ccxt.binance(CONFIG['binance'])
        logger.info("✅ Binance client initialized")
    return _binance_client

def get_firestore_client():
    """Get cached Firestore client"""
    global _firestore_client
    if _firestore_client is None and FIRESTORE_AVAILABLE:
        _firestore_client = firestore.Client(project=CONFIG['firestore']['project_id'])
        logger.info("✅ Firestore client initialized")
    return _firestore_client

def save_to_firestore(collection, document_id, data):
    """Save data to Firestore"""
    try:
        if not FIRESTORE_AVAILABLE:
            logger.warning("Firestore not available, skipping save")
            return False
        
        db = get_firestore_client()
        if db:
            db.collection(collection).document(document_id).set(data)
            return True
    except Exception as e:
        logger.error(f"Error saving to Firestore: {e}")
    return False

def get_account_balance():
    """Get JPY balance - optimized"""
    try:
        binance = get_binance_client()
        balance = binance.fetch_balance()
        jpy_balance = float(balance.get('JPY', {}).get('free', 0))
        
        # Save snapshot
        save_to_firestore('account_snapshots', 
                         f"snapshot_{int(time.time())}", 
                         {'balance': jpy_balance, 'timestamp': datetime.now().isoformat()})
        
        return jpy_balance
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        return 0

def analyze_symbol_fast(symbol):
    """Fast symbol analysis - simplified for cost optimization"""
    try:
        start_time = time.time()
        binance = get_binance_client()
        
        # Get data with more candles for better accuracy - 1000 candles
        ohlcv = binance.fetch_ohlcv(symbol, '1h', limit=1000)
        if not ohlcv or len(ohlcv) < 200:  # Need more data for accuracy
            return None
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['close'] = pd.to_numeric(df['close'])
        
        current_price = df['close'].iloc[-1]
        
        # Simple analysis - only essential indicators
        analysis = {'symbol': symbol, 'price': current_price, 'signals': {}}
        
        if TA_AVAILABLE:
            # More comprehensive analysis for better accuracy
            rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
            analysis['rsi'] = rsi
            analysis['signals']['rsi_oversold'] = rsi < 30
            analysis['signals']['rsi_overbought'] = rsi > 70
            
            # Multiple moving averages for better trend detection
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            sma_50 = df['close'].rolling(50).mean().iloc[-1]
            analysis['signals']['price_above_sma20'] = current_price > sma_20
            analysis['signals']['price_above_sma50'] = current_price > sma_50
            analysis['signals']['sma_bullish'] = sma_20 > sma_50
            
            # MACD for trend confirmation
            macd_line = MACD(df['close']).macd().iloc[-1]
            macd_signal = MACD(df['close']).macd_signal().iloc[-1]
            analysis['signals']['macd_bullish'] = macd_line > macd_signal
            
            # Bollinger Bands for volatility
            bb = BollingerBands(df['close'])
            bb_lower = bb.bollinger_lband().iloc[-1]
            bb_upper = bb.bollinger_hband().iloc[-1]
            analysis['signals']['bb_oversold'] = current_price < bb_lower
            analysis['signals']['bb_overbought'] = current_price > bb_upper
        
        # Enhanced scoring for better accuracy
        buy_score = 0
        if analysis['signals'].get('rsi_oversold'): buy_score += 3
        if analysis['signals'].get('price_above_sma20'): buy_score += 2
        if analysis['signals'].get('price_above_sma50'): buy_score += 2
        if analysis['signals'].get('sma_bullish'): buy_score += 2
        if analysis['signals'].get('macd_bullish'): buy_score += 2
        if analysis['signals'].get('bb_oversold'): buy_score += 3
        
        # Penalty for overbought conditions
        if analysis['signals'].get('rsi_overbought'): buy_score -= 3
        if analysis['signals'].get('bb_overbought'): buy_score -= 2
        
        analysis['buy_score'] = max(0, buy_score)  # Don't go negative
        analysis['recommendation'] = 'BUY' if buy_score >= 5 else 'HOLD'  # Higher threshold
        analysis['confidence'] = min(buy_score / 10.0, 1.0)  # Confidence score
        analysis['analysis_time'] = time.time() - start_time
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return None

def place_simple_buy_order(symbol, jpy_amount):
    """Place simple buy order - no complex SL/TP"""
    try:
        binance = get_binance_client()
        
        # Get current price
        ticker = binance.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # Calculate quantity
        quantity = jpy_amount / current_price
        quantity = float(f"{quantity:.6f}")  # Round to 6 decimals
        
        # Place market buy
        order = binance.create_market_buy_order(symbol, quantity)
        
        if order['status'] == 'closed':
            # Save to Firestore
            order_data = {
                'symbol': symbol,
                'type': 'BUY',
                'quantity': quantity,
                'price': order.get('average', current_price),
                'value_jpy': jpy_amount,
                'timestamp': datetime.now().isoformat(),
                'order_id': order['id']
            }
            save_to_firestore('trades', f"trade_{order['id']}", order_data)
            
            # Send notification
            if NOTIFICATIONS_AVAILABLE:
                send_trade_notification(order_data)
            
            logger.info(f"✅ Buy order placed: {symbol} - {quantity} @ {current_price}")
            return order_data
        
    except Exception as e:
        logger.error(f"Error placing buy order {symbol}: {e}")
        return None

def execute_trading_strategy(recommendations, balance):
    """Execute simple trading strategy"""
    if not CONFIG['trading']['enabled']:
        return {'message': 'Trading disabled', 'trades': []}
    
    if balance < CONFIG['trading']['min_order_value_jpy']:
        return {'message': 'Insufficient balance', 'trades': []}
    
    executed_trades = []
    
    # Trade up to 2 symbols for better diversification
    trade_count = 0
    for recommendation in recommendations:
        if trade_count >= CONFIG['trading']['max_trades']:
            break
            
        if recommendation['recommendation'] == 'BUY' and recommendation.get('confidence', 0) >= 0.5:
            # Use balanced allocation between trades
            trade_amount = (balance * CONFIG['trading']['allocation_percentage']) / CONFIG['trading']['max_trades']
            
            result = place_simple_buy_order(recommendation['symbol'], trade_amount)
            if result:
                executed_trades.append(result)
                trade_count += 1
    
    return {'message': f'Executed {len(executed_trades)} trades', 'trades': executed_trades}

@functions_framework.http
def crypto_trading_main(request: Request):
    """Main Cloud Function entry point"""
    start_time = time.time()
    
    try:
        # Parse request
        request_json = request.get_json(silent=True)
        action = request_json.get('action', 'analyze_and_trade') if request_json else 'analyze_and_trade'
        
        logger.info(f"Function triggered: {action}")
        
        # Check execution time limit
        if time.time() - start_time > CONFIG['trading']['max_execution_time']:
            return {'error': 'Execution timeout'}, 408
        
        # Route actions
        if action == 'get_balance':
            balance = get_account_balance()
            return {'balance': balance, 'currency': 'JPY'}
        
        elif action == 'analyze_only':
            # Analyze symbols
            recommendations = []
            for symbol in CONFIG['trading']['symbols']:
                if time.time() - start_time > CONFIG['trading']['max_execution_time']:
                    break
                
                analysis = analyze_symbol_fast(symbol)
                if analysis:
                    recommendations.append(analysis)
                    # Save analysis
                    save_to_firestore('analysis', 
                                     f"{symbol.replace('/', '_')}_{int(time.time())}", 
                                     analysis)
            
            return {
                'recommendations': recommendations,
                'execution_time': time.time() - start_time
            }
        
        elif action == 'analyze_and_trade':
            # Get balance
            balance = get_account_balance()
            
            # Analyze symbols
            recommendations = []
            for symbol in CONFIG['trading']['symbols']:
                if time.time() - start_time > CONFIG['trading']['max_execution_time']:
                    break
                
                analysis = analyze_symbol_fast(symbol)
                if analysis and analysis['recommendation'] == 'BUY':
                    recommendations.append(analysis)
            
            # Execute trades
            trading_result = execute_trading_strategy(recommendations, balance)
            
            result = {
                'balance': balance,
                'recommendations': len(recommendations),
                'trading_result': trading_result,
                'execution_time': time.time() - start_time
            }
            
            # Save execution log
            save_to_firestore('execution_logs', 
                             f"execution_{int(time.time())}", 
                             result)
            
            # Send summary notification if trades executed
            if NOTIFICATIONS_AVAILABLE and trading_result.get('trades'):
                send_simple_notification(
                    "Trading Session Complete", 
                    f"Executed {len(trading_result['trades'])} trades in {result['execution_time']:.1f}s"
                )
            
            return result
        
        else:
            return {'error': f'Unknown action: {action}'}, 400
    
    except Exception as e:
        logger.error(f"Function execution error: {e}")
        
        # Send error notification
        if NOTIFICATIONS_AVAILABLE:
            send_error_notification(f"Function execution failed: {str(e)}")
        
        return {'error': str(e)}, 500

# For local testing
if __name__ == '__main__':
    from flask import Flask, request
    app = Flask(__name__)
    
    @app.route('/', methods=['POST', 'GET'])
    def local_test():
        return crypto_trading_main(request)
    
    app.run(debug=True, port=8080)
