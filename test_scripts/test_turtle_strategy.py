#!/usr/bin/env python3
"""
Test script for Turtle Strategy (1-hour timeframe)
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategies.Turtle import TurtleStrategy
from brokers.paper_broker import PaperBroker

def create_sample_data(symbol='AAPL', periods=200):
    """Create sample historical data for testing (1-hour timeframe)"""
    print(f"Creating sample data for {symbol} over {periods} 1-hour periods...")
    
    # Generate realistic price data for 1-hour timeframe
    np.random.seed(42)  # For reproducible results
    base_price = 150.0
    
    dates = pd.date_range(start='2023-01-01', periods=periods, freq='1h')
    prices = []
    
    for i in range(periods):
        if i == 0:
            price = base_price
        else:
            # Random walk for 1H timeframe
            change = np.random.normal(0, 0.5) + (base_price - prices[-1]['close']) * 0.001
            price = prices[-1]['close'] + change
        
        # Generate OHLC data with 1H volatility
        hourly_volatility = np.random.uniform(0.5, 1.5)
        high = price + np.random.uniform(0, hourly_volatility)
        low = price - np.random.uniform(0, hourly_volatility)
        open_price = price + np.random.uniform(-hourly_volatility/2, hourly_volatility/2)
        close_price = price + np.random.uniform(-hourly_volatility/2, hourly_volatility/2)
        
        # Ensure OHLC relationships
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        prices.append({
            'timestamp': dates[i],
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close_price, 2),
            'volume': int(np.random.uniform(100000, 500000))  # Lower volume for 1H
        })
    
    return prices

async def test_turtle_strategy():
    """Test the Turtle Strategy with sample data"""
    print("🧪 Testing Turtle Strategy (1-Hour Timeframe)")
    print("=" * 60)
    
    # Initialize components
    print("1. Initializing components...")
    
    # Create paper broker
    broker = PaperBroker("PaperBroker", {'starting_cash': 100000})
    await broker.connect()
    
    # Create sample data
    sample_data = create_sample_data('AAPL', 200)  # 200 1-hour periods
    print(f"   Created {len(sample_data)} 1-hour data points")
    
    # Strategy parameters - optimized for 1H timeframe
    strategy_params = {
        'symbol': 'AAPL',
        'timeframe': '1h',  # 1-hour timeframe
        'quantity': 100,
        'stop_n': 2.0,
        'risk_percent': 0.01,
        'pyramid_n': 0.5,
        'max_units': 5,
        'atr_period': 14,
        'l1_long': 20,  # 20-hour highs
        'l2_long': 55,  # 55-hour highs
        'l1_long_exit': 10,
        'l2_long_exit': 20,
        'initial_capital': 100000
    }
    
    # Create strategy
    strategy = TurtleStrategy("Turtle_Test", broker, strategy_params)
    await strategy.init()
    
    print("2. Running strategy on sample data...")
    
    # Track trades manually for verification
    manual_trades = []
    current_position = None
    entry_price = 0
    entry_time = None
    
    # Process each bar
    for i, bar in enumerate(sample_data):
        await strategy.on_bar(pd.Series(bar))
        
        # Check if a trade was executed
        if hasattr(strategy, 'in_buy') and strategy.in_buy and current_position != 'long':
            current_position = 'long'
            entry_price = bar['close']
            entry_time = bar['timestamp']
            print(f"   📈 LONG entry at {entry_price:.2f} on {entry_time.strftime('%Y-%m-%d %H:%M')}")
            
        elif (not strategy.in_buy) and current_position is not None:
            # Position was closed
            exit_price = bar['close']
            pnl = (exit_price - entry_price) * strategy_params['quantity']
            
            manual_trades.append({
                'entry_time': entry_time,
                'exit_time': bar['timestamp'],
                'side': current_position,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'quantity': strategy_params['quantity']
            })
            
            print(f"   💰 {current_position.upper()} exit at {exit_price:.2f}, PnL: ${pnl:.2f}")
            current_position = None
    
    print(f"\n3. Strategy Results:")
    print(f"   Manual trades detected: {len(manual_trades)}")
    
    if manual_trades:
        total_pnl = sum(trade['pnl'] for trade in manual_trades)
        winning_trades = [t for t in manual_trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / len(manual_trades) * 100
        
        print(f"   Total PnL: ${total_pnl:.2f}")
        print(f"   Win rate: {win_rate:.1f}% ({len(winning_trades)}/{len(manual_trades)})")
        
        print(f"\n   Trade Details:")
        for i, trade in enumerate(manual_trades, 1):
            print(f"   {i}. {trade['side'].upper()}: {trade['entry_time'].strftime('%Y-%m-%d %H:%M')} -> {trade['exit_time'].strftime('%Y-%m-%d %H:%M')}")
            print(f"      Entry: ${trade['entry_price']:.2f}, Exit: ${trade['exit_price']:.2f}, PnL: ${trade['pnl']:.2f}")
    
    # Cleanup
    await broker.disconnect()
    
    print(f"\n✅ Turtle Strategy test completed!")
    return len(manual_trades) > 0

if __name__ == "__main__":
    print("🚀 Starting Turtle Strategy Test (1-Hour Timeframe)")
    print("=" * 70)
    
    try:
        success = asyncio.run(test_turtle_strategy())
        if success:
            print("\n🎉 Turtle Strategy test PASSED!")
            print("   Strategy executed trades on 1-hour timeframe")
        else:
            print("\n⚠️  Turtle Strategy test completed but no trades were executed")
            print("   This might be normal depending on the data and parameters")
    except Exception as e:
        print(f"\n❌ Turtle Strategy test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
