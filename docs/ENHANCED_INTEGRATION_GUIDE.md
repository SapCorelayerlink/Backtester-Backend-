# Enhanced IBKR and Polygon.io Integration Guide

This guide explains how to use the enhanced integration that combines IBKR and Polygon.io with automatic fallback logic for paper trading.

## Overview

The enhanced integration provides:
- **Primary Data Source**: IBKR (when available)
- **Fallback Data Source**: Polygon.io (when IBKR is unavailable)
- **Primary Broker**: IBKR (for live trading)
- **Fallback Broker**: Paper Trading (for simulation)
- **Automatic Fallback**: Seamless switching between data sources and brokers

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Strategies    │    │ Enhanced Broker │    │ Enhanced Data   │
│                 │◄──►│                 │◄──►│ Provider        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   IBKR Broker   │    │  IBKR Provider  │
                       │                 │    │                 │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Paper Broker   │    │ Polygon Provider│
                       │                 │    │                 │
                       └─────────────────┘    └─────────────────┘
```

## Setup Instructions

### 1. Prerequisites

Install required dependencies:

```bash
pip install ib_insync polygon-api-client pandas numpy
```

### 2. IBKR Configuration

#### Option A: Using IBKR Gateway (Recommended for Paper Trading)

1. Download and install IBKR Gateway from Interactive Brokers
2. Configure for Paper Trading
3. Set up the connection in your config:

```python
# config.py
IBKR_HOST = "127.0.0.1"
IBKR_PORT = 4002  # Paper trading port
IBKR_CLIENT_ID = 1
```

#### Option B: Using IBKR TWS

1. Download and install TWS (Trader Workstation)
2. Enable API connections
3. Configure for Paper Trading

### 3. Polygon.io Configuration

1. Sign up for a Polygon.io account
2. Get your API key
3. Add to your config:

```python
# config.py
POLYGON_API_KEY = "your_polygon_api_key_here"
```

### 4. Enhanced Configuration

Create a comprehensive configuration:

```python
# config.py

# IBKR Configuration
IBKR_HOST = "127.0.0.1"
IBKR_PORT = 4002  # Paper trading
IBKR_CLIENT_ID = 1

# Polygon.io Configuration
POLYGON_API_KEY = "your_polygon_api_key_here"

# Enhanced Integration Settings
ENHANCED_CONFIG = {
    'use_ibkr': True,
    'use_polygon': True,
    'paper_trading': True,
    'initial_balance': 100000,
    'max_position_size': 0.1,  # 10% of portfolio
    'stop_loss_pct': 0.02,     # 2% stop loss
    'take_profit_pct': 0.06    # 6% take profit
}
```

## Usage Examples

### 1. Basic Enhanced Strategy Setup

```python
import asyncio
from datetime import datetime, timedelta
from brokers.enhanced_broker import EnhancedBroker
from data.enhanced_data_provider import EnhancedDataProvider
from strategies.enhanced_fibonacci_strategy import EnhancedFibonacciStrategy

async def setup_enhanced_strategy():
    # Initialize enhanced broker
    broker_config = {
        'use_ibkr': True,
        'paper_trading': True,
        'initial_balance': 100000
    }
    
    enhanced_broker = EnhancedBroker("enhanced_broker", broker_config)
    
    # Initialize enhanced data provider
    data_provider = EnhancedDataProvider(
        ibkr_manager=ibkr_manager,  # Your IBKR manager instance
        polygon_api_key="your_polygon_api_key"
    )
    
    # Initialize strategy
    strategy_params = {
        'symbol': 'AAPL',
        'timeframe': '15',
        'quantity': 100,
        'fib_levels': [0.382, 0.5, 0.618],
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.06
    }
    
    strategy = EnhancedFibonacciStrategy("enhanced_fibonacci", enhanced_broker, strategy_params)
    
    # Initialize and run
    await strategy.init()
    
    return strategy, enhanced_broker, data_provider
```

### 2. Running a Backtest

```python
async def run_enhanced_backtest():
    strategy, broker, data_provider = await setup_enhanced_strategy()
    
    # Define backtest period
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Run backtest
    results = await strategy.run_backtest(
        symbol='AAPL',
        start_date=start_date,
        end_date=end_date,
        interval='15'
    )
    
    print(f"Backtest Results:")
    print(f"Total Trades: {results.get('total_trades', 0)}")
    print(f"Win Rate: {results.get('win_rate', 0):.1f}%")
    print(f"Total PnL: ${results.get('total_pnl', 0):.2f}")
    print(f"Return: {results.get('return_percentage', 0):.2f}%")
    
    return results
```

### 3. Live Trading Setup

```python
async def start_live_trading():
    strategy, broker, data_provider = await setup_enhanced_strategy()
    
    # Start live trading
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    await strategy.start_live_trading(symbols, interval='15')
    
    # Keep running
    try:
        while strategy.is_running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await strategy.stop_live_trading()
        print("Live trading stopped")
```

### 4. Monitoring Provider Status

```python
async def monitor_providers():
    data_provider = EnhancedDataProvider(
        ibkr_manager=ibkr_manager,
        polygon_api_key="your_polygon_api_key"
    )
    
    # Check provider status
    status = await data_provider.get_provider_status()
    
    print("Data Provider Status:")
    for provider, info in status.items():
        print(f"  {provider}: {'Available' if info['available'] else 'Unavailable'} ({info['type']})")
    
    # Check broker status
    broker = EnhancedBroker("enhanced_broker", {})
    broker_status = await broker.get_broker_status()
    
    print("\nBroker Status:")
    for broker_type, info in broker_status.items():
        print(f"  {broker_type}: {'Available' if info['available'] else 'Unavailable'} ({info['type']})")
```

## Fallback Behavior

### Data Provider Fallback

1. **Primary**: IBKR data provider
2. **Fallback**: Polygon.io data provider
3. **Automatic**: System automatically switches when primary is unavailable

### Broker Fallback

1. **Primary**: IBKR broker (for live trading)
2. **Fallback**: Paper broker (for simulation)
3. **Manual Switch**: Can manually switch between modes

### Example Fallback Scenarios

```python
# Scenario 1: IBKR available, Polygon available
# Result: Uses IBKR for both data and trading

# Scenario 2: IBKR unavailable, Polygon available
# Result: Uses Polygon for data, Paper for trading

# Scenario 3: IBKR available, Polygon unavailable
# Result: Uses IBKR for both data and trading

# Scenario 4: Both unavailable
# Result: Raises exception - no providers available
```

## Testing the Integration

Run the test script to verify your setup:

```bash
python test_enhanced_integration.py
```

This will test:
- Data provider initialization
- Broker initialization
- Historical data retrieval
- Account information
- Strategy initialization
- Backtest execution
- Broker switching
- Position management

## Troubleshooting

### Common Issues

1. **IBKR Connection Failed**
   - Ensure IBKR Gateway/TWS is running
   - Check port configuration
   - Verify API connections are enabled

2. **Polygon API Errors**
   - Verify API key is correct
   - Check API key permissions
   - Ensure you have sufficient credits

3. **Import Errors**
   - Install required packages: `pip install ib_insync polygon-api-client`
   - Check Python path and module structure

4. **Data Provider Unavailable**
   - Check network connectivity
   - Verify API credentials
   - Review error logs for specific issues

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Provider Testing

```python
# Test IBKR provider
from brokers.ibkr_manager import ibkr_manager
if ibkr_manager.ib.isConnected():
    print("IBKR is connected")
else:
    print("IBKR is not connected")

# Test Polygon provider
from polygon import RESTClient
client = RESTClient("your_api_key")
try:
    bars = client.get_aggs("AAPL", 1, "minute", "2024-01-01", "2024-01-01", limit=1)
    print("Polygon is working")
except Exception as e:
    print(f"Polygon error: {e}")
```

## Performance Considerations

### Data Provider Selection

- **IBKR**: Lower latency, real-time data, but requires connection
- **Polygon**: Higher latency, historical data, but more reliable

### Broker Selection

- **IBKR**: Real trading, but requires account setup
- **Paper**: Simulation only, but always available

### Optimization Tips

1. Use IBKR for live trading when possible
2. Use Polygon for backtesting and historical analysis
3. Implement proper error handling for fallback scenarios
4. Monitor provider status regularly
5. Cache frequently used data

## Advanced Configuration

### Custom Data Provider

```python
from data.enhanced_data_provider import DataProviderBase

class CustomDataProvider(DataProviderBase):
    async def get_historical_bars(self, symbol, from_date, to_date, interval):
        # Your custom implementation
        pass
    
    async def is_available(self):
        # Your availability check
        pass
```

### Custom Broker

```python
from brokers.enhanced_broker import BrokerBase

class CustomBroker(BrokerBase):
    async def place_order(self, order):
        # Your custom implementation
        pass
    
    async def get_account_info(self):
        # Your custom implementation
        pass
```

## Conclusion

The enhanced integration provides a robust, flexible solution for algorithmic trading with automatic fallback capabilities. It ensures your strategies can continue operating even when primary data sources or brokers become unavailable.

For additional support, refer to:
- [IBKR API Documentation](https://interactivebrokers.github.io/tws-api/)
- [Polygon.io API Documentation](https://polygon.io/docs/)
- [Project Documentation](README.md)
