# 🚀 Bactester Setup Guide

This guide explains how to set up and run the Bactester trading backtesting system from scratch.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: 3.8 or higher
- **Node.js**: 18 or higher (for frontend)
- **Docker**: For TimescaleDB database
- **Git**: For cloning the repository

### Required Software
1. **Python 3.8+**: Download from [python.org](https://python.org)
2. **Node.js 18+**: Download from [nodejs.org](https://nodejs.org)
3. **Docker Desktop**: Download from [docker.com](https://docker.com)
4. **Git**: Download from [git-scm.com](https://git-scm.com)

## 🛠️ Installation Steps

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd bactester
```

### Step 2: Set Up Python Environment
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Set Up Database (TimescaleDB)
```bash
# Navigate to config directory
cd config

# Start TimescaleDB using Docker
docker-compose -f docker-compose.timescaledb.yml up -d

# Verify database is running
docker ps
```

**Database Details:**
- **Host**: localhost
- **Port**: 5432
- **Database**: bactester
- **Username**: bactester
- **Password**: bactester

### Step 4: Set Up Frontend (Optional)
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Build frontend (for production)
npm run build

# Or run in development mode
npm run dev
```

### Step 5: Configure API Keys (Optional)
If you want to use live data sources, set up API keys:

```bash
# Create environment file
cp .env.example .env

# Edit .env file with your API keys
# POLYGON_API_KEY=your_polygon_api_key_here
# IBKR_HOST=localhost
# IBKR_PORT=4001
```

## 🎯 How to Run the System

### Option 1: FastAPI Backend Server
```bash
# Start the main API server
python -m api.main

# Server will be available at:
# - API: http://localhost:8000
# - Dashboard: http://localhost:8000/dashboard
# - API Docs: http://localhost:8000/docs
```

### Option 2: Test Individual Strategies
```bash
# Test RSI + VWAP Strategy (4-hour timeframe)
python test_rsi_vwap_simple.py

# Test Turtle Strategy (1-hour timeframe)
python test_turtle_strategy.py

# View strategy timeframes summary
python strategy_timeframes_summary.py
```

### Option 3: Paper Trading
```bash
# Run paper trading with sample strategy
python paper_trader.py --symbols AAPL MSFT --strategy simple_paper_strategy
```

### Option 4: Database Management
```bash
# Reset database (if needed)
python reset_database.py

# View database data
python view_database_data.py
```

### Option 5: Frontend Development
```bash
# Start frontend development server
cd frontend
npm run dev

# Frontend will be available at: http://localhost:5173
```

## 📊 Available Strategies

The system includes 5 pre-configured strategies with specific timeframes:

1. **Turtle Trend Breakout Strategy** - 1-hour bars (intraday)
2. **Bollinger Band & 5-EMA Combined Strategy** - Flexible timeframe
3. **RSI-VWAP Strategy** - 4-hour bars
4. **Dynamic Support/Resistance Trend Strategy** - 4-hour bars
5. **Swing Failure Pattern (SFP) Strategy** - 4-hour bars

## 🗄️ Database Schema

The system uses TimescaleDB with the following tables:
- `backtest_runs` - Backtest execution records
- `trades` - Individual trade details
- `equity_curves` - Portfolio equity over time
- `performance_metrics` - Calculated performance metrics
- `strategies` - Strategy metadata
- `market_data` - Historical market data

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
PG_HOST=localhost
PG_PORT=5432
PG_DB=bactester
PG_USER=bactester
PG_PASSWORD=bactester
PG_SSLMODE=prefer

# API Keys (optional)
POLYGON_API_KEY=your_key_here
IBKR_HOST=localhost
IBKR_PORT=4001
```

### Strategy Parameters
Each strategy can be configured with different parameters:
- Timeframes (1h, 4h, 1d)
- Risk management settings
- Technical indicator parameters
- Position sizing rules

## 🧪 Testing

### Quick System Test
```bash
# Test database connection
python -c "from data.backtest_database import BacktestDatabase; db = BacktestDatabase(); print('Database OK')"

# Test strategy loading
python -c "from strategies.rsi_vwap_strategy import RSI_VWAPStrategy; print('Strategy OK')"

# Test broker
python -c "from brokers.paper_broker import PaperBroker; print('Broker OK')"
```

### Run All Tests
```bash
# Test all strategies
python test_all_strategies.py

# Test trade logging
python test_trade_logging_simple.py
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check if TimescaleDB is running
   docker ps
   
   # Restart database
   docker-compose -f config/docker-compose.timescaledb.yml restart
   ```

2. **Python Import Errors**
   ```bash
   # Make sure you're in the project root
   cd /path/to/bactester
   
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

3. **Port Already in Use**
   ```bash
   # Check what's using port 8000
   netstat -ano | findstr :8000  # Windows
   lsof -i :8000                 # macOS/Linux
   ```

4. **Docker Issues**
   ```bash
   # Restart Docker Desktop
   # Then restart TimescaleDB
   docker-compose -f config/docker-compose.timescaledb.yml down
   docker-compose -f config/docker-compose.timescaledb.yml up -d
   ```

### Reset Everything
```bash
# Stop all services
docker-compose -f config/docker-compose.timescaledb.yml down

# Remove database volume
docker volume rm bactester_timescale-data

# Restart fresh
docker-compose -f config/docker-compose.timescaledb.yml up -d
python reset_database.py
```

## 📈 Usage Examples

### Example 1: Run RSI + VWAP Strategy
```bash
# This will:
# 1. Generate sample 4-hour data
# 2. Run the RSI + VWAP strategy
# 3. Save trades to database
# 4. Display results
python test_rsi_vwap_simple.py
```

### Example 2: View Database Results
```bash
# Interactive database explorer
python view_database_data.py

# Choose options:
# 1. Database Overview
# 2. View All Backtest Runs
# 3. View Recent Trades
# 4. View Strategy Performance
```

### Example 3: Start Full System
```bash
# Terminal 1: Start database
cd config && docker-compose -f docker-compose.timescaledb.yml up -d

# Terminal 2: Start API server
python -m api.main

# Terminal 3: Start frontend (optional)
cd frontend && npm run dev
```

## 🔒 Security Notes

- Default database credentials are for development only
- Change passwords for production use
- API keys should be stored securely
- Use environment variables for sensitive data

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs (when server is running)
- **Strategy Documentation**: See individual strategy files in `strategies/`
- **Database Schema**: See `database/schema.sql`
- **Configuration**: See `config.py` and `config/` directory

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Check the logs in the `logs/` directory
4. Ensure database is running and accessible

---

**Happy Trading! 🎯**
