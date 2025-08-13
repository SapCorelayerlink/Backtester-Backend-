import sqlite3
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

class BacktestDatabase:
    """
    Comprehensive database manager for storing all backtest results, strategies, trades, and performance metrics.
    Everything is stored in proper table format for easy querying and analysis.
    """
    
    def __init__(self, db_path: str = "data/backtest_database.db"):
        """Initialize the backtest database with all necessary tables."""
        self.db_path = db_path
        self.engine: Engine | None = None
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_engine()
        self.init_database()

    def _init_engine(self):
        """Initialize optional PostgreSQL engine if env vars are set; otherwise None."""
        pg_host = os.getenv('PG_HOST')
        pg_db = os.getenv('PG_DB')
        pg_user = os.getenv('PG_USER')
        pg_password = os.getenv('PG_PASSWORD', '')
        pg_port = os.getenv('PG_PORT', '5432')
        pg_sslmode = os.getenv('PG_SSLMODE', 'prefer')
        if pg_host and pg_db and pg_user:
            url = f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}?sslmode={pg_sslmode}"
            self.engine = create_engine(url)
    
    def init_database(self):
        """Create all necessary tables if they don't exist."""
        if self.engine and self.engine.url.get_backend_name().startswith('postgresql'):
            with self.engine.begin() as conn:
                # Enable TimescaleDB and create schemas in Postgres
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS timescaledb'))
                # backtest_runs
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS backtest_runs (
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
                # equity_curves as hypertable
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS equity_curves (
                        timestamp TIMESTAMPTZ NOT NULL,
                        run_id TEXT NOT NULL,
                        equity DOUBLE PRECISION NOT NULL,
                        PRIMARY KEY (timestamp, run_id),
                        FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id) ON DELETE CASCADE
                    )
                '''))
                conn.execute(text("SELECT create_hypertable('equity_curves','timestamp', if_not_exists => TRUE)"))
                # trades
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS trades (
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
                # strategies
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS strategies (
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
                # performance_metrics
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id SERIAL PRIMARY KEY,
                        run_id TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value DOUBLE PRECISION NOT NULL,
                        metric_type TEXT NOT NULL,
                        calculated_at TIMESTAMPTZ DEFAULT NOW(),
                        FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id) ON DELETE CASCADE
                    )
                '''))
                # market_data hypertable (if not already created by DataManager)
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS market_data (
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
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timeframe ON market_data (symbol, timeframe)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_equity_curves_run_id ON equity_curves(run_id)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_trades_run_id ON trades(run_id)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_performance_metrics_run_id ON performance_metrics(run_id)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_backtest_runs_strategy ON backtest_runs(strategy_name)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_backtest_runs_symbol ON backtest_runs(symbol)'))
                return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Backtest Runs Table - Main backtest information
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtest_runs (
                    run_id TEXT PRIMARY KEY,
                    strategy_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    initial_capital REAL NOT NULL,
                    final_equity REAL NOT NULL,
                    total_return REAL NOT NULL,
                    total_return_pct REAL NOT NULL,
                    total_trades INTEGER NOT NULL,
                    winning_trades INTEGER NOT NULL,
                    losing_trades INTEGER NOT NULL,
                    win_rate REAL NOT NULL,
                    total_pnl REAL NOT NULL,
                    average_trade_pnl REAL NOT NULL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    parameters TEXT,  -- JSON string of strategy parameters
                    status TEXT DEFAULT 'completed'
                )
            ''')
            
            # 2. Equity Curve Table - Daily equity values
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equity_curves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    equity REAL NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id) ON DELETE CASCADE
                )
            ''')
            
            # 3. Trades Table - Individual trade details
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    pnl REAL NOT NULL,
                    return_pct REAL NOT NULL,
                    trade_duration_hours REAL,
                    FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id) ON DELETE CASCADE
                )
            ''')
            
            # 4. Strategies Table - Strategy definitions and metadata
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    category TEXT,
                    parameters_schema TEXT,  -- JSON schema of parameters
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # 5. Performance Metrics Table - Detailed performance metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_type TEXT NOT NULL,  -- 'ratio', 'percentage', 'currency', 'count'
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id) ON DELETE CASCADE
                )
            ''')
            
            # 6. Market Data Table - Historical price data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp, timeframe)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_equity_curves_run_id ON equity_curves(run_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_run_id ON trades(run_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_performance_metrics_run_id ON performance_metrics(run_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timeframe ON market_data(symbol, timeframe)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_backtest_runs_strategy ON backtest_runs(strategy_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_backtest_runs_symbol ON backtest_runs(symbol)')
            
            conn.commit()
    
    def save_backtest_result(self, result_data: Dict[str, Any]) -> str:
        """
        Save a complete backtest result to the database.
        Returns the run_id that was saved.
        """
        run_id = result_data.get('run_id')
        if not run_id:
            raise ValueError("run_id is required in result_data")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Save main backtest run
            cursor.execute('''
                INSERT OR REPLACE INTO backtest_runs (
                    run_id, strategy_name, symbol, timeframe, start_date, end_date,
                    initial_capital, final_equity, total_return, total_return_pct,
                    total_trades, winning_trades, losing_trades, win_rate,
                    total_pnl, average_trade_pnl, sharpe_ratio, max_drawdown, parameters
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                run_id,
                result_data.get('strategy_name'),
                result_data.get('parameters', {}).get('symbol', 'N/A'),
                result_data.get('parameters', {}).get('timeframe', 'N/A'),
                result_data.get('start_time'),
                result_data.get('end_time'),
                result_data.get('initial_capital', 0),
                result_data.get('final_equity', 0),
                result_data.get('total_return', 0),
                result_data.get('total_return_pct', 0),
                result_data.get('summary', {}).get('total_trades', 0),
                result_data.get('summary', {}).get('winning_trades', 0),
                result_data.get('summary', {}).get('losing_trades', 0),
                result_data.get('summary', {}).get('win_rate', 0),
                result_data.get('summary', {}).get('total_pnl', 0),
                result_data.get('summary', {}).get('average_trade_pnl', 0),
                result_data.get('sharpe_ratio', 0),
                result_data.get('max_drawdown', 0),
                json.dumps(result_data.get('parameters', {}))
            ))
            
            # 2. Save equity curve
            if result_data.get('equity_curve'):
                cursor.execute('DELETE FROM equity_curves WHERE run_id = ?', (run_id,))
                for timestamp, equity in result_data['equity_curve']:
                    cursor.execute('''
                        INSERT INTO equity_curves (run_id, timestamp, equity)
                        VALUES (?, ?, ?)
                    ''', (run_id, timestamp, float(equity)))
            
            # 3. Save trades
            if result_data.get('trades'):
                cursor.execute('DELETE FROM trades WHERE run_id = ?', (run_id,))
                for trade in result_data['trades']:
                    # Calculate trade duration
                    entry_time = datetime.fromisoformat(trade['entry_time'].replace('Z', '+00:00'))
                    exit_time = datetime.fromisoformat(trade['exit_time'].replace('Z', '+00:00'))
                    duration_hours = (exit_time - entry_time).total_seconds() / 3600
                    
                    # Calculate return percentage
                    return_pct = ((trade['exit_price'] - trade['entry_price']) / trade['entry_price']) * 100
                    
                    cursor.execute('''
                        INSERT INTO trades (
                            run_id, entry_time, exit_time, symbol, side, quantity,
                            entry_price, exit_price, pnl, return_pct, trade_duration_hours
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        run_id,
                        trade['entry_time'],
                        trade['exit_time'],
                        trade['symbol'],
                        trade['side'],
                        trade['quantity'],
                        trade['entry_price'],
                        trade['exit_price'],
                        trade['pnl'],
                        return_pct,
                        duration_hours
                    ))
            
            # 4. Save performance metrics
            cursor.execute('DELETE FROM performance_metrics WHERE run_id = ?', (run_id,))
            
            # Basic metrics
            metrics = [
                ('total_return', result_data.get('total_return', 0), 'currency'),
                ('total_return_pct', result_data.get('total_return_pct', 0), 'percentage'),
                ('win_rate', result_data.get('summary', {}).get('win_rate', 0), 'percentage'),
                ('total_pnl', result_data.get('summary', {}).get('total_pnl', 0), 'currency'),
                ('average_trade_pnl', result_data.get('summary', {}).get('average_trade_pnl', 0), 'currency'),
                ('total_trades', result_data.get('summary', {}).get('total_trades', 0), 'count'),
                ('winning_trades', result_data.get('summary', {}).get('winning_trades', 0), 'count'),
                ('losing_trades', result_data.get('summary', {}).get('losing_trades', 0), 'count'),
                ('sharpe_ratio', result_data.get('sharpe_ratio', 0), 'ratio'),
                ('max_drawdown', result_data.get('max_drawdown', 0), 'percentage')
            ]
            
            for metric_name, metric_value, metric_type in metrics:
                cursor.execute('''
                    INSERT INTO performance_metrics (run_id, metric_name, metric_value, metric_type)
                    VALUES (?, ?, ?, ?)
                ''', (run_id, metric_name, metric_value, metric_type))
            
            conn.commit()
        
        return run_id
    
    def get_backtest_result(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a complete backtest result from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get main backtest run
            cursor.execute('SELECT * FROM backtest_runs WHERE run_id = ?', (run_id,))
            run_data = cursor.fetchone()
            
            if not run_data:
                return None
            
            # Get equity curve
            cursor.execute('SELECT timestamp, equity FROM equity_curves WHERE run_id = ? ORDER BY timestamp', (run_id,))
            equity_curve = [[row['timestamp'], row['equity']] for row in cursor.fetchall()]
            
            # Get trades
            cursor.execute('SELECT * FROM trades WHERE run_id = ? ORDER BY entry_time', (run_id,))
            trades = [dict(row) for row in cursor.fetchall()]
            
            # Get performance metrics
            cursor.execute('SELECT metric_name, metric_value, metric_type FROM performance_metrics WHERE run_id = ?', (run_id,))
            metrics = {row['metric_name']: row['metric_value'] for row in cursor.fetchall()}
            
            # Build result dictionary
            result = {
                'run_id': run_data['run_id'],
                'strategy_name': run_data['strategy_name'],
                'start_time': run_data['start_date'],
                'end_time': run_data['end_date'],
                'initial_capital': run_data['initial_capital'],
                'final_equity': run_data['final_equity'],
                'total_return': run_data['total_return'],
                'total_return_pct': run_data['total_return_pct'],
                'equity_curve': equity_curve,
                'trades': trades,
                'parameters': json.loads(run_data['parameters']) if run_data['parameters'] else {},
                'summary': {
                    'total_trades': run_data['total_trades'],
                    'winning_trades': run_data['winning_trades'],
                    'losing_trades': run_data['losing_trades'],
                    'win_rate': run_data['win_rate'],
                    'total_pnl': run_data['total_pnl'],
                    'average_trade_pnl': run_data['average_trade_pnl']
                },
                'sharpe_ratio': run_data['sharpe_ratio'],
                'max_drawdown': run_data['max_drawdown']
            }
            
            return result
    
    def list_backtest_runs(self, strategy_name: Optional[str] = None, symbol: Optional[str] = None) -> List[str]:
        """List all backtest run IDs, optionally filtered by strategy or symbol."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT run_id FROM backtest_runs WHERE 1=1'
            params = []
            
            if strategy_name:
                query += ' AND strategy_name = ?'
                params.append(strategy_name)
            
            if symbol:
                query += ' AND symbol = ?'
                params.append(symbol)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]
    
    def get_backtest_summary(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of backtest results."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM backtest_runs WHERE run_id = ?
            ''', (run_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return dict(row)
    
    def get_strategy_performance(self, strategy_name: str) -> List[Dict[str, Any]]:
        """Get performance history for a specific strategy."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM backtest_runs 
                WHERE strategy_name = ? 
                ORDER BY created_at DESC
            ''', (strategy_name,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trade_history(self, run_id: str) -> List[Dict[str, Any]]:
        """Get detailed trade history for a backtest run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM trades 
                WHERE run_id = ? 
                ORDER BY entry_time
            ''', (run_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def save_market_data(self, symbol: str, timeframe: str, data: pd.DataFrame):
        """Save market data to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for index, row in data.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO market_data 
                    (symbol, timestamp, timeframe, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    index.isoformat(),
                    timeframe,
                    row['Open'],
                    row['High'],
                    row['Low'],
                    row['Close'],
                    row.get('Volume', 0)
                ))
            
            conn.commit()
    
    def get_market_data(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Retrieve market data from the database."""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT timestamp, open, high, low, close, volume
                FROM market_data 
                WHERE symbol = ? AND timeframe = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            '''
            
            df = pd.read_sql_query(query, conn, params=(symbol, timeframe, start_date, end_date))
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            return df
    
    def delete_backtest_run(self, run_id: str) -> bool:
        """Delete a backtest run and all associated data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Delete related data first (foreign key constraints will handle the rest)
            cursor.execute('DELETE FROM equity_curves WHERE run_id = ?', (run_id,))
            cursor.execute('DELETE FROM trades WHERE run_id = ?', (run_id,))
            cursor.execute('DELETE FROM performance_metrics WHERE run_id = ?', (run_id,))
            cursor.execute('DELETE FROM backtest_runs WHERE run_id = ?', (run_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count records in each table
            tables = ['backtest_runs', 'equity_curves', 'trades', 'performance_metrics', 'strategies', 'market_data']
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # Get unique strategies
            cursor.execute('SELECT COUNT(DISTINCT strategy_name) FROM backtest_runs')
            stats['unique_strategies'] = cursor.fetchone()[0]
            
            # Get unique symbols
            cursor.execute('SELECT COUNT(DISTINCT symbol) FROM backtest_runs')
            stats['unique_symbols'] = cursor.fetchone()[0]
            
            # Get total PnL
            cursor.execute('SELECT SUM(total_pnl) FROM backtest_runs')
            stats['total_pnl'] = cursor.fetchone()[0] or 0
            
            return stats 