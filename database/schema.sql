-- Backtesting System with Interactive Brokers API
-- PostgreSQL + TimescaleDB Schema

-- Enable TimescaleDB extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Broker connections table
CREATE TABLE broker_connections (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    broker_name TEXT NOT NULL,
    api_key TEXT,
    api_secret TEXT,
    account_id TEXT,
    status TEXT NOT NULL DEFAULT 'inactive',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Strategies table
CREATE TABLE strategies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    category TEXT,
    parameters JSONB,
    type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indicators table
CREATE TABLE indicators (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parameters JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Strategy-Indicators junction table
CREATE TABLE strategy_indicators (
    strategy_id TEXT NOT NULL,
    indicator_id TEXT NOT NULL,
    PRIMARY KEY (strategy_id, indicator_id),
    FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE,
    FOREIGN KEY (indicator_id) REFERENCES indicators(id) ON DELETE CASCADE
);

-- Backtest requests table
CREATE TABLE backtest_requests (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    date_range_start DATE NOT NULL,
    date_range_end DATE NOT NULL,
    capital DOUBLE PRECISION NOT NULL,
    commission DOUBLE PRECISION DEFAULT 0.0,
    slippage DOUBLE PRECISION DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE RESTRICT
);

-- Market data table (TimescaleDB hypertable)
CREATE TABLE market_data (
    id TEXT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION,
    source TEXT,
    adjusted_close DOUBLE PRECISION,
    dividend DOUBLE PRECISION,
    PRIMARY KEY (timestamp, symbol, timeframe)
);

-- Convert market_data to hypertable
SELECT create_hypertable('market_data', 'timestamp', if_not_exists => TRUE);

-- Backtest results table
CREATE TABLE backtest_results (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    pnl DOUBLE PRECISION,
    win_rate DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    sharpe_ratio DOUBLE PRECISION,
    sortino_ratio DOUBLE PRECISION,
    total_trades INTEGER,
    average_trade_duration DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (request_id) REFERENCES backtest_requests(id) ON DELETE CASCADE
);

-- Trades table
CREATE TABLE trades (
    id TEXT PRIMARY KEY,
    result_id TEXT NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    exit_time TIMESTAMPTZ,
    entry_price DOUBLE PRECISION NOT NULL,
    exit_price DOUBLE PRECISION,
    qty DOUBLE PRECISION NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('long', 'short')),
    profit_loss DOUBLE PRECISION,
    reason_for_entry TEXT,
    reason_for_exit TEXT,
    FOREIGN KEY (result_id) REFERENCES backtest_results(id) ON DELETE CASCADE
);

-- Orders table
CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    trade_id TEXT NOT NULL,
    order_type TEXT NOT NULL,
    price DOUBLE PRECISION,
    qty DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE
);

-- Portfolio snapshots table (TimescaleDB hypertable)
CREATE TABLE portfolio_snapshots (
    id TEXT,
    result_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    equity_value DOUBLE PRECISION NOT NULL,
    cash DOUBLE PRECISION NOT NULL,
    unrealized_pnl DOUBLE PRECISION DEFAULT 0.0,
    realized_pnl DOUBLE PRECISION DEFAULT 0.0,
    margin_used DOUBLE PRECISION DEFAULT 0.0,
    PRIMARY KEY (timestamp, result_id),
    FOREIGN KEY (result_id) REFERENCES backtest_results(id) ON DELETE CASCADE
);

-- Convert portfolio_snapshots to hypertable
SELECT create_hypertable('portfolio_snapshots', 'timestamp', if_not_exists => TRUE);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

CREATE INDEX IF NOT EXISTS idx_broker_connections_user_id ON broker_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_broker_connections_status ON broker_connections(status);

CREATE INDEX IF NOT EXISTS idx_strategies_category ON strategies(category);
CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(type);

CREATE INDEX IF NOT EXISTS idx_backtest_requests_user_id ON backtest_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_requests_strategy_id ON backtest_requests(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtest_requests_symbol ON backtest_requests(symbol);
CREATE INDEX IF NOT EXISTS idx_backtest_requests_status ON backtest_requests(status);

CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timeframe ON market_data(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_market_data_source ON market_data(source);

CREATE INDEX IF NOT EXISTS idx_backtest_results_request_id ON backtest_results(request_id);

CREATE INDEX IF NOT EXISTS idx_trades_result_id ON trades(result_id);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);
CREATE INDEX IF NOT EXISTS idx_trades_side ON trades(side);

CREATE INDEX IF NOT EXISTS idx_orders_trade_id ON orders(trade_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_result_id ON portfolio_snapshots(result_id);

-- Add some useful views
CREATE OR REPLACE VIEW active_strategies AS
SELECT s.*, COUNT(br.id) as backtest_count
FROM strategies s
LEFT JOIN backtest_requests br ON s.id = br.strategy_id
GROUP BY s.id, s.name, s.description, s.category, s.parameters, s.type, s.created_at, s.updated_at;

CREATE OR REPLACE VIEW trading_performance AS
SELECT 
    br.id as request_id,
    br.symbol,
    br.timeframe,
    s.name as strategy_name,
    result.pnl,
    result.win_rate,
    result.max_drawdown,
    result.sharpe_ratio,
    result.total_trades,
    br.created_at
FROM backtest_requests br
JOIN strategies s ON br.strategy_id = s.id
LEFT JOIN backtest_results result ON br.id = result.request_id
WHERE br.status = 'completed';

-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts for the backtesting system';
COMMENT ON TABLE broker_connections IS 'API connections to various brokers (IBKR, etc.)';
COMMENT ON TABLE strategies IS 'Trading strategies with their parameters';
COMMENT ON TABLE indicators IS 'Technical indicators used in strategies';
COMMENT ON TABLE strategy_indicators IS 'Many-to-many relationship between strategies and indicators';
COMMENT ON TABLE backtest_requests IS 'Backtest execution requests';
COMMENT ON TABLE market_data IS 'Historical market data (TimescaleDB hypertable)';
COMMENT ON TABLE backtest_results IS 'Aggregated results from completed backtests';
COMMENT ON TABLE trades IS 'Individual trades executed during backtests';
COMMENT ON TABLE orders IS 'Order details for each trade';
COMMENT ON TABLE portfolio_snapshots IS 'Portfolio value over time (TimescaleDB hypertable)';
