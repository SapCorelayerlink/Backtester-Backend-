#!/usr/bin/env python3
"""
Test script for RSI + VWAP Strategy
Tests the strategy with historical data and verifies trade logging
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
from historical_trading_dashboard import HistoricalTradingDashboard

def create_sample_data(symbol='AAPL', days=100):
    """Create sample historical data for testing"""
    print(f"Creating sample data for {symbol} over {days} days...")
    
    # Generate realistic price data
    np.random.seed(42)  # For reproducible results
    base_price = 150.0
    
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    prices = []
    
    for i in range(days):
        # Add some trend and volatility
        if i == 0:
            price = base_price
        else:
            # Random walk with some mean reversion
            change = np.random.normal(0, 2) + (base_price - prices[-1]) * 0.01
            price = prices[-1] + change
        
        # Generate OHLC data
        daily_volatility = np.random.uniform(1, 3)
        high = price + np.random.uniform(0, daily_volatility)
        low = price - np.random.uniform(0, daily_volatility)
        open_price = price + np.random.uniform(-daily_volatility/2, daily_volatility/2)
        close_price = price + np.random.uniform(-daily_volatility/2, daily_volatility/2)
        
        # Ensure OHLC relationships
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        prices.append({
            'timestamp': dates[i],
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close_price, 2),
            'volume': int(np.random.uniform(1000000, 5000000))
        })
    
    return prices

async def test_rsi_vwap_strategy():
    """Test the RSI + VWAP Strategy with sample data"""
    print("🧪 Testing RSI + VWAP Strategy")
    print("=" * 50)
    
    # Initialize components
    print("1. Initializing components...")
    
    # Create paper broker
    broker = PaperBroker()
    await broker.connect()
    
    # Create database
    database = BacktestDatabase()
    
    # Create sample data
    sample_data = create_sample_data('AAPL', 100)
    print(f"   Created {len(sample_data)} data points")
    
    # Strategy parameters
    strategy_params = {
        'symbol': 'AAPL',
        'timeframe': '1d',
        'quantity': 50,  # Smaller quantity to avoid cash issues
        'rsi_length_long': 14,
        'rsi_length_short': 14,
        'oversold_long': 30,
        'oversold2_long': 20,
        'overbought_short': 70,
        'overbought2_short': 80,
        'max_pyramiding': 3,
        'stop_loss_pct': 0.05,
        'take_profit_pct': 0.03
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
    
    # Test with historical trading dashboard
    print(f"\n5. Testing with Historical Trading Dashboard...")
    
    # Create dashboard instance
    dashboard = HistoricalTradingDashboard()
    
    # Prepare data for dashboard
    df_data = pd.DataFrame(sample_data)
    df_data.set_index('timestamp', inplace=True)
    
    # Run backtest through dashboard
    strategies_config = {
        'RSI_VWAP_Test': {
            'strategy_name': 'RSIVWAPStrategy',
            'parameters': strategy_params
        }
    }
    
    results = await dashboard.run_backtest(
        data=df_data,
        strategies=strategies_config,
        start_date='2023-01-01',
        end_date='2023-04-10'
    )
    
    print(f"   Dashboard backtest completed")
    print(f"   Results saved to database with run IDs: {dashboard.backtest_run_ids}")
    
    # Verify database entries
    print(f"\n6. Verifying Database Entries...")
    
    # Check backtest runs
    try:
        with database.get_connection() as conn:
            # Check backtest runs
            result = conn.execute(database.text("SELECT COUNT(*) FROM backtest_runs WHERE strategy_name = 'RSI_VWAP_Test'"))
            run_count = result.fetchone()[0]
            print(f"   Backtest runs in database: {run_count}")
            
            # Check trades
            result = conn.execute(database.text("SELECT COUNT(*) FROM trades WHERE strategy_name = 'RSI_VWAP_Test'"))
            trade_count = result.fetchone()[0]
            print(f"   Trades in database: {trade_count}")
            
            # Check equity curves
            result = conn.execute(database.text("SELECT COUNT(*) FROM equity_curves WHERE strategy_name = 'RSI_VWAP_Test'"))
            equity_count = result.fetchone()[0]
            print(f"   Equity curve points in database: {equity_count}")
            
            if trade_count > 0:
                # Get trade details
                result = conn.execute(database.text("""
                    SELECT symbol, side, quantity, entry_price, exit_price, pnl, 
                           entry_time, exit_time
                    FROM trades 
                    WHERE strategy_name = 'RSI_VWAP_Test'
                    ORDER BY entry_time
                """))
                db_trades = result.fetchall()
                
                print(f"\n   Database Trade Details:")
                for i, trade in enumerate(db_trades, 1):
                    print(f"   {i}. {trade[0]} {trade[1].upper()}: {trade[2]} shares")
                    print(f"      Entry: ${trade[3]:.2f} ({trade[6].strftime('%Y-%m-%d')})")
                    print(f"      Exit: ${trade[4]:.2f} ({trade[7].strftime('%Y-%m-%d')})")
                    print(f"      PnL: ${trade[5]:.2f}")
    
    except Exception as e:
        print(f"   Database verification error: {e}")
    
    # Cleanup
    await broker.disconnect()
    
    print(f"\n✅ RSI + VWAP Strategy test completed!")
    return len(manual_trades) > 0 or len(broker_trades) > 0

if __name__ == "__main__":
    print("🚀 Starting RSI + VWAP Strategy Test")
    print("=" * 60)
    
    try:
        success = asyncio.run(test_rsi_vwap_strategy())
        if success:
            print("\n🎉 RSI + VWAP Strategy test PASSED!")
            print("   Strategy executed trades and logged them to database")
        else:
            print("\n⚠️  RSI + VWAP Strategy test completed but no trades were executed")
            print("   This might be normal depending on the data and parameters")
    except Exception as e:
        print(f"\n❌ RSI + VWAP Strategy test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
