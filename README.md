# 📈 Intraday SuperTrend MA Trading Strategy

A professional algorithmic trading system that implements a sophisticated intraday strategy using SuperTrend indicators and Moving Averages. This system is designed to work with Interactive Brokers (IBKR) through both TWS (Trader Workstation) and IB Gateway for automated trading and backtesting.

## 🎯 Strategy Overview

The **Intraday SuperTrend MA Strategy** combines two powerful technical indicators:

- **3-Hour SuperTrend**: Provides overall market direction (bullish/bearish)
- **30-Minute Moving Averages**: Generates precise entry and exit signals

### How It Works

1. **Direction Filter**: Uses a 3-hour SuperTrend to determine if the market is bullish (GREEN) or bearish (RED)
2. **Entry Signals**:
   - **Long Entry**: When SuperTrend is GREEN and MA5 > MA9 > MA20 > MA50 (all moving averages in ascending order)
   - **Short Entry**: When SuperTrend is RED and MA5 crosses below MA50
3. **Exit Signals**:
   - **Long Exit**: When price closes below the 9-period moving average
   - **Short Exit**: When price closes above the 9-period moving average

## 🚀 Features

- ✅ **Live Trading** with Interactive Brokers Gateway/TWS
- ✅ **Historical Backtesting** using real IBKR data
- ✅ **Automated Risk Management** with stop-loss and take-profit orders
- ✅ **Real-time Data Processing** with 1-minute bar resolution
- ✅ **SQLite Database** for efficient data storage and retrieval
- ✅ **Comprehensive Logging** and trade tracking
- ✅ **Visual Analytics** with equity curve plotting
- ✅ **Flexible Configuration** for different symbols and parameters

## 📋 Prerequisites

### Software Requirements

1. **Python 3.8 or higher**
2. **Interactive Brokers Account** (paper trading account recommended for testing)
3. **IBKR Gateway or TWS** installed and configured

### Hardware Requirements

- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: At least 1GB free space for data storage
- **Internet**: Stable broadband connection for real-time data

## 🛠️ Installation

### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd Strategy
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
python -c "import pandas, numpy, ib_insync, matplotlib; print('All dependencies installed successfully!')"
```

## 🔧 IBKR Gateway Setup

### For Non-Technical Users: Complete IBKR Setup Guide

#### Step 1: Download and Install IB Gateway

1. Visit [Interactive Brokers Download Center](https://www.interactivebrokers.com/en/trading/ib-api.php)
2. Download **IB Gateway** (recommended) or **TWS**
3. Install following the setup wizard

#### Step 2: Configure IB Gateway

1. **Launch IB Gateway**
2. **Login** with your IBKR credentials
3. **Enable API Access**:
   - In IB Gateway, go to **Configure** → **Settings** → **API** → **Settings**
   - Check **"Enable ActiveX and Socket Clients"**
   - Set **Socket Port** to `4002` (paper trading) or `4001` (live trading)
   - **Important**: Add `127.0.0.1` to **Trusted IPs**
   - Set **Master API Client ID** to `1000` (or any high number)
   - Check **"Read-Only API"** if you only want to backtest (optional)

#### Step 3: Paper Trading Setup (Recommended for Testing)

1. In IB Gateway, select **"Paper Trading"** mode during login
2. This gives you $1,000,000 virtual money to test strategies safely
3. Paper trading uses port `4002` by default

#### Step 4: Verify Connection

The system will automatically try to connect to these ports in order:
- `7497` (TWS Paper Trading)
- `7496` (TWS Live Trading)  
- `4002` (Gateway Paper Trading)
- `4001` (Gateway Live Trading)

## 🎮 Usage

### Quick Start: Running a Backtest

1. **Start IB Gateway** and ensure it's connected
2. **Run the backtest script**:

```bash
python backtest_ibkr.py
```

This will:
- Connect to IBKR Gateway automatically
- Download 5 years of QQQ historical data
- Run the strategy simulation
- Generate results in `backtests/QQQ/[timestamp]/`

### Live Trading Test

To test the strategy with live market data (paper trading recommended):

```python
import asyncio
from intraday_supertrend_ma_strategy import IntradaySupertrendMA
from brokers.ibkr_manager import ibkr_manager

# Create strategy instance
params = {
    'symbol': 'QQQ',
    'quantity': 100,
    'starting_equity': 100000.0
}

strategy = IntradaySupertrendMA("Live Test", ibkr_manager, params)

# Run live test for 5 minutes
asyncio.run(strategy.test_with_ibkr_gateway(symbol='QQQ', test_duration_minutes=5))
```

## ⚙️ Configuration

### Strategy Parameters

The strategy accepts these configurable parameters:

```python
params = {
    # Symbol and Timeframes
    'symbol': 'QQQ',                    # Trading symbol
    'base_timeframe': '1min',           # Base data timeframe
    'ma_timeframe': '30min',            # Moving average timeframe
    'supertrend_timeframe': '3h',       # SuperTrend timeframe
    
    # SuperTrend Settings
    'supertrend_length': 10,            # SuperTrend period
    'supertrend_multiplier': 3.0,       # SuperTrend multiplier
    
    # Moving Average Settings
    'ma_type': 'SMA',                   # 'SMA' or 'EMA'
    'ma5_period': 5,                    # Fast MA period
    'ma9_period': 9,                    # Signal MA period
    'ma20_period': 20,                  # Medium MA period
    'ma50_period': 50,                  # Slow MA period
    
    # Trading Settings
    'quantity': 100,                    # Position size
    'stop_loss_pct': 0.02,             # Stop loss (2%)
    'take_profit_pct': 0.03,           # Take profit (3%)
    'use_bracket_orders': True,         # Use stop/target orders
    'place_market_orders': True,        # Use market vs limit orders
    
    # Risk Management
    'starting_equity': 100000.0,        # Starting capital
    
    # Data Settings
    'backfill_days': 5,                 # Days of historical data
    'persist_resampled': True,          # Save resampled data
    
    # Trading Hours (US Eastern Time)
    'trading_hours': {
        'start': time(9, 30),           # Market open
        'end': time(16, 0)              # Market close
    }
}
```

### Supported Symbols

The strategy works with any US equities, popular choices:
- **QQQ** (Nasdaq ETF) - Default, highly liquid
- **SPY** (S&P 500 ETF) - Large cap focus
- **AAPL** (Apple) - Individual stock example
- **TSLA** (Tesla) - High volatility stock

## 📊 Understanding Results

### Backtest Output

Each backtest creates a timestamped folder with:

1. **`trades.csv`** - Complete trade log with:
   - Entry/exit times and prices
   - Position size and direction (long/short)
   - Profit/loss per trade

2. **`equity_curve.csv`** - Portfolio value over time
3. **`equity_curve.png`** - Visual equity curve chart
4. **`status.txt`** - Execution log and connection details

### Sample Results Interpretation

```
Total trades: 15
Ending equity: 102,350.00
Win Rate: 73.3%
```

This means:
- 15 trades were executed
- $2,350 profit on $100,000 starting capital (2.35% return)
- 11 out of 15 trades were profitable

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. "Unable to connect to IBKR Gateway/TWS"

**Symptoms**: Connection errors when running scripts

**Solutions**:
- ✅ Ensure IB Gateway/TWS is running and logged in
- ✅ Check API settings are enabled (see Setup Guide above)
- ✅ Verify the correct port is being used (4002 for paper, 4001 for live)
- ✅ Add `127.0.0.1` to Trusted IPs in Gateway settings
- ✅ Try different client IDs if you get "client id already in use"

#### 2. "No market data received"

**Symptoms**: Strategy runs but shows no price updates

**Solutions**:
- ✅ Check market hours (9:30 AM - 4:00 PM ET for US stocks)
- ✅ Verify market data subscriptions in your IBKR account
- ✅ Ensure the symbol exists and is tradeable (try QQQ first)

#### 3. "Permission denied" or "Read-only API"

**Symptoms**: Cannot place orders even in paper trading

**Solutions**:
- ✅ Uncheck "Read-Only API" in Gateway settings
- ✅ Ensure paper trading mode is selected for safe testing
- ✅ Restart IB Gateway after changing settings

#### 4. Python Import Errors

**Symptoms**: `ModuleNotFoundError` when running scripts

**Solutions**:
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Or install individually
pip install ib-insync pandas numpy matplotlib
```

### Connection Testing

To test your IBKR connection independently:

```python
from ib_insync import IB

ib = IB()
try:
    ib.connect('127.0.0.1', 4002, clientId=1)  # 4002 for paper trading
    print("✅ Connected successfully!")
    print(f"Account: {ib.managedAccounts()}")
    ib.disconnect()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## ⚠️ Risk Warnings

### Important Disclaimers

1. **Educational Purpose**: This strategy is for educational and research purposes
2. **Past Performance**: Historical results don't guarantee future performance
3. **Market Risk**: All trading involves risk of loss
4. **Paper Trading First**: Always test with paper trading before using real money
5. **Position Sizing**: Never risk more than you can afford to lose

### Best Practices

- 🔒 Start with paper trading to understand the system
- 📊 Monitor performance closely during live trading
- 💰 Use appropriate position sizing (typically 1-2% risk per trade)
- 🕐 Be aware of market hours and holidays
- 📈 Regularly review and adjust parameters based on market conditions

## 🔄 Advanced Usage

### Custom Strategy Development

You can create your own strategies by extending the `StrategyBase` class:

```python
from core.base import StrategyBase
from core.registry import StrategyRegistry

@StrategyRegistry.register("MyCustomStrategy")
class MyCustomStrategy(StrategyBase):
    async def on_bar(self, bar_data):
        # Your custom trading logic here
        pass
```

### Multi-Symbol Trading

Run the strategy on multiple symbols:

```python
symbols = ['QQQ', 'SPY', 'IWM']
for symbol in symbols:
    # Create separate strategy instance for each symbol
    params['symbol'] = symbol
    strategy = IntradaySupertrendMA(f"Strategy_{symbol}", broker, params)
    # Run strategy...
```

## 📚 Complete Documentation

This README provides an overview. For comprehensive documentation:

**📋 [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Complete documentation index**

### Quick Links:
- 🚀 **[QUICK_START.md](QUICK_START.md)** - Get running in 15 minutes
- 🏦 **[IBKR_SETUP_GUIDE.md](IBKR_SETUP_GUIDE.md)** - Detailed IBKR Gateway setup
- ⚙️ **[CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)** - Parameter configuration
- 📊 **[USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)** - Complete usage examples
- ❓ **[FAQ.md](FAQ.md)** - Troubleshooting and common questions
- 🔌 **[test_connection.py](test_connection.py)** - Test your IBKR connection

## 📞 Support

### Getting Help

1. **Check [FAQ.md](FAQ.md)** for common solutions and troubleshooting
2. **Run [test_connection.py](test_connection.py)** to diagnose connection issues
3. **Review the [IBKR_SETUP_GUIDE.md](IBKR_SETUP_GUIDE.md)** for setup problems
4. **Test with paper trading** first

### System Requirements Check

```python
import sys
print(f"Python version: {sys.version}")

try:
    import pandas as pd
    import numpy as np
    import ib_insync
    import matplotlib
    print("✅ All required packages are installed")
except ImportError as e:
    print(f"❌ Missing package: {e}")
```

## 📄 License

This project is provided as-is for educational purposes. Use at your own risk.

---

**Happy Trading! 📈**

*Remember: The best strategy is the one you understand and can execute consistently.*
