#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from binance.client import Client
import trading_config
import pandas as pd
import time

def get_jpy_pairs():
    """Lấy danh sách cặp USDT có sẵn"""
    try:
        client = Client(
            api_key=trading_config.BINANCE_CONFIG['api_key'],
            api_secret=trading_config.BINANCE_CONFIG['api_secret'],
            testnet=trading_config.BINANCE_CONFIG['testnet']
        )
        
        exchange_info = client.get_exchange_info()
        symbols = [s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING']
        
        popular_coins = ['BTC', 'ETH', 'ADA', 'XRP', 'XLM', 'DOT', 'LINK', 'UNI', 'SOL', 'MATIC']
        available_pairs = []
        
        for coin in popular_coins:
            usdt_symbol = f'{coin}USDT'
            if usdt_symbol in symbols:
                pair_format = f'{coin}/JPY'  # Format tương thích
                available_pairs.append(pair_format)
                if len(available_pairs) >= 5:  # Giới hạn 5 cặp để test
                    break
        
        print(f"📊 Found {len(available_pairs)} pairs: {available_pairs}")
        return available_pairs
        
    except Exception as e:
        print(f"⚠️ Error getting pairs: {e}")
        return ['BTC/JPY', 'ETH/JPY', 'ADA/JPY']

def get_crypto_data(symbol, timeframe='30m', limit=500):
    """Lấy dữ liệu giá"""
    try:
        client = Client(
            api_key=trading_config.BINANCE_CONFIG['api_key'],
            api_secret=trading_config.BINANCE_CONFIG['api_secret'],
            testnet=trading_config.BINANCE_CONFIG['testnet']
        )
        
        # Convert symbol
        if '/JPY' in symbol:
            coin = symbol.split('/')[0]
            binance_symbol = f'{coin}USDT'
        else:
            binance_symbol = symbol.replace('/', '')
        
        interval = Client.KLINE_INTERVAL_30MINUTE
        # Use "limit days ago UTC" instead of minutes
        klines = client.get_historical_klines(binance_symbol, interval, "30 days ago UTC")
        
        if not klines:
            print(f"❌ No data for {symbol}")
            return None
        
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
            
        df.set_index('timestamp', inplace=True)
        print(f"✅ Data for {symbol}: {df.shape}")
        return df
        
    except Exception as e:
        print(f"❌ Error getting data for {symbol}: {e}")
        return None

def simple_analysis(symbol, df):
    """Phân tích đơn giản với điều kiện dễ dàng hơn"""
    try:
        if df is None or len(df) < 5:
            return None
        
        # Basic indicators
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2] if len(df) > 1 else current_price
        volume = df['volume'].iloc[-1]
        
        # Very simple conditions - price increase + volume
        price_change_pct = (current_price - prev_price) / prev_price * 100
        
        if price_change_pct > -5 and volume > 0:  # Very loose conditions
            confidence = 50 + min(abs(price_change_pct) * 2, 30)
            entry_price = current_price * 1.001
            tp_price = current_price * 1.015  # 1.5% profit
            stop_loss = current_price * 0.985  # 1.5% stop loss
            
            return {
                'symbol': symbol,
                'confidence_score': confidence,
                'entry_price': entry_price,
                'tp_price': tp_price,
                'stop_loss': stop_loss,
                'risk_reward_ratio': 1.0,
                'reason': f'Price change: {price_change_pct:.2f}%, Volume: {volume:.0f}'
            }
        
        return None
        
    except Exception as e:
        print(f"❌ Analysis error for {symbol}: {e}")
        return None

def main():
    """Main function"""
    print("🚀 SIMPLE TRADING BOT TEST")
    print("=" * 50)
    
    # Get pairs
    pairs = get_jpy_pairs()
    if not pairs:
        print("❌ No pairs found")
        return
    
    # Analyze each pair
    opportunities = []
    for symbol in pairs:
        print(f"🔍 Analyzing {symbol}...")
        
        # Get data
        df = get_crypto_data(symbol)
        if df is None:
            continue
        
        # Simple analysis
        opportunity = simple_analysis(symbol, df)
        if opportunity:
            opportunities.append(opportunity)
            print(f"✅ Found opportunity: {symbol} - Confidence {opportunity['confidence_score']}")
        else:
            print(f"❌ No opportunity: {symbol}")
    
    # Results
    print("\n" + "=" * 50)
    if opportunities:
        print(f"🎯 Found {len(opportunities)} opportunities:")
        for opp in opportunities:
            print(f"  📈 {opp['symbol']}: Confidence {opp['confidence_score']}, Entry ${opp['entry_price']:.4f}")
    else:
        print("❌ No opportunities found")

if __name__ == "__main__":
    main()
