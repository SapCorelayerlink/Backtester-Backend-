# Polygon.io Integration for Paper Trading

This document describes the Polygon.io integration for the Bactester project, enabling paper trading with real-time market data.

## Overview

The Polygon.io integration provides:
- Real-time market data streaming via WebSocket
- Historical data retrieval via REST API
- Paper trading execution simulator
- Integration with existing strategy framework

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Set your Polygon.io API key in one of these ways:

**Option A: Environment Variable**
```bash
export POLYGON_API_KEY="your_api_key_here"
```

**Option B: Edit config.py**
```python
POLYGON_API_KEY = "your_api_key_here"
```

### 3. Get Polygon.io API Key

1. Sign up at [polygon.io](https://polygon.io)
2. Choose a plan (free tier available)
3. Get your API key from the dashboard

## Configuration

The integration is configured through `config.py`:

```python
# Polygon.io Configuration
POLYGON_API_KEY = "your_api_key_here"
POLYGON_BASE_URL = "https://api.polygon.io"

# Paper Trading Configuration
PAPER_MODE = True
PAPER_STARTING_CASH = 100000

# Trading Configuration
DEFAULT_COMMISSION = 0.0
DEFAULT_SLIPPAGE = 0.0
```

## Components

### 1. Data Provider (`data/polygon_data.py`)

Handles all Polygon.io API interactions:

```python
from data.polygon_data import polygon_data

# Get historical data
df = await polygon_data.get_historical_bars(
    symbol='AAPL',
    from_date=datetime.now() - timedelta(days=30),
    to_date=datetime.now(),
    interval='1D'
)

# Get real-time price
price = await polygon_data.get_real_time_price('AAPL')

# Stream live prices
await polygon_data.stream_live_prices(
    symbols=['AAPL', 'MSFT'],
    on_price_callback=handle_price_update
)
```

### 2. Paper Executor (`brokers/paper_executor.py`)

Simulates order execution and portfolio management:

```python
from brokers.paper_executor import PaperExecutor

executor = PaperExecutor(starting_cash=100000)

# Place an order
order = await executor.place_order(
    symbol='AAPL',
    side='buy',
    quantity=10,
    order_type='market'
)

# Process price updates
await executor.process_price_update(tick_data)

# Get portfolio summary
portfolio = executor.get_portfolio_summary()
```

### 3. Paper Broker (`brokers/paper_broker.py`)

Implements the broker interface for paper trading:

```python
from brokers.paper_broker import PaperBroker

broker = PaperBroker("paper_broker", {'starting_cash': 100000})
await broker.connect()

# Place orders
result = await broker.place_order({
    'symbol': 'AAPL',
    'qty': 10,
    'side': 'buy',
    'order_type': 'market'
})
```

### 4. Paper Trader (`paper_trader.py`)

Main entry point for paper trading:

```bash
python paper_trader.py --symbols AAPL MSFT --strategy simple_paper_strategy --cash 100000
```

## Usage Examples

### 1. Test Integration

```bash
python examples/test_polygon_integration.py
```

### 2. Run Paper Trading

```bash
# Basic usage
python paper_trader.py --symbols AAPL MSFT --strategy simple_paper_strategy

# With custom parameters
python paper_trader.py \
    --symbols AAPL MSFT GOOGL \
    --strategy simple_paper_strategy \
    --cash 50000 \
    --params '{"short_window": 10, "long_window": 30}'
```

### 3. Programmatic Usage

```python
from paper_trader import PaperTrader

# Create trader
trader = PaperTrader(
    symbols=['AAPL', 'MSFT'],
    strategy_name='simple_paper_strategy',
    starting_cash=100000,
    strategy_params={'short_window': 5, 'long_window': 20}
)

# Start trading
await trader.start()

# Get status
status = trader.get_status()
print(f"Equity: ${status['portfolio']['total_equity']:,.2f}")

# Stop trading
await trader.stop()
```

## Strategy Development

### Creating a Paper Trading Strategy

```python
from core.base import StrategyBase
from core.registry import StrategyRegistry

@StrategyRegistry.register("my_strategy")
class MyStrategy(StrategyBase):
    def __init__(self, name: str, broker, params: dict = None):
        super().__init__(name, broker, params)
        # Initialize strategy parameters
        
    async def init(self):
        """Initialize the strategy."""
        pass
        
    async def on_bar(self, bar_data: pd.Series):
        """Called for each new bar of data."""
        symbol = bar_data.get('symbol')
        close_price = bar_data.get('close')
        
        # Your trading logic here
        if self.should_buy(symbol, close_price):
            await self.broker.place_order({
                'symbol': symbol,
                'qty': 10,
                'side': 'buy',
                'order_type': 'market'
            })
```

### Strategy Parameters

Pass parameters to your strategy:

```python
strategy_params = {
    'short_window': 10,
    'long_window': 30,
    'position_size': 100,
    'stop_loss': 0.05
}

trader = PaperTrader(
    symbols=['AAPL'],
    strategy_name='my_strategy',
    strategy_params=strategy_params
)
```

## API Endpoints

The paper trading system can be integrated with the existing API:

### Get Portfolio Status
```http
GET /api/paper/portfolio
```

### Get Trade History
```http
GET /api/paper/trades
```

### Place Order
```http
POST /api/paper/order
{
    "symbol": "AAPL",
    "qty": 10,
    "side": "buy",
    "order_type": "market"
}
```

## Monitoring and Logging

### Log Files
- `paper_trader.log`: Main trading log
- `polygon_data.log`: Data provider log

### Real-time Monitoring
The system provides real-time status updates:

```python
# Get current status
status = trader.get_status()
print(f"Status: {status['status']}")
print(f"Equity: ${status['portfolio']['total_equity']:,.2f}")
print(f"Cash: ${status['portfolio']['cash']:,.2f}")
print(f"Unrealized PnL: ${status['portfolio']['unrealized_pnl']:,.2f}")
```

## Performance Metrics

The system tracks comprehensive performance metrics:

- Total equity and cash
- Unrealized and realized PnL
- Win rate and total trades
- Position details
- Order history

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   ValueError: Please set your Polygon.io API key
   ```
   Solution: Set the `POLYGON_API_KEY` environment variable or update `config.py`

2. **No Data Available**
   ```
   No historical data found for SYMBOL
   ```
   Solution: Check if the symbol exists and you have the appropriate data plan

3. **WebSocket Connection Issues**
   ```
   Error setting up live price streaming
   ```
   Solution: Check your internet connection and API key permissions

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Limitations

1. **Market Hours**: Live streaming only works during market hours
2. **Data Plan**: Some features require paid Polygon.io plans
3. **Rate Limits**: API calls are subject to rate limits
4. **Paper Trading**: This is simulation only, no real money is involved

## Future Enhancements

- [ ] Support for options and futures
- [ ] Advanced order types (stop-loss, take-profit)
- [ ] Risk management features
- [ ] Performance analytics dashboard
- [ ] Integration with other data providers

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Test with the integration test script
4. Consult Polygon.io documentation for API-specific issues
