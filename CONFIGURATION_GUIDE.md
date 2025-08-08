# ⚙️ Strategy Configuration Guide

**Complete guide to configuring and customizing the Intraday SuperTrend MA Strategy**

## 🎯 Quick Configuration

For users who want to get started quickly:

```python
# Basic setup for QQQ trading
params = {
    'symbol': 'QQQ',                    # What to trade
    'quantity': 100,                    # How many shares per trade
    'starting_equity': 100000.0,        # Starting capital ($100k)
    'stop_loss_pct': 0.02,             # 2% stop loss
    'take_profit_pct': 0.03,           # 3% take profit
}
```

For detailed customization, read on...

---

## 📊 Symbol and Market Configuration

### Primary Symbol Settings

```python
params = {
    'symbol': 'QQQ',                    # Primary trading symbol
    'base_timeframe': '1min',           # Base data resolution
    'ma_timeframe': '30min',            # Moving average timeframe
    'supertrend_timeframe': '3h',       # SuperTrend timeframe
}
```

#### Recommended Symbols for Different Strategies

| Symbol | Description | Liquidity | Volatility | Best For |
|--------|-------------|-----------|------------|----------|
| **QQQ** | Nasdaq ETF | Very High | Medium | Beginners, consistent trends |
| **SPY** | S&P 500 ETF | Very High | Low-Medium | Conservative trading |
| **IWM** | Russell 2000 ETF | High | Medium-High | Small cap exposure |
| **AAPL** | Apple Inc. | Very High | Medium | Tech sector focus |
| **TSLA** | Tesla Inc. | High | High | High volatility strategies |
| **NVDA** | NVIDIA Corp. | High | High | AI/semiconductor sector |

#### Timeframe Guidelines

**Base Timeframe** (`base_timeframe`):
- **1min**: High resolution, more signals (recommended)
- **5min**: Less noise, fewer signals
- **15min**: Very smooth, limited signals

**Moving Average Timeframe** (`ma_timeframe`):
- **30min**: Default, good balance (recommended)
- **15min**: More sensitive, more trades
- **1h**: Less sensitive, fewer trades

**SuperTrend Timeframe** (`supertrend_timeframe`):
- **3h**: Strong directional filter (recommended)
- **1h**: More frequent direction changes
- **6h** or **1d**: Very stable direction filter

---

## 📈 Technical Indicator Settings

### SuperTrend Configuration

```python
params = {
    'supertrend_length': 10,            # Period for ATR calculation
    'supertrend_multiplier': 3.0,       # Sensitivity multiplier
}
```

#### SuperTrend Parameter Guide

**Length** (`supertrend_length`):
- **5-7**: More sensitive, more signals, more whipsaws
- **10**: Default, balanced (recommended)
- **14-20**: Less sensitive, stronger signals, may miss moves

**Multiplier** (`supertrend_multiplier`):
- **2.0-2.5**: Tight stops, more trades, higher risk
- **3.0**: Default balance (recommended)
- **3.5-4.0**: Wider stops, fewer trades, stronger signals

### Moving Average Configuration

```python
params = {
    'ma_type': 'SMA',                   # 'SMA' or 'EMA'
    'ma5_period': 5,                    # Fast MA (entry signal)
    'ma9_period': 9,                    # Exit signal MA
    'ma20_period': 20,                  # Medium trend MA
    'ma50_period': 50,                  # Slow trend MA
}
```

#### MA Type Comparison

**SMA (Simple Moving Average)**:
- ✅ Smoother, less noise
- ✅ Better for trending markets
- ❌ Slower to react to changes

**EMA (Exponential Moving Average)**:
- ✅ Faster reaction to price changes
- ✅ Better for volatile markets
- ❌ More false signals in choppy markets

#### MA Period Guidelines

**Fast MA (5-period)**:
- **3-5**: Very responsive, more signals
- **5**: Default (recommended)
- **8-10**: Smoother, fewer signals

**Exit MA (9-period)**:
- **7-9**: Tighter exits, smaller profits/losses
- **9**: Default (recommended)
- **12-15**: Wider exits, larger profits/losses

**Trend MAs (20 & 50-period)**:
- Keep these ratios for trend alignment
- Can scale proportionally (e.g., 10, 16, 40, 100)

---

## 💰 Position Sizing and Risk Management

### Basic Position Settings

```python
params = {
    'quantity': 100,                    # Position size in shares
    'starting_equity': 100000.0,        # Starting capital
    'stop_loss_pct': 0.02,             # Stop loss percentage
    'take_profit_pct': 0.03,           # Take profit percentage
}
```

### Advanced Risk Management

#### Dynamic Position Sizing

For risk-based position sizing (2% risk per trade):

```python
def calculate_position_size(account_balance, risk_pct, entry_price, stop_price):
    """
    Calculate position size based on fixed risk percentage
    
    Example: $100k account, 2% risk, $400 stock, $392 stop
    Risk amount = $100k * 0.02 = $2000
    Risk per share = $400 - $392 = $8
    Position size = $2000 / $8 = 250 shares
    """
    risk_amount = account_balance * (risk_pct / 100)
    risk_per_share = abs(entry_price - stop_price)
    position_size = int(risk_amount / risk_per_share)
    return position_size

# Example usage in params
params = {
    'use_dynamic_sizing': True,
    'risk_per_trade_pct': 2.0,         # 2% risk per trade
    'max_position_size': 1000,         # Maximum shares regardless of calculation
}
```

#### Stop Loss and Take Profit Guidelines

**Conservative (Low Risk)**:
```python
params = {
    'stop_loss_pct': 0.015,            # 1.5% stop loss
    'take_profit_pct': 0.025,          # 2.5% take profit
}
```

**Moderate (Balanced)**:
```python
params = {
    'stop_loss_pct': 0.02,             # 2% stop loss (default)
    'take_profit_pct': 0.03,           # 3% take profit (default)
}
```

**Aggressive (Higher Risk)**:
```python
params = {
    'stop_loss_pct': 0.03,             # 3% stop loss
    'take_profit_pct': 0.045,          # 4.5% take profit
}
```

---

## 🏪 Order Management Settings

### Order Types and Execution

```python
params = {
    'place_market_orders': True,        # Market vs Limit orders
    'use_bracket_orders': True,         # Include stop/target automatically
    'order_timeout_seconds': 30,       # Cancel unfilled orders after X seconds
}
```

#### Order Type Selection

**Market Orders** (`place_market_orders: True`):
- ✅ Guaranteed execution
- ✅ Fast fills
- ❌ Price slippage risk
- **Best for**: Liquid stocks (QQQ, SPY, AAPL)

**Limit Orders** (`place_market_orders: False`):
- ✅ Price protection
- ✅ Better fills in volatile markets
- ❌ Risk of no execution
- **Best for**: Less liquid stocks or large positions

#### Bracket Orders

**With Brackets** (`use_bracket_orders: True`):
- ✅ Automatic risk management
- ✅ No need to monitor constantly
- ✅ Faster execution
- **Recommended for**: Most strategies

**Without Brackets** (`use_bracket_orders: False`):
- ✅ More control over exits
- ✅ Can adjust stops/targets dynamically
- ❌ Requires more monitoring
- **Best for**: Active management

---

## ⏰ Trading Hours and Schedule

### Market Hours Configuration

```python
from datetime import time

params = {
    'trading_hours': {
        'start': time(9, 30),           # 9:30 AM ET
        'end': time(16, 0),             # 4:00 PM ET
    }
}
```

#### Different Market Sessions

**Regular Trading Hours (RTH)**:
```python
'trading_hours': {
    'start': time(9, 30),               # 9:30 AM ET
    'end': time(16, 0),                 # 4:00 PM ET
}
```

**Extended Hours (Early + Regular)**:
```python
'trading_hours': {
    'start': time(4, 0),                # 4:00 AM ET (pre-market)
    'end': time(16, 0),                 # 4:00 PM ET
}
```

**Extended Hours (Regular + After)**:
```python
'trading_hours': {
    'start': time(9, 30),               # 9:30 AM ET
    'end': time(20, 0),                 # 8:00 PM ET (after-market)
}
```

**24-Hour Trading** (for forex or crypto):
```python
'trading_hours': {
    'start': time(0, 0),                # Midnight
    'end': time(23, 59),                # 11:59 PM
}
```

---

## 💾 Data Management Settings

### Historical Data Configuration

```python
params = {
    'backfill_days': 5,                 # Days of historical data to load
    'persist_resampled': True,          # Save computed timeframes to DB
    'data_quality_checks': True,       # Validate data before trading
}
```

#### Backfill Guidelines

**Short-term Strategy** (intraday):
```python
'backfill_days': 2                      # Minimal data, faster startup
```

**Standard Strategy** (default):
```python
'backfill_days': 5                      # Good balance
```

**Robust Strategy** (needs lots of history):
```python
'backfill_days': 30                     # More data for stable indicators
```

### Database Configuration

```python
params = {
    'database_path': 'data/market_data.db',  # SQLite database location
    'cleanup_old_data': True,               # Remove data older than X days
    'data_retention_days': 90,              # Keep 90 days of minute data
}
```

---

## 🔧 Advanced Configuration Examples

### Conservative Long-Only Strategy

Perfect for retirement accounts or conservative traders:

```python
conservative_params = {
    # Symbol and timeframes
    'symbol': 'SPY',                    # S&P 500 ETF (less volatile)
    'base_timeframe': '1min',
    'ma_timeframe': '1h',               # Longer timeframe for stability
    'supertrend_timeframe': '6h',       # Very stable direction filter
    
    # Less sensitive indicators
    'supertrend_length': 14,            # Longer period
    'supertrend_multiplier': 3.5,       # Less sensitive
    'ma_type': 'SMA',                   # Smoother than EMA
    'ma5_period': 8,                    # Slower MAs
    'ma9_period': 13,
    'ma20_period': 34,
    'ma50_period': 89,
    
    # Conservative risk management
    'quantity': 50,                     # Smaller positions
    'stop_loss_pct': 0.015,            # Tight stop loss
    'take_profit_pct': 0.02,           # Modest targets
    'starting_equity': 100000.0,
    
    # Long-only (disable short entries)
    'allow_short_trades': False,
    
    # Conservative hours
    'trading_hours': {
        'start': time(10, 0),           # After opening volatility
        'end': time(15, 30),            # Before closing volatility
    }
}
```

### Aggressive High-Frequency Strategy

For experienced traders seeking more action:

```python
aggressive_params = {
    # Volatile symbol
    'symbol': 'TSLA',                   # High volatility
    'base_timeframe': '1min',
    'ma_timeframe': '15min',            # Shorter timeframe
    'supertrend_timeframe': '1h',       # More frequent direction changes
    
    # More sensitive indicators
    'supertrend_length': 7,             # Shorter period
    'supertrend_multiplier': 2.5,       # More sensitive
    'ma_type': 'EMA',                   # Faster response
    'ma5_period': 3,                    # Very fast MAs
    'ma9_period': 7,
    'ma20_period': 15,
    'ma50_period': 30,
    
    # Aggressive risk management
    'quantity': 200,                    # Larger positions
    'stop_loss_pct': 0.025,            # Wider stops for volatility
    'take_profit_pct': 0.04,           # Larger targets
    'starting_equity': 100000.0,
    
    # Extended hours
    'trading_hours': {
        'start': time(8, 0),            # Pre-market
        'end': time(18, 0),             # After-hours
    }
}
```

### Multi-Symbol Portfolio Strategy

Trading multiple symbols with correlation considerations:

```python
portfolio_params = {
    # Multiple symbols
    'symbols': ['QQQ', 'SPY', 'IWM'],   # Tech, Large cap, Small cap
    'correlation_filter': True,         # Avoid correlated trades
    'max_concurrent_positions': 2,     # Limit simultaneous trades
    
    # Position sizing per symbol
    'base_quantity': 100,
    'symbol_weights': {
        'QQQ': 1.0,                    # Full weight
        'SPY': 0.8,                    # 80% weight
        'IWM': 1.2,                    # 120% weight (more volatile)
    },
    
    # Shared settings
    'base_timeframe': '1min',
    'ma_timeframe': '30min',
    'supertrend_timeframe': '3h',
    'starting_equity': 100000.0,
}
```

---

## 🎛️ Parameter Optimization Guidelines

### Systematic Parameter Testing

```python
# Example parameter ranges for optimization
optimization_ranges = {
    'supertrend_length': range(7, 21, 2),       # 7, 9, 11, 13, 15, 17, 19
    'supertrend_multiplier': [2.0, 2.5, 3.0, 3.5, 4.0],
    'ma5_period': range(3, 11),                 # 3 to 10
    'stop_loss_pct': [0.015, 0.02, 0.025, 0.03],
    'take_profit_pct': [0.02, 0.025, 0.03, 0.035, 0.04],
}

# Run backtests for each combination
for st_len in optimization_ranges['supertrend_length']:
    for st_mult in optimization_ranges['supertrend_multiplier']:
        for stop_loss in optimization_ranges['stop_loss_pct']:
            params = {
                'supertrend_length': st_len,
                'supertrend_multiplier': st_mult,
                'stop_loss_pct': stop_loss,
                # ... other parameters
            }
            # Run backtest with these parameters
            # Record results for comparison
```

### Performance Metrics to Track

When optimizing parameters, monitor:

1. **Total Return**: Overall profit/loss
2. **Win Rate**: Percentage of profitable trades
3. **Profit Factor**: Gross profit / Gross loss
4. **Maximum Drawdown**: Largest peak-to-trough decline
5. **Sharpe Ratio**: Risk-adjusted returns
6. **Number of Trades**: Ensure sufficient sample size

---

## ⚠️ Configuration Best Practices

### Start Conservative

1. **Begin with Default Settings**: Understand baseline performance
2. **Test with Paper Trading**: No financial risk while learning
3. **Small Position Sizes**: Start with 10-50 shares
4. **Single Symbol**: Master one before diversifying

### Gradual Optimization

1. **Change One Parameter at a Time**: Isolate the impact
2. **Sufficient Data**: Test on at least 6 months of data
3. **Out-of-Sample Testing**: Reserve recent data for validation
4. **Market Regime Awareness**: Different parameters work in different markets

### Risk Management Priority

1. **Stop Loss is Mandatory**: Never trade without stops
2. **Position Sizing**: Never risk more than 2-3% per trade
3. **Correlation Limits**: Avoid too many similar positions
4. **Maximum Daily Loss**: Set daily loss limits

---

## 📋 Configuration Checklist

Before running your strategy, verify:

- [ ] **Symbol is liquid and tradeable** (check IBKR availability)
- [ ] **Timeframes make sense** (30min MA on 3h ST is typical)
- [ ] **Stop loss and take profit are reasonable** (1-5% range)
- [ ] **Position size fits your account** (not more than 10% of capital per trade)
- [ ] **Market hours match your availability** (strategy needs monitoring)
- [ ] **Backtest shows positive results** (at least 3-6 months of data)
- [ ] **Paper trading is successful** (test before live money)

---

**Remember**: Configuration is an iterative process. Start simple, test thoroughly, and optimize gradually based on results. The best parameters for your strategy depend on your risk tolerance, capital, and market conditions.
