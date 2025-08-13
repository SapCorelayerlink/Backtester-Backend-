#!/usr/bin/env python3
"""
View and query data from PostgreSQL/TimescaleDB database
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# Set PostgreSQL environment variables
os.environ['PG_HOST'] = 'localhost'
os.environ['PG_PORT'] = '5432'
os.environ['PG_DB'] = 'bactester'
os.environ['PG_USER'] = 'bactester'
os.environ['PG_PASSWORD'] = 'bactester'
os.environ['PG_SSLMODE'] = 'prefer'

def connect_to_database():
    """Connect to PostgreSQL/TimescaleDB"""
    url = f"postgresql+psycopg2://bactester:bactester@localhost:5432/bactester?sslmode=prefer"
    return create_engine(url)

def view_database_overview():
    """Show overview of all tables and their record counts"""
    engine = connect_to_database()
    
    print("📊 DATABASE OVERVIEW")
    print("=" * 50)
    
    with engine.begin() as conn:
        # Get table counts
        tables = ['backtest_runs', 'trades', 'equity_curves', 'performance_metrics', 'strategies', 'market_data']
        
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            print(f"   {table:20} : {count:5} records")
    
    print()

def view_backtest_runs():
    """Show all backtest runs"""
    engine = connect_to_database()
    
    print("🏃 BACKTEST RUNS")
    print("=" * 80)
    
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT run_id, strategy_name, symbol, timeframe, 
                   start_date, end_date, total_trades, total_pnl, win_rate,
                   created_at
            FROM backtest_runs 
            ORDER BY created_at DESC
        """))
        
        rows = result.fetchall()
        
        if not rows:
            print("   No backtest runs found")
            return
        
        print(f"{'Run ID':<25} {'Strategy':<15} {'Symbol':<8} {'TF':<4} {'Trades':<6} {'PnL':<10} {'Win%':<6} {'Created'}")
        print("-" * 80)
        
        for row in rows:
            run_id, strategy, symbol, tf, start_date, end_date, trades, pnl, win_rate, created = row
            print(f"{run_id:<25} {strategy:<15} {symbol:<8} {tf:<4} {trades:<6} ${pnl:<9.2f} {win_rate:<5.1f}% {created.strftime('%Y-%m-%d %H:%M')}")

def view_trades(run_id=None):
    """Show trades - optionally filtered by run_id"""
    engine = connect_to_database()
    
    print("💰 TRADES")
    print("=" * 100)
    
    with engine.begin() as conn:
        if run_id:
            query = """
                SELECT run_id, entry_time, exit_time, symbol, side, quantity,
                       entry_price, exit_price, pnl, return_pct, trade_duration_hours
                FROM trades 
                WHERE run_id = :run_id
                ORDER BY entry_time
            """
            result = conn.execute(text(query), {'run_id': run_id})
            print(f"   Showing trades for run: {run_id}")
        else:
            query = """
                SELECT run_id, entry_time, exit_time, symbol, side, quantity,
                       entry_price, exit_price, pnl, return_pct, trade_duration_hours
                FROM trades 
                ORDER BY entry_time DESC
                LIMIT 20
            """
            result = conn.execute(text(query))
            print("   Showing latest 20 trades")
        
        rows = result.fetchall()
        
        if not rows:
            print("   No trades found")
            return
        
        print(f"{'Run ID':<25} {'Entry':<16} {'Exit':<16} {'Symbol':<8} {'Side':<6} {'Qty':<6} {'Entry':<8} {'Exit':<8} {'PnL':<10} {'Return%':<8} {'Duration'}")
        print("-" * 100)
        
        for row in rows:
            run_id, entry_time, exit_time, symbol, side, qty, entry_price, exit_price, pnl, return_pct, duration = row
            print(f"{run_id:<25} {entry_time.strftime('%Y-%m-%d %H:%M'):<16} {exit_time.strftime('%Y-%m-%d %H:%M'):<16} {symbol:<8} {side:<6} {qty:<6} ${entry_price:<7.2f} ${exit_price:<7.2f} ${pnl:<9.2f} {return_pct:<7.2f}% {duration:<8.1f}h")

def view_strategy_performance(strategy_name=None):
    """Show performance metrics for strategies"""
    engine = connect_to_database()
    
    print("📈 STRATEGY PERFORMANCE")
    print("=" * 80)
    
    with engine.begin() as conn:
        if strategy_name:
            query = """
                SELECT run_id, symbol, timeframe, total_trades, total_pnl, win_rate,
                       total_return_pct, average_trade_pnl, sharpe_ratio, max_drawdown
                FROM backtest_runs 
                WHERE strategy_name = :strategy_name
                ORDER BY created_at DESC
            """
            result = conn.execute(text(query), {'strategy_name': strategy_name})
            print(f"   Showing performance for strategy: {strategy_name}")
        else:
            query = """
                SELECT strategy_name, COUNT(*) as runs, 
                       AVG(total_pnl) as avg_pnl, AVG(win_rate) as avg_win_rate,
                       SUM(total_pnl) as total_pnl, AVG(total_return_pct) as avg_return_pct
                FROM backtest_runs 
                GROUP BY strategy_name
                ORDER BY total_pnl DESC
            """
            result = conn.execute(text(query))
            print("   Showing aggregated performance by strategy")
        
        rows = result.fetchall()
        
        if not rows:
            print("   No performance data found")
            return
        
        if strategy_name:
            print(f"{'Run ID':<25} {'Symbol':<8} {'TF':<4} {'Trades':<6} {'PnL':<10} {'Win%':<6} {'Return%':<8} {'Avg PnL':<10} {'Sharpe':<8} {'Max DD%'}")
            print("-" * 80)
            
            for row in rows:
                run_id, symbol, tf, trades, pnl, win_rate, return_pct, avg_pnl, sharpe, max_dd = row
                print(f"{run_id:<25} {symbol:<8} {tf:<4} {trades:<6} ${pnl:<9.2f} {win_rate:<5.1f}% {return_pct:<7.2f}% ${avg_pnl:<9.2f} {sharpe:<7.2f} {max_dd:<7.2f}%")
        else:
            print(f"{'Strategy':<20} {'Runs':<6} {'Total PnL':<12} {'Avg PnL':<10} {'Avg Win%':<10} {'Avg Return%':<12}")
            print("-" * 80)
            
            for row in rows:
                strategy, runs, avg_pnl, avg_win_rate, total_pnl, avg_return_pct = row
                print(f"{strategy:<20} {runs:<6} ${total_pnl:<11.2f} ${avg_pnl:<9.2f} {avg_win_rate:<9.1f}% {avg_return_pct:<11.2f}%")

def view_detailed_trade_analysis(run_id):
    """Show detailed analysis for a specific backtest run"""
    engine = connect_to_database()
    
    print(f"🔍 DETAILED ANALYSIS FOR RUN: {run_id}")
    print("=" * 80)
    
    with engine.begin() as conn:
        # Get backtest run details
        result = conn.execute(text("""
            SELECT strategy_name, symbol, timeframe, start_date, end_date,
                   initial_capital, final_equity, total_return, total_return_pct,
                   total_trades, winning_trades, losing_trades, win_rate,
                   total_pnl, average_trade_pnl, sharpe_ratio, max_drawdown
            FROM backtest_runs 
            WHERE run_id = :run_id
        """), {'run_id': run_id})
        
        run_data = result.fetchone()
        
        if not run_data:
            print(f"   Run ID {run_id} not found")
            return
        
        strategy, symbol, tf, start_date, end_date, initial_cap, final_equity, total_return, return_pct, total_trades, winning_trades, losing_trades, win_rate, total_pnl, avg_pnl, sharpe, max_dd = run_data
        
        print(f"   Strategy: {strategy}")
        print(f"   Symbol: {symbol} ({tf})")
        print(f"   Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"   Initial Capital: ${initial_cap:,.2f}")
        print(f"   Final Equity: ${final_equity:,.2f}")
        print(f"   Total Return: ${total_return:,.2f} ({return_pct:.2f}%)")
        print(f"   Total Trades: {total_trades} (Wins: {winning_trades}, Losses: {losing_trades})")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Average Trade PnL: ${avg_pnl:.2f}")
        print(f"   Sharpe Ratio: {sharpe:.2f}" if sharpe else "   Sharpe Ratio: N/A")
        print(f"   Max Drawdown: {max_dd:.2f}%" if max_dd else "   Max Drawdown: N/A")
        
        print(f"\n   📊 TRADE BREAKDOWN:")
        
        # Get trade distribution
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN pnl <= 0 THEN 1 END) as losing_trades,
                AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                AVG(CASE WHEN pnl <= 0 THEN pnl END) as avg_loss,
                MAX(pnl) as max_win,
                MIN(pnl) as max_loss,
                AVG(trade_duration_hours) as avg_duration
            FROM trades 
            WHERE run_id = :run_id
        """), {'run_id': run_id})
        
        stats = result.fetchone()
        total, wins, losses, avg_win, avg_loss, max_win, max_loss, avg_duration = stats
        
        print(f"      Total Trades: {total}")
        print(f"      Winning Trades: {wins} (${avg_win:.2f} avg)")
        print(f"      Losing Trades: {losses} (${avg_loss:.2f} avg)")
        print(f"      Max Win: ${max_win:.2f}")
        print(f"      Max Loss: ${max_loss:.2f}")
        print(f"      Average Duration: {avg_duration:.1f} hours")
        
        # Show recent trades
        print(f"\n   📋 RECENT TRADES:")
        view_trades(run_id)

def interactive_menu():
    """Interactive menu for database exploration"""
    while True:
        print("\n" + "="*60)
        print("🗄️  DATABASE EXPLORER")
        print("="*60)
        print("1. Database Overview")
        print("2. View All Backtest Runs")
        print("3. View Recent Trades")
        print("4. View Strategy Performance")
        print("5. Detailed Analysis (by Run ID)")
        print("6. View Trades for Specific Run")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-6): ").strip()
        
        if choice == '0':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            view_database_overview()
        elif choice == '2':
            view_backtest_runs()
        elif choice == '3':
            view_trades()
        elif choice == '4':
            strategy = input("Enter strategy name (or press Enter for all): ").strip()
            if strategy:
                view_strategy_performance(strategy)
            else:
                view_strategy_performance()
        elif choice == '5':
            run_id = input("Enter run ID: ").strip()
            if run_id:
                view_detailed_trade_analysis(run_id)
        elif choice == '6':
            run_id = input("Enter run ID: ").strip()
            if run_id:
                view_trades(run_id)
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        print("🔍 PostgreSQL/TimescaleDB Database Explorer")
        print("=" * 60)
        
        # Test connection
        engine = connect_to_database()
        with engine.begin() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to: {version.split(',')[0]}")
        
        # Show quick overview
        view_database_overview()
        
        # Start interactive menu
        interactive_menu()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("   Make sure TimescaleDB is running:")
        print("   docker-compose -f config/docker-compose.timescaledb.yml up -d")
