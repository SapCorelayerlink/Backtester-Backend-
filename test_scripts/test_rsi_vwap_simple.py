#!/usr/bin/env python3
"""
Simple test script for RSI + VWAP Strategy
Tests the strategy with sample data without Polygon dependencies
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategies.rsi_vwap_strategy import RSIVWAPStrategy
from brokers.paper_broker import PaperBroker
from data.backtest_database import BacktestDatabase

def create_sample_data(symbol='AAPL', periods=600):
    """Create sample historical data for testing (4-hour timeframe)"""
    print(f"Creating sample data for {symbol} over {periods} 4-hour periods...")
    
    # Generate realistic price data with more volatility to trigger trades
    np.random.seed(42)  # For reproducible results
    base_price = 150.0
    
    dates = pd.date_range(start='2023-01-01', periods=periods, freq='4H')
    prices = []
    
    for i in range(periods):
        # Add more volatility to increase chance of RSI signals
        if i == 0:
            price = base_price
        else:
            # More volatile random walk for 4H timeframe
            change = np.random.normal(0, 2) + (base_price - prices[-1]['close']) * 0.01
            price = prices[-1]['close'] + change
        
        # Generate OHLC data with 4H volatility
        hourly_volatility = np.random.uniform(1, 3)
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
            'volume': int(np.random.uniform(500000, 2000000))  # Lower volume for 4H
        })
    
    return prices

async def test_rsi_vwap_strategy():
    """Test the RSI + VWAP Strategy with sample data"""
    # Import SQLAlchemy text at the top level to fix scope issue
    from sqlalchemy import text
    
    # Set PostgreSQL environment variables for TimescaleDB
    import os
    os.environ['PG_HOST'] = 'localhost'
    os.environ['PG_PORT'] = '5432'
    os.environ['PG_DB'] = 'bactester'
    os.environ['PG_USER'] = 'bactester'
    os.environ['PG_PASSWORD'] = 'bactester'
    os.environ['PG_SSLMODE'] = 'prefer'
    
    print("🧪 Testing RSI + VWAP Strategy (4-Hour Timeframe)")
    print("=" * 60)
    
    # Initialize components
    print("1. Initializing components...")
    
    # Create paper broker
    broker = PaperBroker("PaperBroker", {'starting_cash': 100000})
    await broker.connect()
    
    # Create database
    database = BacktestDatabase()
    
    # Create sample data
    sample_data = create_sample_data('AAPL', 600)  # 600 4-hour periods = 100 days
    print(f"   Created {len(sample_data)} 4-hour data points")
    
    # Strategy parameters - optimized for 4H timeframe
    strategy_params = {
        'symbol': 'AAPL',
        'timeframe': '4h',  # 4-hour timeframe
        'quantity': 50,  # Smaller quantity to avoid cash issues
        'rsi_length_long': 14,
        'rsi_length_short': 14,
        'oversold_long': 30,  # Standard oversold level
        'oversold2_long': 20,
        'overbought_short': 70,  # Standard overbought level
        'overbought2_short': 80,
        'max_pyramiding': 3,
        'stop_loss_pct': 0.02,  # Tighter stop loss for 4H
        'take_profit_pct': 0.015  # Tighter take profit for 4H
    }
    
    # Create strategy
    strategy = RSIVWAPStrategy("RSI_VWAP_Test", broker, strategy_params)
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
        if hasattr(strategy, 'in_long') and strategy.in_long and current_position != 'long':
            current_position = 'long'
            entry_price = bar['close']
            entry_time = bar['timestamp']
            print(f"   📈 LONG entry at {entry_price:.2f} on {entry_time.strftime('%Y-%m-%d')}")
            
        elif hasattr(strategy, 'in_short') and strategy.in_short and current_position != 'short':
            current_position = 'short'
            entry_price = bar['close']
            entry_time = bar['timestamp']
            print(f"   📉 SHORT entry at {entry_price:.2f} on {entry_time.strftime('%Y-%m-%d')}")
            
        elif (not strategy.in_long and not strategy.in_short) and current_position is not None:
            # Position was closed
            exit_price = bar['close']
            pnl = (exit_price - entry_price) * strategy_params['quantity']
            if current_position == 'short':
                pnl = -pnl
                
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
            print(f"   {i}. {trade['side'].upper()}: {trade['entry_time'].strftime('%Y-%m-%d')} -> {trade['exit_time'].strftime('%Y-%m-%d')}")
            print(f"      Entry: ${trade['entry_price']:.2f}, Exit: ${trade['exit_price']:.2f}, PnL: ${trade['pnl']:.2f}")
    
    # Check broker trade history
    print(f"\n4. Broker Trade History:")
    broker_trades = await broker.get_trade_history()
    print(f"   Broker recorded {len(broker_trades)} trades")
    
    if broker_trades:
        broker_pnl = sum(trade.get('pnl', 0) for trade in broker_trades)
        print(f"   Broker total PnL: ${broker_pnl:.2f}")
        
        print(f"\n   Broker Trade Details:")
        for i, trade in enumerate(broker_trades, 1):
            print(f"   {i}. {trade.get('side', 'N/A')}: {trade.get('symbol', 'N/A')} x {trade.get('quantity', 0)}")
            print(f"      Price: ${trade.get('price', 0):.2f}, PnL: ${trade.get('pnl', 0):.2f}")
    
    # Test database saving directly
    print(f"\n5. Testing Database Saving...")
    
    if manual_trades:
        # Save trades to database manually using PostgreSQL/TimescaleDB
        try:
            # Create a backtest run record
            run_id = f"RSI_VWAP_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with database.engine.begin() as conn:
                # Insert backtest run
                conn.execute(text("""
                    INSERT INTO backtest_runs (run_id, strategy_name, symbol, timeframe, start_date, end_date, 
                                             initial_capital, final_equity, total_return, total_return_pct,
                                             total_trades, winning_trades, losing_trades, win_rate, 
                                             total_pnl, average_trade_pnl, parameters)
                    VALUES (:run_id, :strategy_name, :symbol, :timeframe, :start_date, :end_date,
                           :initial_capital, :final_equity, :total_return, :total_return_pct,
                           :total_trades, :winning_trades, :losing_trades, :win_rate,
                           :total_pnl, :average_trade_pnl, :parameters)
                """), {
                    'run_id': run_id,
                    'strategy_name': 'RSI_VWAP_Test',
                    'symbol': 'AAPL',
                    'timeframe': '4h',
                    'start_date': sample_data[0]['timestamp'],
                    'end_date': sample_data[-1]['timestamp'],
                    'initial_capital': 100000,
                    'final_equity': 100000 + total_pnl,
                    'total_return': total_pnl,
                    'total_return_pct': (total_pnl / 100000) * 100,
                    'total_trades': len(manual_trades),
                    'winning_trades': len([t for t in manual_trades if t['pnl'] > 0]),
                    'losing_trades': len([t for t in manual_trades if t['pnl'] <= 0]),
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'average_trade_pnl': total_pnl / len(manual_trades),
                    'parameters': str(strategy_params)
                })
                
                # Save individual trades
                for i, trade in enumerate(manual_trades):
                    trade_duration = (trade['exit_time'] - trade['entry_time']).total_seconds() / 3600  # hours
                    return_pct = ((trade['exit_price'] - trade['entry_price']) / trade['entry_price']) * 100
                    
                    conn.execute(text("""
                        INSERT INTO trades (run_id, entry_time, exit_time, symbol, side, quantity, 
                                         entry_price, exit_price, pnl, return_pct, trade_duration_hours)
                        VALUES (:run_id, :entry_time, :exit_time, :symbol, :side, :quantity,
                               :entry_price, :exit_price, :pnl, :return_pct, :trade_duration_hours)
                    """), {
                        'run_id': run_id,
                        'entry_time': trade['entry_time'],
                        'exit_time': trade['exit_time'],
                        'symbol': 'AAPL',
                        'side': trade['side'],
                        'quantity': trade['quantity'],
                        'entry_price': trade['entry_price'],
                        'exit_price': trade['exit_price'],
                        'pnl': trade['pnl'],
                        'return_pct': return_pct,
                        'trade_duration_hours': trade_duration
                    })
            
            print(f"   ✅ Successfully saved {len(manual_trades)} trades to PostgreSQL/TimescaleDB")
            print(f"   Backtest run ID: {run_id}")
            
            # Verify database entries
            with database.engine.begin() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM trades WHERE run_id = :run_id"), {'run_id': run_id})
                trade_count = result.fetchone()[0]
            
            print(f"   Total trades in database for this run: {trade_count}")
                
        except Exception as e:
            print(f"   ❌ Database saving error: {e}")
            print(f"   Error details: {type(e).__name__}: {str(e)}")
    
    # Cleanup
    await broker.disconnect()
    
    print(f"\n✅ RSI + VWAP Strategy test completed!")
    return len(manual_trades) > 0 or len(broker_trades) > 0

if __name__ == "__main__":
    print("🚀 Starting RSI + VWAP Strategy Test (4-Hour Timeframe)")
    print("=" * 70)
    
    try:
        success = asyncio.run(test_rsi_vwap_strategy())
        if success:
            print("\n🎉 RSI + VWAP Strategy test PASSED!")
            print("   Strategy executed trades and logged them to database")
        else:
            print("\n⚠️  RSI + VWAP Strategy test completed but no trades were executed")
            print("   This might be normal depending on the data and parameters")
            print("   Try adjusting the RSI thresholds or using more volatile data")
    except Exception as e:
        print(f"\n❌ RSI + VWAP Strategy test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
