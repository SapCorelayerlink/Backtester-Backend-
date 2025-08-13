#!/usr/bin/env python3
"""
Reset PostgreSQL/TimescaleDB database with correct schema
"""

import os
from sqlalchemy import create_engine, text

# Set PostgreSQL environment variables
os.environ['PG_HOST'] = 'localhost'
os.environ['PG_PORT'] = '5432'
os.environ['PG_DB'] = 'bactester'
os.environ['PG_USER'] = 'bactester'
os.environ['PG_PASSWORD'] = 'bactester'
os.environ['PG_SSLMODE'] = 'prefer'

def reset_database():
    """Reset the database with correct schema"""
    print("🔄 Resetting PostgreSQL/TimescaleDB database...")
    
    # Create engine
    url = f"postgresql+psycopg2://bactester:bactester@localhost:5432/bactester?sslmode=prefer"
    engine = create_engine(url)
    
    with engine.begin() as conn:
        print("   Dropping existing tables...")
        
        # Drop tables in correct order (respecting foreign keys)
        tables_to_drop = [
            'market_data',
            'equity_curves', 
            'trades',
            'performance_metrics',
            'strategies',
            'backtest_runs'
        ]
        
        for table in tables_to_drop:
            try:
                conn.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
                print(f"   ✓ Dropped {table}")
            except Exception as e:
                print(f"   ⚠️  Could not drop {table}: {e}")
        
        print("\n   Creating new tables...")
        
        # Create backtest_runs table
        conn.execute(text('''
            CREATE TABLE backtest_runs (
                run_id TEXT PRIMARY KEY,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                start_date TIMESTAMPTZ NOT NULL,
                end_date TIMESTAMPTZ NOT NULL,
                initial_capital DOUBLE PRECISION NOT NULL,
                final_equity DOUBLE PRECISION NOT NULL,
                total_return DOUBLE PRECISION NOT NULL,
                total_return_pct DOUBLE PRECISION NOT NULL,
                total_trades INTEGER NOT NULL,
                winning_trades INTEGER NOT NULL,
                losing_trades INTEGER NOT NULL,
                win_rate DOUBLE PRECISION NOT NULL,
                total_pnl DOUBLE PRECISION NOT NULL,
                average_trade_pnl DOUBLE PRECISION NOT NULL,
                sharpe_ratio DOUBLE PRECISION,
                max_drawdown DOUBLE PRECISION,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                parameters TEXT,
                status TEXT DEFAULT 'completed'
            )
        '''))
        print("   ✓ Created backtest_runs")
        
        # Create equity_curves as hypertable
        conn.execute(text('''
            CREATE TABLE equity_curves (
                timestamp TIMESTAMPTZ NOT NULL,
                run_id TEXT NOT NULL,
                equity DOUBLE PRECISION NOT NULL,
                PRIMARY KEY (timestamp, run_id),
                FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id) ON DELETE CASCADE
            )
        '''))
        conn.execute(text("SELECT create_hypertable('equity_curves','timestamp', if_not_exists => TRUE)"))
        print("   ✓ Created equity_curves hypertable")
        
        # Create trades table
        conn.execute(text('''
            CREATE TABLE trades (
                id SERIAL PRIMARY KEY,
                run_id TEXT NOT NULL,
                entry_time TIMESTAMPTZ NOT NULL,
                exit_time TIMESTAMPTZ NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity DOUBLE PRECISION NOT NULL,
                entry_price DOUBLE PRECISION NOT NULL,
                exit_price DOUBLE PRECISION NOT NULL,
                pnl DOUBLE PRECISION NOT NULL,
                return_pct DOUBLE PRECISION NOT NULL,
                trade_duration_hours DOUBLE PRECISION,
                FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id) ON DELETE CASCADE
            )
        '''))
        print("   ✓ Created trades")
        
        # Create strategies table
        conn.execute(text('''
            CREATE TABLE strategies (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                category TEXT,
                parameters_schema TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE
            )
        '''))
        print("   ✓ Created strategies")
        
        # Create performance_metrics table
        conn.execute(text('''
            CREATE TABLE performance_metrics (
                id SERIAL PRIMARY KEY,
                run_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value DOUBLE PRECISION NOT NULL,
                metric_type TEXT NOT NULL,
                calculated_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id) ON DELETE CASCADE
            )
        '''))
        print("   ✓ Created performance_metrics")
        
        # Create market_data hypertable
        conn.execute(text('''
            CREATE TABLE market_data (
                timestamp TIMESTAMPTZ NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                open DOUBLE PRECISION NOT NULL,
                high DOUBLE PRECISION NOT NULL,
                low DOUBLE PRECISION NOT NULL,
                close DOUBLE PRECISION NOT NULL,
                volume BIGINT,
                PRIMARY KEY (timestamp, symbol, timeframe)
            )
        '''))
        conn.execute(text("SELECT create_hypertable('market_data','timestamp', if_not_exists => TRUE)"))
        print("   ✓ Created market_data hypertable")
        
        print("\n   Creating indexes...")
        
        # Create indexes
        indexes = [
            ('idx_market_data_symbol_timeframe', 'market_data (symbol, timeframe)'),
            ('idx_equity_curves_run_id', 'equity_curves(run_id)'),
            ('idx_trades_run_id', 'trades(run_id)'),
            ('idx_trades_symbol', 'trades(symbol)'),
            ('idx_performance_metrics_run_id', 'performance_metrics(run_id)'),
            ('idx_backtest_runs_strategy', 'backtest_runs(strategy_name)'),
            ('idx_backtest_runs_symbol', 'backtest_runs(symbol)')
        ]
        
        for index_name, table_columns in indexes:
            try:
                conn.execute(text(f'CREATE INDEX {index_name} ON {table_columns}'))
                print(f"   ✓ Created {index_name}")
            except Exception as e:
                print(f"   ⚠️  Could not create {index_name}: {e}")
    
    print("\n✅ Database reset completed successfully!")
    print("   PostgreSQL/TimescaleDB is ready for RSI + VWAP Strategy testing")

if __name__ == "__main__":
    try:
        reset_database()
    except Exception as e:
        print(f"\n❌ Database reset failed: {e}")
        print("   Make sure TimescaleDB is running:")
        print("   docker-compose -f config/docker-compose.timescaledb.yml up -d")
        import traceback
        traceback.print_exc()
