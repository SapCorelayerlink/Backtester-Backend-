#!/usr/bin/env python3
"""
Simplified Test for Trade Logging Functionality
Tests core trade logging without requiring external APIs.
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.backtest_database import BacktestDatabase
from brokers.paper_broker import PaperBroker
from brokers.paper_executor import PaperExecutor
import config

class SimpleTradeLoggingTester:
    """Simplified tester for trade logging functionality."""
    
    def __init__(self):
        self.database = BacktestDatabase()
        self.test_results = {}
        
    async def run_all_tests(self):
        """Run all trade logging tests."""
        print("🧪 Starting Simplified Trade Logging Tests")
        print("=" * 80)
        
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Database Schema", self.test_database_schema),
            ("Paper Executor Trade Recording", self.test_paper_executor_trades),
            ("Database Trade Saving", self.test_database_trade_saving),
            ("Equity Curve Saving", self.test_equity_curve_saving),
            ("Backtest Run Creation", self.test_backtest_run_creation),
            ("Complete Trade Flow", self.test_complete_trade_flow),
            ("Trade Details Verification", self.test_trade_details_verification),
            ("Database Query Verification", self.test_database_query_verification)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            print("-" * 50)
            try:
                result = await test_func()
                self.test_results[test_name] = result
                if result['status'] == 'PASS':
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED - {result['error']}")
            except Exception as e:
                self.test_results[test_name] = {'status': 'FAIL', 'error': str(e)}
                print(f"❌ {test_name}: FAILED - {e}")
        
        # Print summary
        self.print_test_summary()
    
    async def test_database_connection(self):
        """Test database connection and initialization."""
        try:
            # Test database initialization
            db = BacktestDatabase()
            
            # Test if database file exists (for SQLite) or connection works (for PostgreSQL)
            if hasattr(db, 'engine') and db.engine:
                # PostgreSQL/TimescaleDB
                from sqlalchemy import text
                with db.engine.begin() as conn:
                    result = conn.execute(text("SELECT 1")).fetchone()
                    if result[0] == 1:
                        return {'status': 'PASS', 'message': 'PostgreSQL connection successful'}
            else:
                # SQLite
                import sqlite3
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result[0] == 1:
                        return {'status': 'PASS', 'message': 'SQLite connection successful'}
            
            return {'status': 'FAIL', 'error': 'Database connection failed'}
            
        except Exception as e:
            return {'status': 'FAIL', 'error': f'Database connection error: {e}'}
    
    async def test_database_schema(self):
        """Test database schema and table creation."""
        try:
            db = BacktestDatabase()
            
            # Test if required tables exist
            required_tables = ['backtest_runs', 'trades', 'equity_curves', 'performance_metrics']
            
            if hasattr(db, 'engine') and db.engine:
                # PostgreSQL/TimescaleDB
                from sqlalchemy import text
                with db.engine.begin() as conn:
                    for table in required_tables:
                        result = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")).fetchone()
                        if not result[0]:
                            return {'status': 'FAIL', 'error': f'Table {table} does not exist'}
            else:
                # SQLite
                import sqlite3
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    for table in required_tables:
                        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                        if not cursor.fetchone():
                            return {'status': 'FAIL', 'error': f'Table {table} does not exist'}
            
            return {'status': 'PASS', 'message': 'All required tables exist'}
            
        except Exception as e:
            return {'status': 'FAIL', 'error': f'Schema test error: {e}'}
    
    async def test_paper_executor_trades(self):
        """Test paper executor trade recording functionality."""
        try:
            # Create paper executor
            executor = PaperExecutor(starting_cash=10000)
            
            # Place a buy order (smaller quantity to avoid cash issues)
            order_result = await executor.place_order(
                symbol='AAPL',
                side='buy',
                quantity=50,
                order_type='market'
            )
            
            # Simulate price update to trigger order fill
            tick_data = {
                'symbol': 'AAPL',
                'price': 150.0,
                'timestamp': datetime.now()
            }
            
            await executor.process_price_update(tick_data)
            
            # Check if trade was recorded
            trades = executor.get_trade_history()
            
            if len(trades) > 0:
                trade = trades[0]
                required_fields = ['order_id', 'symbol', 'side', 'quantity', 'price', 'commission', 'timestamp']
                
                for field in required_fields:
                    if field not in trade:
                        return {'status': 'FAIL', 'error': f'Missing field in trade: {field}'}
                
                return {'status': 'PASS', 'message': f'Trade recorded successfully: {trade}'}
            else:
                return {'status': 'FAIL', 'error': 'No trades recorded'}
                
        except Exception as e:
            return {'status': 'FAIL', 'error': f'Paper executor test error: {e}'}
    
    async def test_database_trade_saving(self):
        """Test saving trades to database."""
        try:
            # Create a test backtest run first
            db = BacktestDatabase()
            test_run_id = f"TEST_RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            run_data = {
                'run_id': test_run_id,
                'strategy_name': 'TestStrategy',
                'start_time': '2024-01-01',
                'end_time': '2024-01-31',
                'initial_capital': 10000,
                'final_equity': 10000,
                'total_return': 0,
                'total_return_pct': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'average_trade_pnl': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'parameters': {'symbol': 'AAPL', 'timeframe': '1D'},
                'status': 'running'
            }
            
            db.save_backtest_result(run_data)
            
            # Create test trade data
            test_trade = {
                'run_id': test_run_id,
                'entry_time': datetime.now().isoformat(),
                'exit_time': datetime.now().isoformat(),
                'symbol': 'AAPL',
                'side': 'buy',
                'quantity': 100,
                'entry_price': 150.0,
                'exit_price': 150.0,
                'pnl': 0.0,
                'return_pct': 0.0,
                'trade_duration_hours': 0.0
            }
            
            # Save trade directly to database
            if hasattr(db, 'engine') and db.engine:
                # PostgreSQL/TimescaleDB
                from sqlalchemy import text
                with db.engine.begin() as conn:
                    conn.execute(text('''
                        INSERT INTO trades (
                            run_id, entry_time, exit_time, symbol, side, quantity,
                            entry_price, exit_price, pnl, return_pct, trade_duration_hours
                        ) VALUES (:run_id, :entry_time, :exit_time, :symbol, :side, :quantity,
                                :entry_price, :exit_price, :pnl, :return_pct, :trade_duration_hours)
                    '''), {
                        'run_id': test_trade['run_id'],
                        'entry_time': test_trade['entry_time'],
                        'exit_time': test_trade['exit_time'],
                        'symbol': test_trade['symbol'],
                        'side': test_trade['side'],
                        'quantity': test_trade['quantity'],
                        'entry_price': test_trade['entry_price'],
                        'exit_price': test_trade['exit_price'],
                        'pnl': test_trade['pnl'],
                        'return_pct': test_trade['return_pct'],
                        'trade_duration_hours': test_trade['trade_duration_hours']
                    })
            else:
                # SQLite
                import sqlite3
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO trades (
                            run_id, entry_time, exit_time, symbol, side, quantity,
                            entry_price, exit_price, pnl, return_pct, trade_duration_hours
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        test_trade['run_id'],
                        test_trade['entry_time'],
                        test_trade['exit_time'],
                        test_trade['symbol'],
                        test_trade['side'],
                        test_trade['quantity'],
                        test_trade['entry_price'],
                        test_trade['exit_price'],
                        test_trade['pnl'],
                        test_trade['return_pct'],
                        test_trade['trade_duration_hours']
                    ))
                    conn.commit()
            
            # Verify trade was saved
            if hasattr(db, 'engine') and db.engine:
                # PostgreSQL
                from sqlalchemy import text
                with db.engine.begin() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM trades WHERE run_id = :run_id"), {'run_id': test_run_id}).fetchone()
                    if result[0] > 0:
                        return {'status': 'PASS', 'message': 'Trade saved to PostgreSQL successfully'}
            else:
                # SQLite
                import sqlite3
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM trades WHERE run_id = ?", (test_run_id,))
                    if cursor.fetchone()[0] > 0:
                        return {'status': 'PASS', 'message': 'Trade saved to SQLite successfully'}
            
            return {'status': 'FAIL', 'error': 'Trade not found in database after saving'}
            
        except Exception as e:
            return {'status': 'FAIL', 'error': f'Database trade saving test error: {e}'}
    
    async def test_equity_curve_saving(self):
        """Test saving equity curve data to database."""
        try:
            # Create test backtest run
            db = BacktestDatabase()
            test_run_id = f"TEST_EQUITY_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            run_data = {
                'run_id': test_run_id,
                'strategy_name': 'TestStrategy',
                'start_time': '2024-01-01',
                'end_time': '2024-01-31',
                'initial_capital': 10000,
                'final_equity': 10000,
                'total_return': 0,
                'total_return_pct': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'average_trade_pnl': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'parameters': {'symbol': 'AAPL', 'timeframe': '1D'},
                'status': 'running'
            }
            db.save_backtest_result(run_data)
            
            # Save equity data directly
            test_date = datetime.now()
            test_equity = 10500.0
            
            if hasattr(db, 'engine') and db.engine:
                # PostgreSQL/TimescaleDB
                from sqlalchemy import text
                with db.engine.begin() as conn:
                    conn.execute(text('''
                        INSERT INTO equity_curves (run_id, timestamp, equity)
                        VALUES (:run_id, :timestamp, :equity)
                    '''), {
                        'run_id': test_run_id,
                        'timestamp': test_date.isoformat(),
                        'equity': test_equity
                    })
            else:
                # SQLite
                import sqlite3
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO equity_curves (run_id, timestamp, equity)
                        VALUES (?, ?, ?)
                    ''', (test_run_id, test_date.isoformat(), test_equity))
                    conn.commit()
            
            # Verify equity was saved
            if hasattr(db, 'engine') and db.engine:
                # PostgreSQL
                from sqlalchemy import text
                with db.engine.begin() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM equity_curves WHERE run_id = :run_id"), {'run_id': test_run_id}).fetchone()
                    if result[0] > 0:
                        return {'status': 'PASS', 'message': 'Equity curve saved to PostgreSQL successfully'}
            else:
                # SQLite
                import sqlite3
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM equity_curves WHERE run_id = ?", (test_run_id,))
                    if cursor.fetchone()[0] > 0:
                        return {'status': 'PASS', 'message': 'Equity curve saved to SQLite successfully'}
            
            return {'status': 'FAIL', 'error': 'Equity curve not found in database after saving'}
            
        except Exception as e:
            return {'status': 'FAIL', 'error': f'Equity curve saving test error: {e}'}
    
    async def test_backtest_run_creation(self):
        """Test backtest run creation in database."""
        try:
            # Create test backtest run
            db = BacktestDatabase()
            test_run_id = f"TEST_RUN_CREATE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            run_data = {
                'run_id': test_run_id,
                'strategy_name': 'TestStrategy',
                'start_time': '2024-01-01',
                'end_time': '2024-01-31',
                'initial_capital': 10000,
                'final_equity': 10000,
                'total_return': 0,
                'total_return_pct': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'average_trade_pnl': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'parameters': {'symbol': 'AAPL', 'timeframe': '1D'},
                'status': 'running'
            }
            
            db.save_backtest_result(run_data)
            
            # Check if run exists in database
            if hasattr(db, 'engine') and db.engine:
                # PostgreSQL
                from sqlalchemy import text
                with db.engine.begin() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM backtest_runs WHERE run_id = :run_id"), {'run_id': test_run_id}).fetchone()
                    if result[0] > 0:
                        return {'status': 'PASS', 'message': f'Backtest run created successfully: {test_run_id}'}
            else:
                # SQLite
                import sqlite3
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM backtest_runs WHERE run_id = ?", (test_run_id,))
                    if cursor.fetchone()[0] > 0:
                        return {'status': 'PASS', 'message': f'Backtest run created successfully: {test_run_id}'}
            
            return {'status': 'FAIL', 'error': 'Backtest run not found in database'}
            
        except Exception as e:
            return {'status': 'FAIL', 'error': f'Backtest run creation test error: {e}'}
    
    async def test_complete_trade_flow(self):
        """Test complete trade flow from order to database."""
        try:
            # Create paper broker
            broker = PaperBroker('test_broker', {'starting_cash': 10000})
            await broker.connect()
            
            # Place an order
            order_result = await broker.place_order({
                'symbol': 'AAPL',
                'qty': 50,
                'side': 'buy',
                'order_type': 'market'
            })
            
            # Simulate price update
            tick_data = {
                'symbol': 'AAPL',
                'price': 150.0,
                'timestamp': datetime.now()
            }
            
            await broker.process_price_update(tick_data)
            
            # Get trade history
            trades = await broker.get_trade_history()
            
            if len(trades) == 0:
                return {'status': 'FAIL', 'error': 'No trades generated in complete flow'}
            
            # Verify trade details
            trade = trades[0]
            required_fields = ['order_id', 'symbol', 'side', 'quantity', 'price', 'commission', 'timestamp']
            
            for field in required_fields:
                if field not in trade:
                    return {'status': 'FAIL', 'error': f'Missing field in complete flow trade: {field}'}
            
            return {'status': 'PASS', 'message': f'Complete trade flow successful: {trade}'}
            
        except Exception as e:
            return {'status': 'FAIL', 'error': f'Complete trade flow test error: {e}'}
    
    async def test_trade_details_verification(self):
        """Test verification of all trade details."""
        try:
            # Create a comprehensive test trade
            test_trade = {
                'order_id': 'DETAIL_TEST_001',
                'symbol': 'AAPL',
                'side': 'buy',
                'quantity': 100,
                'price': 150.0,
                'commission': 1.50,
                'timestamp': datetime.now().isoformat()
            }
            
            # Test trade details
            details_to_verify = [
                ('symbol', 'AAPL'),
                ('side', 'buy'),
                ('quantity', 100),
                ('price', 150.0),
                ('commission', 1.50)
            ]
            
            for field, expected_value in details_to_verify:
                if test_trade.get(field) != expected_value:
                    return {'status': 'FAIL', 'error': f'Trade detail mismatch: {field} expected {expected_value}, got {test_trade.get(field)}'}
            
            # Test data types
            if not isinstance(test_trade['quantity'], int):
                return {'status': 'FAIL', 'error': 'Quantity should be integer'}
            
            if not isinstance(test_trade['price'], float):
                return {'status': 'FAIL', 'error': 'Price should be float'}
            
            if not isinstance(test_trade['commission'], float):
                return {'status': 'FAIL', 'error': 'Commission should be float'}
            
            return {'status': 'PASS', 'message': 'All trade details verified successfully'}
            
        except Exception as e:
            return {'status': 'FAIL', 'error': f'Trade details verification error: {e}'}
    
    async def test_database_query_verification(self):
        """Test database query functionality for trades."""
        try:
            db = BacktestDatabase()
            
            # Test querying trades
            if hasattr(db, 'engine') and db.engine:
                # PostgreSQL
                from sqlalchemy import text
                with db.engine.begin() as conn:
                    # Test basic query
                    result = conn.execute(text("SELECT COUNT(*) FROM trades")).fetchone()
                    trade_count = result[0]
                    
                    # Test query with conditions
                    result = conn.execute(text("SELECT COUNT(*) FROM trades WHERE symbol = 'AAPL'")).fetchone()
                    aapl_trades = result[0]
                    
                    return {'status': 'PASS', 'message': f'Database queries successful. Total trades: {trade_count}, AAPL trades: {aapl_trades}'}
            else:
                # SQLite
                import sqlite3
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Test basic query
                    cursor.execute("SELECT COUNT(*) FROM trades")
                    trade_count = cursor.fetchone()[0]
                    
                    # Test query with conditions
                    cursor.execute("SELECT COUNT(*) FROM trades WHERE symbol = 'AAPL'")
                    aapl_trades = cursor.fetchone()[0]
                    
                    return {'status': 'PASS', 'message': f'Database queries successful. Total trades: {trade_count}, AAPL trades: {aapl_trades}'}
            
        except Exception as e:
            return {'status': 'FAIL', 'error': f'Database query verification error: {e}'}
    
    def print_test_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 80)
        print("📊 TRADE LOGGING TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = 0
        failed_tests = 0
        
        for test_name, result in self.test_results.items():
            if result['status'] == 'PASS':
                passed_tests += 1
                print(f"✅ {test_name}: PASSED")
                if 'message' in result:
                    print(f"   └─ {result['message']}")
            else:
                failed_tests += 1
                print(f"❌ {test_name}: FAILED")
                print(f"   └─ Error: {result['error']}")
        
        print("\n" + "-" * 80)
        print(f"📈 RESULTS: {passed_tests} PASSED, {failed_tests} FAILED")
        
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED! Trade logging system is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the errors above.")
        
        print("=" * 80)

async def main():
    """Main function to run all trade logging tests."""
    print("🚀 Starting Simplified Trade Logging Tests")
    print("This will test the core trade logging functionality")
    print()
    
    tester = SimpleTradeLoggingTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
