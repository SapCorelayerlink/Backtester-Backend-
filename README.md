# Bactester - Advanced Trading Backtesting System

A comprehensive trading backtesting system with Interactive Brokers (IBKR) and Polygon.io integration, real-time data processing, paper trading, and advanced strategy testing capabilities.

## 🏗️ Project Structure

```
Bactester/
├── api/                    # FastAPI backend server
│   ├── main.py            # API endpoints and WebSocket
│   └── templates/         # HTML templates
├── brokers/               # Broker integrations
│   ├── ibkr_broker.py    # IBKR API wrapper
│   ├── ibkr_manager.py   # IBKR connection manager
│   ├── paper_broker.py   # Paper trading broker
│   └── paper_executor.py # Paper trading executor
├── core/                  # Core framework
│   ├── base.py           # Strategy and Broker base classes
│   ├── lock.py           # Database locking mechanism
│   └── registry.py       # Strategy registry
├── data/                  # Data management
│   ├── data_manager.py   # Market data storage/retrieval
│   ├── backtest_database.py # Backtest results storage
│   └── polygon_data.py   # Polygon.io data provider
├── database/              # Database schemas
│   └── schema.sql        # PostgreSQL/TimescaleDB schema
├── strategies/            # Trading strategies
│   ├── sample_strategy.py
│   ├── macrossover_strategy.py
│   ├── Supertrend.py
│   ├── rsi_vwap_strategy.py
│   ├── Support Resiatance .py
│   ├── Turtle.py
│   ├── Bollinger + 5EMA.py
│   ├── SwingFailure.py
│   ├── intraday_supertrend_ma_strategy.py
│   └── simple_paper_strategy.py
├── frontend/              # React/Vite frontend
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── setup_guide/           # Setup and installation files
│   ├── SETUP_GUIDE.md    # Complete setup instructions
│   ├── QUICK_COMMANDS.md # Quick reference commands
│   ├── quick_start.py    # Interactive setup script
│   ├── start_bactester.bat # Windows startup script
│   └── start_bactester.sh # macOS/Linux startup script
├── test_scripts/          # Strategy testing scripts
│   ├── test_rsi_vwap_simple.py
│   ├── test_turtle_strategy.py
│   ├── test_all_strategies.py
│   ├── test_trade_logging_simple.py
│   └── strategy_timeframes_summary.py
├── utility_scripts/       # Database and utility scripts
│   ├── reset_database.py
│   └── view_database_data.py
├── tests/                 # Unit tests
├── scripts/               # Utility scripts
├── config/                # Configuration files
│   └── docker-compose.timescaledb.yml
├── docs/                  # Documentation
├── examples/              # Example scripts and tests
├── logs/                  # Log files
├── paper_trader.py        # Paper trading entry point
├── config.py              # Configuration settings
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### 🎯 Easiest Way (Recommended)
**Windows Users:**
```bash
# Double-click or run:
setup_guide/start_bactester.bat
```

**macOS/Linux Users:**
```bash
# Make executable and run:
chmod +x setup_guide/start_bactester.sh
./setup_guide/start_bactester.sh
```

**Manual Setup:**
```bash
# Run the interactive setup script:
python setup_guide/quick_start.py
```

### 📋 Detailed Setup

#### Option 1: IBKR Integration (Live Trading)
#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Start TimescaleDB
```bash
cd config
docker-compose -f docker-compose.timescaledb.yml up -d
```

#### 3. Start IBKR Gateway
- Launch IBKR Gateway on port 4001
- Enable API connections

#### 4. Start the API Server
```bash
python -m api.main
```

#### 5. Access the System
- API: http://localhost:8000
- Dashboard: http://localhost:8000/dashboard
- API Docs: http://localhost:8000/docs

#### Option 2: Polygon.io Paper Trading
#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Setup Polygon.io API Key
```bash
python scripts/setup_polygon.py
```

#### 3. Test Integration
```bash
python examples/test_polygon_integration.py
```

#### 4. Run Paper Trading
```bash
python paper_trader.py --symbols AAPL MSFT --strategy simple_paper_strategy
```

## 🔧 Features

- **IBKR Integration**: Real-time data and order execution
- **Polygon.io Integration**: Market data and paper trading
- **Paper Trading**: Risk-free strategy testing with real market data
- **TimescaleDB**: Optimized time-series data storage
- **Multiple Strategies**: 9+ pre-built trading strategies
- **Backtesting Engine**: Comprehensive strategy testing
- **REST API**: Full API for automation
- **WebSocket**: Real-time updates
- **Modern Frontend**: React-based dashboard

## 📊 Supported Strategies

- RSI + VWAP Strategy
- Support & Resistance Strategy
- Turtle Trading Strategy
- Bollinger Bands + 5EMA Strategy
- Swing Failure Pattern Strategy
- Supertrend Strategy
- Moving Average Crossover
- Intraday Supertrend MA Strategy
- Simple Paper Trading Strategy (Polygon.io)

## 🗄️ Database

- **TimescaleDB**: For market data (hypertables)
- **PostgreSQL**: For backtest results and metadata
- **Automatic Schema**: Complete database setup included

## 📚 Documentation

- **📖 Complete Setup Guide**: [setup_guide/SETUP_GUIDE.md](setup_guide/SETUP_GUIDE.md) - Detailed installation and configuration instructions
- **⚡ Quick Commands**: [setup_guide/QUICK_COMMANDS.md](setup_guide/QUICK_COMMANDS.md) - Quick reference for common commands
- **🎯 Quick Start Script**: `setup_guide/quick_start.py` - Interactive setup and testing
- **📁 Docs Directory**: See `docs/` directory for additional guides:
  - IBKR Configuration
  - Polygon.io Integration Guide
  - Strategy Development
  - API Reference
  - Usage Examples

## 🔒 Security

- Database connection pooling
- API authentication ready
- Secure broker connections
- Environment variable configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your strategy to `strategies/`
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details
