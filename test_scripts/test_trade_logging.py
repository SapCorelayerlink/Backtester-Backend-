#!/usr/bin/env python3
"""
Comprehensive Test for Trade Logging Functionality
Tests every detail of the trade logging system to ensure proper functioning.
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

from historical_trading_dashboard import HistoricalTradingDashboard
from data.backtest_database import BacktestDatabase
from brokers.paper_broker import PaperBroker
from brokers.paper_executor import PaperExecutor
import config

class TradeLoggingTester:
    """Comprehensive tester for trade logging functionality."""
    
    def __init__(self):
        self.database = BacktestDatabase()
        self.test_results = {}
        
    async def run_all_tests(self):
        """Run all trade logging tests."""
        print("🧪 Starting Comprehensive Trade Logging Tests")
        print("=" * 80)
        
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Database Schema", self.test_database_schema),
            ("Paper Executor Trade Recording", self.test_paper_executor_trades),
            ("Trade Data Enhancement", self.test_trade_data_enhancement),
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
                with db.engine.begin() as conn:
                    result = conn.execute("SELECT 1").fetchone()
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
                with db.engine.begin() as conn:
                    for table in required_tables:
                        result = conn.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')").fetchone()
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
            
            # Place a buy order
            order_result = await executor.place_order(
                symbol='AAPL',
                side='buy',
                quantity=100,
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
    
    async def test_trade_data_enhancement(self):
        """Test trade data enhancement functionality."""
        try:
            # Create a sample trade
            sample_trade = {
                'order_id': 'TEST_ORDER_001',
                'symbol': 'AAPL',
                'side': 'buy',
                'quantity': 100,
                'price': 150.0,
                'commission': 1.50,
                'timestamp': datetime.now().isoformat()
            }
            
            # Create dashboard instance to test enhancement
            dashboard = HistoricalTradingDashboard(symbols=['AAPL'], starting_cash=10000)
            
            # Test trade enhancement
            enhanced_trade = await dashboard._enhance_trade_data(
                sample_trade, 
                'TestStrategy', 
                datetime.now()
            )
            
            # Check required fields
            required_fields = [
                'trade_id', 'order_id', 'symbol', 'side', 'quantity',
                'entry_price', 'exit_price', 'entry_time', 'exit_time',
                'pnl', 'return_pct', 'trade_duration_hours', 'commission',
                'timestamp', 'strategy_name', 'status'
            ]
            
            for field in required_fields:
                if field not in enhanced_trade:
                    return {'status': 'FAIL', 'error': f'Missing field in enhanced trade: {field}'}
            
            # Check data types and values
            if not enhanced_trade['trade_id'].startswith('TRADE_'):
                return {'status': 'FAIL', 'error': 'Invalid trade ID format'}
            
            if enhanced_trade['symbol'] != 'AAPL':
                return {'status': 'FAIL', 'error': 'Symbol not preserved'}
            
            if enhanced_trade['quantity'] != 100:
                return {'status': 'FAIL', 'error': 'Quantity not preserved'}
            
            return {'status': 'PASS', 'message': f'Trade enhancement successful: {enhanced_trade}'}
            
        except Exception as e:
            return {'status': 'FAIL', 'error': f'Trade enhancement test error: {e}'}
    
    async def test_database_trade_saving(self):
        """Test saving trades to database."""
        try:
            # Create a test backtest run first
            db = BacktestDatabase()
            test_run_id = f"TEST_RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            run_data = {
                'run_id': test_run_id,
                'strategy_name': 'TestStrategy',
                'symbol': 'AAPL',
                'timeframe': '1D',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
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
                'parameters': '{}',
                'status': 'running'
            }
            
            db.save_backtest_result(run_data)
            
            # Create dashboard and test trade saving
            dashboard = HistoricalTradingDashboard(symbols=['AAPL'], starting_cash=10000)
            dashboard.backtest_run_ids['TestStrategy'] = test_run_id
            
            # Create test trade
            test_trade = {
                'trade_id': 'TRADE_TEST_001',
                'order_id': 'ORDER_TEST_001',
                'symbol': 'AAPL',
                'side': 'buy',
                'quantity': 100,
                'entry_price': 150.0,
                'exit_price': 150.0,
                'entry_time': datetime.now().isoformat(),
                'exit_time': datetime.now().isoformat(),
                'pnl': 0.0,
                'return_pct': 0.0,
                'trade_duration_hours': 0.0,
                'commission': 1.50,
                'timestamp': datetime.now().isoformat(),
                'strategy_name': 'TestStrategy',
                'status': 'closed'
            }
            
            # Save trade to database
            await dashboard._save_trade_to_database(test_trade, 'TestStrategy')
            
            # Verify trade was saved
            if hasattr(db, 'engine') and db.engine:
                # PostgreSQL
                with db.engine.begin() as conn:
                    result = conn.execute("SELECT COUNT(*) FROM trades WHERE run_id = :run_id", {'run_id': test_run_id}).fetchone()
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
            # Create dashboard and test equity saving
            dashboard = HistoricalTradingDashboard(symbols=['AAPL'], starting_cash=10000)
            test_run_id = f"TEST_EQUITY_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            dashboard.backtest_run_ids['TestStrategy'] = test_run_id
            
            # Create test backtest run
            db = BacktestDatabase()
            run_data = {
                'run_id': test_run_id,
                'strategy_name': 'TestStrategy',
                'symbol': 'AAPL',
                'timeframe': '1D',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
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
                'parameters': '{}',
                'status': 'running'
            }
            db.save_backtest_result(run_data)
            
            # Save equity data
            test_date = datetime.now()
            test_equity = 10500.0
            await dashboard._save_equity_to_database('TestStrategy', test_date, test_equity)
            
            # Verify equity was saved
            if hasattr(db, 'engine') and db.engine:
                # PostgreSQL
                with db.engine.begin() as conn:
                    result = conn.execute("SELECT COUNT(*) FROM equity_curves WHERE run_id = :run_id", {'run_id': test_run_id}).fetchone()
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
            # Create dashboard
            dashboard = HistoricalTradingDashboard(symbols=['AAPL'], starting_cash=10000)
            
            # Test backtest run creation
            test_params = {
                'symbols': ['AAPL'],
                'timeframe': '1D',
                'initial_capital': 10000
            }
            
            await dashboard._create_backtest_run('TestStrategy', test_params)
            
            # Verify run was created
            run_id = dashboard.backtest_run_ids.get('TestStrategy')
            if not run_id:
                return {'status': 'FAIL', 'error': 'Backtest run ID not created'}
            
            # Check if run exists in database
            db = BacktestDatabase()
            if hasattr(db, 'engine') and db.engine:
                # PostgreSQL
                with db.engine.begin() as conn:
                    result = conn.execute("SELECT COUNT(*) FROM backtest_runs WHERE run_id = :run_id", {'run_id': run_id}).fetchone()
                    if result[0] > 0:
                        return {'status': 'PASS', 'message': f'Backtest run created successfully: {run_id}'}
            else:
                # SQLite
                import sqlite3
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM backtest_runs WHERE run_id = ?", (run_id,))
                    if cursor.fetchone()[0] > 0:
                        return {'status': 'PASS', 'message': f'Backtest run created successfully: {run_id}'}
            
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
                'qty': 100,
                'side': 'buy',
                'order_type': 'MKT'
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
                with db.engine.begin() as conn:
                    # Test basic query
                    result = conn.execute("SELECT COUNT(*) FROM trades").fetchone()
                    trade_count = result[0]
                    
                    # Test query with conditions
                    result = conn.execute("SELECT COUNT(*) FROM trades WHERE symbol = 'AAPL'").fetchone()
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
    print("🚀 Starting Comprehensive Trade Logging Tests")
    print("This will test every detail of the trade logging system")
    print()
    
    tester = TradeLoggingTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
