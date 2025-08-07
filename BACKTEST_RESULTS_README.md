# Enhanced Backtest Results System

This document describes the enhanced backtest results functionality that has been added to the strategy framework.

## Overview

The enhanced system provides:
1. **Automatic result saving** - Backtest results are automatically saved to JSON files
2. **Structured data** - Results include equity curves, trades, and summary metrics
3. **API endpoints** - RESTful endpoints to retrieve and list results
4. **Frontend visualization** - HTML interface with Chart.js for result visualization

## New Features

### 1. Enhanced StrategyBase Class

The `StrategyBase` class now includes result tracking capabilities:

- **Equity curve tracking** - Records equity values over time
- **Trade recording** - Captures all trades with entry/exit details
- **Automatic result saving** - Saves results to JSON files after backtest completion

### 2. New API Endpoints

#### GET `/api/v1/strategies/results`
Lists all available backtest result run IDs.

**Response:**
```json
{
  "run_ids": ["MACrossover_AAPL_2023-01-01_2023-12-31_20241201_143022_abc12345"]
}
```

#### GET `/api/v1/strategies/results/{run_id}`
Retrieves detailed backtest results for a specific run ID.

**Response:**
```json
{
  "run_id": "MACrossover_AAPL_2023-01-01_2023-12-31_20241201_143022_abc12345",
  "strategy_name": "MACrossover",
  "start_time": "2023-01-01T00:00:00",
  "end_time": "2023-12-31T23:59:59",
  "initial_capital": 10000.0,
  "final_equity": 11500.0,
  "total_return": 1500.0,
  "total_return_pct": 15.0,
  "equity_curve": [
    ["2023-01-01T00:00:00", 10000.0],
    ["2023-01-02T00:00:00", 10050.0],
    ...
  ],
  "trades": [
    {
      "entry_time": "2023-01-15T00:00:00",
      "exit_time": "2023-01-20T00:00:00",
      "symbol": "AAPL",
      "quantity": 1.0,
      "side": "buy",
      "entry_price": 150.0,
      "exit_price": 155.0,
      "pnl": 5.0
    }
  ],
  "summary": {
    "total_trades": 25,
    "winning_trades": 15,
    "losing_trades": 10,
    "win_rate": 60.0,
    "total_pnl": 1500.0,
    "average_trade_pnl": 60.0
  },
  "parameters": {
    "symbol": "AAPL",
    "timeframe": "1d",
    "initial_capital": 10000,
    "n1": 10,
    "n2": 30,
    "stop_loss_pct": 0.05
  }
}
```

### 3. Frontend Interface

#### GET `/backtest-report`
Serves the HTML frontend for visualizing backtest results.

**Features:**
- Dropdown to select from available backtest runs
- Summary cards showing key metrics
- Interactive equity curve chart using Chart.js
- Detailed trades table
- Responsive design

## Usage

### Running a Backtest

1. **Using the existing backtest endpoint:**
   ```
   GET /api/v1/broker/{broker_name}/backtest?strategy_name=MACrossover&symbol=AAPL&start_date=2023-01-01&end_date=2023-12-31
   ```

2. **Using the strategy run method:**
   ```python
   strategy = MACrossover(name="MyStrategy", broker=broker, params={...})
   run_id = await strategy.run()
   ```

### Viewing Results

1. **List available results:**
   ```
   GET /api/v1/strategies/results
   ```

2. **Get specific results:**
   ```
   GET /api/v1/strategies/results/{run_id}
   ```

3. **View in browser:**
   ```
   GET /backtest-report
   ```

### File Structure

Results are saved in the `backtest_results/` directory:

```
backtest_results/
├── MACrossover_AAPL_2023-01-01_2023-12-31_20241201_143022_abc12345.json
├── MACrossover_AAPL_2023-06-01_2024-06-01_20241201_144530_def67890.json
└── ...
```

## Implementation Details

### StrategyBase Enhancements

The `StrategyBase` class now includes:

- `equity_curve` - List of [timestamp, equity] pairs
- `trades` - List of trade dictionaries
- `record_trade()` - Method to record completed trades
- `update_equity()` - Method to update equity curve
- `save_backtest_results()` - Method to save results to JSON

### MACrossover Strategy Updates

The MACrossover strategy has been enhanced to:

- Track positions and entry/exit prices
- Implement stop-loss functionality
- Record trades when positions are closed
- Update equity based on trade PnL

### API Integration

The existing backtest endpoint now:

1. Runs the backtest using the `backtesting` library
2. Extracts equity curve and trades from backtest stats
3. Creates a strategy instance to use the new result saving
4. Saves structured JSON results alongside HTML reports

## Testing

Run the test script to verify functionality:

```bash
python test_backtest_results.py
```

This will:
1. Create a strategy instance
2. Run a backtest
3. Verify results are saved
4. Display summary information

## Future Enhancements

Potential improvements:
- Add more chart types (drawdown, rolling returns)
- Export results to CSV/Excel
- Add result comparison features
- Implement result archiving and cleanup
- Add email notifications for completed backtests 