#!/usr/bin/env python3
"""
Test script for the enhanced backtest results functionality.
This script tests the new result saving and retrieval features.
"""

import asyncio
import json
import os
from datetime import datetime
from strategies.macrossover_strategy import MACrossover
from brokers.mock_broker import MockBroker

async def test_backtest_results():
    """Test the enhanced backtest results functionality."""
    
    print("Testing Enhanced Backtest Results Functionality")
    print("=" * 50)
    
    # Create a mock broker
    broker = MockBroker(name="test_broker")
    
    # Create a strategy instance
    strategy = MACrossover(
        name="TestMACrossover",
        broker=broker,
        params={
            'symbol': 'AAPL',
            'timeframe': '1d',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'initial_capital': 10000,
            'n1': 10,
            'n2': 30,
            'stop_loss_pct': 0.05
        }
    )
    
    print(f"Created strategy: {strategy.name}")
    print(f"Parameters: {strategy.params}")
    
    # Run the strategy
    print("\nRunning strategy...")
    run_id = await strategy.run()
    
    print(f"\nStrategy completed with run_id: {run_id}")
    
    # Check if results file was created
    results_file = f"backtest_results/{run_id}.json"
    if os.path.exists(results_file):
        print(f"✓ Results file created: {results_file}")
        
        # Load and display results
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        print(f"\nBacktest Results Summary:")
        print(f"  Strategy: {results['strategy_name']}")
        print(f"  Run ID: {results['run_id']}")
        print(f"  Start Time: {results['start_time']}")
        print(f"  End Time: {results['end_time']}")
        print(f"  Initial Capital: ${results['initial_capital']:,.2f}")
        print(f"  Final Equity: ${results['final_equity']:,.2f}")
        print(f"  Total Return: ${results['total_return']:,.2f}")
        print(f"  Total Return %: {results['total_return_pct']:.2f}%")
        
        print(f"\nTrade Summary:")
        print(f"  Total Trades: {results['summary']['total_trades']}")
        print(f"  Winning Trades: {results['summary']['winning_trades']}")
        print(f"  Losing Trades: {results['summary']['losing_trades']}")
        print(f"  Win Rate: {results['summary']['win_rate']:.1f}%")
        print(f"  Total PnL: ${results['summary']['total_pnl']:,.2f}")
        print(f"  Average Trade PnL: ${results['summary']['average_trade_pnl']:,.2f}")
        
        print(f"\nEquity Curve Points: {len(results['equity_curve'])}")
        print(f"Trades Recorded: {len(results['trades'])}")
        
        # Display first few trades
        if results['trades']:
            print(f"\nFirst 3 Trades:")
            for i, trade in enumerate(results['trades'][:3]):
                print(f"  Trade {i+1}: {trade['side'].upper()} {trade['symbol']} "
                      f"@ ${trade['entry_price']:.2f} -> ${trade['exit_price']:.2f} "
                      f"(PnL: ${trade['pnl']:.2f})")
        
    else:
        print(f"✗ Results file not found: {results_file}")
    
    # Test listing available results
    print(f"\n" + "=" * 50)
    print("Testing Results Listing")
    
    results_dir = "backtest_results"
    if os.path.exists(results_dir):
        json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
        print(f"Found {len(json_files)} result files:")
        for file in json_files:
            file_path = os.path.join(results_dir, file)
            file_size = os.path.getsize(file_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            print(f"  {file} ({file_size} bytes, modified {mod_time})")
    else:
        print("No backtest_results directory found.")
    
    print(f"\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_backtest_results()) 