# 🚀 Usage Examples and Scripts

**Complete collection of usage examples, from basic backtesting to advanced live trading**

## 🎯 Quick Start Examples

### Example 1: Basic Backtest

```python
import asyncio
from backtest_ibkr import run_backtest

# Run a basic 1-year backtest on QQQ
asyncio.run(run_backtest(
    symbol="QQQ",
    days=365,
    starting_equity=100000.0,
    output_base="backtests/QQQ"
))
```

### Example 2: Custom Strategy Parameters

```python
import asyncio
from intraday_supertrend_ma_strategy import IntradaySupertrendMA
from brokers.ibkr_manager import ibkr_manager

# Custom parameters for aggressive trading
params = {
    'symbol': 'TSLA',
    'quantity': 50,
    'starting_equity': 50000.0,
    'supertrend_length': 7,           # More sensitive
    'supertrend_multiplier': 2.5,     # Tighter stops
    'stop_loss_pct': 0.03,           # 3% stop loss
    'take_profit_pct': 0.045,        # 4.5% take profit
    'ma_type': 'EMA',                # Exponential MA
}

# Create and test strategy
strategy = IntradaySupertrendMA("TSLA_Aggressive", ibkr_manager, params)

# Test with live data for 10 minutes
asyncio.run(strategy.test_with_ibkr_gateway(
    symbol='TSLA', 
    test_duration_minutes=10
))
```

---

## 📊 Complete Usage Scripts

### Script 1: Multi-Symbol Backtest Comparison

Save as `multi_symbol_backtest.py`:

```python
import asyncio
import os
from datetime import datetime
from backtest_ibkr import run_backtest

async def compare_symbols():
    """
    Compare strategy performance across multiple symbols
    """
    symbols = ['QQQ', 'SPY', 'IWM', 'AAPL']
    results = {}
    
    print("🔄 Running multi-symbol backtest comparison...")
    print("=" * 60)
    
    for symbol in symbols:
        print(f"\n📊 Testing {symbol}...")
        
        try:
            # Run backtest for each symbol
            await run_backtest(
                symbol=symbol,
                days=365,  # 1 year
                starting_equity=100000.0,
                output_base=f"backtests/{symbol}"
            )
            
            # Find the latest results folder
            base_dir = f"backtests/{symbol}"
            if os.path.exists(base_dir):
                folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
                if folders:
                    latest_folder = sorted(folders)[-1]
                    
                    # Read equity curve to get final value
                    equity_file = os.path.join(base_dir, latest_folder, "equity_curve.csv")
                    if os.path.exists(equity_file):
                        import pandas as pd
                        equity_df = pd.read_csv(equity_file)
                        if not equity_df.empty:
                            final_equity = equity_df['equity'].iloc[-1]
                            total_return = ((final_equity - 100000) / 100000) * 100
                            results[symbol] = {
                                'final_equity': final_equity,
                                'total_return_pct': total_return
                            }
            
            print(f"✅ {symbol} backtest completed")
            
        except Exception as e:
            print(f"❌ {symbol} backtest failed: {e}")
            results[symbol] = {'error': str(e)}
    
    # Print summary
    print("\n" + "=" * 60)
    print("📈 BACKTEST COMPARISON RESULTS")
    print("=" * 60)
    print(f"{'Symbol':<8} {'Final Equity':<15} {'Return %':<10} {'Status'}")
    print("-" * 50)
    
    for symbol, result in results.items():
        if 'error' in result:
            print(f"{symbol:<8} {'ERROR':<15} {'N/A':<10} {result['error'][:20]}")
        else:
            final_eq = f"${result['final_equity']:,.0f}"
            return_pct = f"{result['total_return_pct']:+.2f}%"
            print(f"{symbol:<8} {final_eq:<15} {return_pct:<10} {'SUCCESS'}")
    
    print("\n🎯 Best performing symbol:")
    best_symbol = max(
        [s for s in results.keys() if 'error' not in results[s]], 
        key=lambda s: results[s]['total_return_pct'],
        default=None
    )
    if best_symbol:
        best_return = results[best_symbol]['total_return_pct']
        print(f"   {best_symbol}: {best_return:+.2f}% return")

if __name__ == "__main__":
    asyncio.run(compare_symbols())
```

### Script 2: Parameter Optimization

Save as `optimize_parameters.py`:

```python
import asyncio
import pandas as pd
from datetime import datetime
import itertools
from intraday_supertrend_ma_strategy import IntradaySupertrendMA
from brokers.ibkr_manager import ibkr_manager

async def optimize_strategy_parameters():
    """
    Test different parameter combinations to find optimal settings
    """
    # Parameter ranges to test
    param_ranges = {
        'supertrend_length': [7, 10, 14],
        'supertrend_multiplier': [2.5, 3.0, 3.5],
        'stop_loss_pct': [0.015, 0.02, 0.025],
        'take_profit_pct': [0.025, 0.03, 0.035],
    }
    
    # Base parameters
    base_params = {
        'symbol': 'QQQ',
        'quantity': 100,
        'starting_equity': 100000.0,
        'backfill_days': 180,  # 6 months of data
        'ma_type': 'SMA',
    }
    
    print("🔧 Starting parameter optimization...")
    print(f"Testing {len(list(itertools.product(*param_ranges.values())))} combinations")
    print("=" * 60)
    
    results = []
    combination_count = 0
    
    # Test all combinations
    for combination in itertools.product(*param_ranges.values()):
        combination_count += 1
        
        # Create parameter set
        test_params = base_params.copy()
        for i, param_name in enumerate(param_ranges.keys()):
            test_params[param_name] = combination[i]
        
        print(f"\n🧪 Test {combination_count}: ST({test_params['supertrend_length']}, "
              f"{test_params['supertrend_multiplier']}) SL:{test_params['stop_loss_pct']:.1%} "
              f"TP:{test_params['take_profit_pct']:.1%}")
        
        try:
            # Create strategy
            strategy = IntradaySupertrendMA(f"Optimize_{combination_count}", ibkr_manager, test_params)
            
            # Initialize strategy (this loads historical data)
            await strategy.init()
            
            # Simulate trading on historical data
            # Note: This is a simplified version - full backtest would be more complex
            total_trades = len(strategy.trades)
            final_equity = strategy.current_equity
            total_return = ((final_equity - base_params['starting_equity']) / base_params['starting_equity']) * 100
            
            # Calculate win rate
            winning_trades = sum(1 for trade in strategy.trades if trade.get('pnl', 0) > 0)
            win_rate = (winning_trades / total_trades) if total_trades > 0 else 0
            
            # Store results
            result = {
                'combination': combination_count,
                'supertrend_length': test_params['supertrend_length'],
                'supertrend_multiplier': test_params['supertrend_multiplier'],
                'stop_loss_pct': test_params['stop_loss_pct'],
                'take_profit_pct': test_params['take_profit_pct'],
                'total_trades': total_trades,
                'final_equity': final_equity,
                'total_return_pct': total_return,
                'win_rate': win_rate,
                'status': 'SUCCESS'
            }
            
            print(f"   ✅ Trades: {total_trades}, Return: {total_return:+.2f}%, Win Rate: {win_rate:.1%}")
            
        except Exception as e:
            result = {
                'combination': combination_count,
                'error': str(e),
                'status': 'ERROR'
            }
            print(f"   ❌ Error: {e}")
        
        results.append(result)
    
    # Save results to CSV
    results_df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"optimization_results_{timestamp}.csv"
    results_df.to_csv(results_file, index=False)
    
    # Print top results
    print("\n" + "=" * 80)
    print("🏆 OPTIMIZATION RESULTS")
    print("=" * 80)
    
    successful_results = results_df[results_df['status'] == 'SUCCESS']
    if not successful_results.empty:
        # Sort by total return
        top_results = successful_results.nlargest(5, 'total_return_pct')
        
        print("Top 5 parameter combinations by return:")
        print("-" * 80)
        for i, (_, row) in enumerate(top_results.iterrows(), 1):
            print(f"{i}. ST({row['supertrend_length']}, {row['supertrend_multiplier']}) "
                  f"SL:{row['stop_loss_pct']:.1%} TP:{row['take_profit_pct']:.1%}")
            print(f"   Return: {row['total_return_pct']:+.2f}%, Trades: {row['total_trades']}, "
                  f"Win Rate: {row['win_rate']:.1%}")
            print()
        
        # Best overall
        best_result = top_results.iloc[0]
        print("🥇 BEST PARAMETERS:")
        print(f"   SuperTrend Length: {best_result['supertrend_length']}")
        print(f"   SuperTrend Multiplier: {best_result['supertrend_multiplier']}")
        print(f"   Stop Loss: {best_result['stop_loss_pct']:.1%}")
        print(f"   Take Profit: {best_result['take_profit_pct']:.1%}")
        print(f"   Expected Return: {best_result['total_return_pct']:+.2f}%")
    
    print(f"\n📊 Full results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(optimize_strategy_parameters())
```

### Script 3: Live Trading Monitor

Save as `live_trading_monitor.py`:

```python
import asyncio
import time
from datetime import datetime
from intraday_supertrend_ma_strategy import IntradaySupertrendMA
from brokers.ibkr_manager import ibkr_manager

class TradingMonitor:
    """Monitor live trading strategy with real-time updates"""
    
    def __init__(self, strategy):
        self.strategy = strategy
        self.start_time = datetime.now()
        self.last_update = time.time()
        
    def print_status(self):
        """Print current strategy status"""
        current_time = datetime.now()
        runtime = current_time - self.start_time
        
        # Clear screen (optional)
        print("\033[H\033[J", end="")  # ANSI escape codes to clear screen
        
        print("=" * 60)
        print(f"🤖 LIVE TRADING MONITOR - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print(f"📊 Strategy: {self.strategy.name}")
        print(f"📈 Symbol: {self.strategy.symbol}")
        print(f"⏱️ Runtime: {str(runtime).split('.')[0]}")
        print(f"💰 Current Equity: ${self.strategy.current_equity:,.2f}")
        
        # Position info
        if self.strategy.position != 0:
            position_type = "LONG" if self.strategy.position == 1 else "SHORT"
            entry_time = self.strategy.entry_time.strftime('%H:%M:%S') if self.strategy.entry_time else "N/A"
            print(f"📍 Position: {position_type} @ ${self.strategy.entry_price:.2f} (entered {entry_time})")
        else:
            print(f"📍 Position: FLAT (no position)")
        
        # Trade statistics
        total_trades = len(self.strategy.trades)
        if total_trades > 0:
            winning_trades = sum(1 for trade in self.strategy.trades if trade.get('pnl', 0) > 0)
            win_rate = (winning_trades / total_trades) * 100
            total_pnl = sum(trade.get('pnl', 0) for trade in self.strategy.trades)
            
            print(f"📊 Total Trades: {total_trades}")
            print(f"🏆 Win Rate: {win_rate:.1f}%")
            print(f"💵 Total P&L: ${total_pnl:+,.2f}")
            
            # Recent trades
            if len(self.strategy.trades) >= 3:
                print("\n📋 Recent Trades:")
                for trade in self.strategy.trades[-3:]:
                    side = trade.get('side', 'Unknown')
                    pnl = trade.get('pnl', 0)
                    entry_price = trade.get('entry_price', 0)
                    exit_price = trade.get('exit_price', 0)
                    exit_time = trade.get('exit_time', 'Unknown')
                    if hasattr(exit_time, 'strftime'):
                        exit_time = exit_time.strftime('%H:%M:%S')
                    
                    pnl_color = "🟢" if pnl > 0 else "🔴"
                    print(f"   {pnl_color} {side} {entry_price:.2f}→{exit_price:.2f} ${pnl:+.2f} ({exit_time})")
        else:
            print(f"📊 Total Trades: 0 (waiting for signals...)")
        
        print("\n💡 Press Ctrl+C to stop monitoring")
        print("=" * 60)

async def run_live_trading(symbol="QQQ", duration_hours=8):
    """
    Run live trading with monitoring
    
    Args:
        symbol: Symbol to trade
        duration_hours: How long to run (hours)
    """
    # Setup strategy parameters
    params = {
        'symbol': symbol,
        'quantity': 100,
        'starting_equity': 100000.0,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.03,
        'backfill_days': 5,
    }
    
    print(f"🚀 Starting live trading monitor for {symbol}")
    print(f"⏱️ Duration: {duration_hours} hours")
    print(f"💰 Starting equity: ${params['starting_equity']:,.2f}")
    print("🔄 Initializing strategy...")
    
    # Create strategy
    strategy = IntradaySupertrendMA(f"Live_{symbol}", ibkr_manager, params)
    await strategy.init()
    
    # Create monitor
    monitor = TradingMonitor(strategy)
    
    # Connect to IBKR
    print("🔌 Connecting to IBKR Gateway...")
    try:
        if not ibkr_manager.ib.isConnected():
            await ibkr_manager.connect()
        print("✅ Connected to IBKR Gateway")
    except Exception as e:
        print(f"❌ Failed to connect to IBKR: {e}")
        return
    
    # Run trading loop
    end_time = time.time() + (duration_hours * 3600)
    
    try:
        while time.time() < end_time:
            # Update monitor display
            monitor.print_status()
            
            # Test strategy with current market data
            await strategy.test_with_ibkr_gateway(
                symbol=symbol, 
                test_duration_minutes=1  # Check every minute
            )
            
            # Wait before next update
            await asyncio.sleep(60)  # Update every minute
            
    except KeyboardInterrupt:
        print("\n🛑 Trading stopped by user")
    except Exception as e:
        print(f"\n❌ Trading error: {e}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("📈 TRADING SESSION SUMMARY")
    print("=" * 60)
    print(f"💰 Starting Equity: ${params['starting_equity']:,.2f}")
    print(f"💰 Ending Equity: ${strategy.current_equity:,.2f}")
    print(f"📊 Total Trades: {len(strategy.trades)}")
    if strategy.trades:
        total_pnl = sum(trade.get('pnl', 0) for trade in strategy.trades)
        print(f"💵 Total P&L: ${total_pnl:+,.2f}")
        win_rate = sum(1 for trade in strategy.trades if trade.get('pnl', 0) > 0) / len(strategy.trades) * 100
        print(f"🏆 Win Rate: {win_rate:.1f}%")
    print("✅ Session completed")

if __name__ == "__main__":
    # Run live trading for 4 hours
    asyncio.run(run_live_trading(symbol="QQQ", duration_hours=4))
```

---

## 🔧 Utility Scripts

### Script 4: Connection Tester

Save as `test_ibkr_connection.py`:

```python
import asyncio
from ib_insync import IB, Stock

async def test_ibkr_connection():
    """
    Comprehensive IBKR connection test
    """
    print("🔌 IBKR Connection Test")
    print("=" * 40)
    
    # Test different ports
    ports_to_test = [
        (4002, "Gateway Paper Trading"),
        (4001, "Gateway Live Trading"),
        (7497, "TWS Paper Trading"),
        (7496, "TWS Live Trading"),
    ]
    
    for port, description in ports_to_test:
        print(f"\n📡 Testing {description} (port {port})...")
        
        ib = IB()
        try:
            # Try to connect
            await ib.connectAsync('127.0.0.1', port, clientId=999)
            
            if ib.isConnected():
                print(f"✅ Connected successfully!")
                
                # Test account info
                try:
                    accounts = ib.managedAccounts()
                    print(f"📊 Accounts: {accounts}")
                    
                    # Test market data
                    contract = Stock('QQQ', 'SMART', 'USD')
                    ib.qualifyContracts(contract)
                    
                    ticker = ib.reqMktData(contract)
                    await asyncio.sleep(2)  # Wait for data
                    
                    if ticker.last > 0:
                        print(f"📈 QQQ Last Price: ${ticker.last:.2f}")
                        print(f"📊 Bid/Ask: ${ticker.bid:.2f}/${ticker.ask:.2f}")
                    else:
                        print("⚠️ No market data received (may be outside market hours)")
                    
                    ib.cancelMktData(contract)
                    
                except Exception as e:
                    print(f"⚠️ Data test failed: {e}")
                
                # Disconnect
                ib.disconnect()
                print(f"🔌 Disconnected from {description}")
                print(f"🎉 {description} is working correctly!")
                return True  # Found working connection
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
        
        finally:
            if ib.isConnected():
                ib.disconnect()
    
    print("\n" + "=" * 40)
    print("❌ No working IBKR connections found!")
    print("💡 Make sure:")
    print("   - IB Gateway or TWS is running")
    print("   - You're logged in")
    print("   - API is enabled in settings")
    print("   - Correct port is configured")
    return False

if __name__ == "__main__":
    asyncio.run(test_ibkr_connection())
```

### Script 5: Data Integrity Checker

Save as `check_data_integrity.py`:

```python
import pandas as pd
from data.data_manager import DataManager

def check_data_integrity(symbol="QQQ", timeframe="1min"):
    """
    Check the integrity of stored market data
    """
    print(f"🔍 Data Integrity Check for {symbol} ({timeframe})")
    print("=" * 50)
    
    dm = DataManager()
    
    try:
        # Load all data for symbol/timeframe
        df = dm.load_bars(symbol, timeframe)
        
        if df.empty:
            print(f"❌ No data found for {symbol} {timeframe}")
            return
        
        print(f"📊 Total bars: {len(df):,}")
        print(f"📅 Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
        
        # Check for missing columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
        else:
            print(f"✅ All required columns present")
        
        # Check for null values
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            print(f"⚠️ Null values found:")
            for col, count in null_counts.items():
                if count > 0:
                    print(f"   {col}: {count} nulls")
        else:
            print(f"✅ No null values")
        
        # Check OHLC logic
        invalid_ohlc = 0
        if len(df) > 0:
            # High should be >= Low, Open, Close
            high_issues = (df['high'] < df[['low', 'open', 'close']].max(axis=1)).sum()
            # Low should be <= High, Open, Close  
            low_issues = (df['low'] > df[['high', 'open', 'close']].min(axis=1)).sum()
            invalid_ohlc = high_issues + low_issues
        
        if invalid_ohlc > 0:
            print(f"❌ Invalid OHLC bars: {invalid_ohlc}")
        else:
            print(f"✅ OHLC logic is valid")
        
        # Check for duplicate timestamps
        duplicates = df.index.duplicated().sum()
        if duplicates > 0:
            print(f"❌ Duplicate timestamps: {duplicates}")
        else:
            print(f"✅ No duplicate timestamps")
        
        # Check for gaps in data (for minute data)
        if timeframe == "1min" and len(df) > 1:
            time_diffs = df.index.to_series().diff()
            expected_diff = pd.Timedelta(minutes=1)
            large_gaps = (time_diffs > pd.Timedelta(hours=24)).sum()  # Gaps > 1 day
            
            print(f"📈 Data gaps > 24 hours: {large_gaps}")
            if large_gaps > 0:
                print(f"   (This is normal for weekends/holidays)")
        
        # Show sample data
        print(f"\n📋 Sample data (first 3 rows):")
        print(df.head(3).round(2))
        
        print(f"\n📈 Price statistics:")
        print(f"   Highest price: ${df['high'].max():.2f}")
        print(f"   Lowest price: ${df['low'].min():.2f}")
        print(f"   Average volume: {df['volume'].mean():,.0f}")
        
        print(f"\n✅ Data integrity check completed")
        
    except Exception as e:
        print(f"❌ Error checking data: {e}")

if __name__ == "__main__":
    # Check multiple symbols and timeframes
    symbols = ["QQQ", "SPY"]
    timeframes = ["1min", "30min", "3h"]
    
    for symbol in symbols:
        for timeframe in timeframes:
            check_data_integrity(symbol, timeframe)
            print("\n" + "-" * 50 + "\n")
```

---

## 🎮 Interactive Usage Examples

### Jupyter Notebook Example

Create `strategy_analysis.ipynb`:

```python
# Cell 1: Setup
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
from intraday_supertrend_ma_strategy import IntradaySupertrendMA
from backtest_ibkr import run_backtest
import nest_asyncio
nest_asyncio.apply()

# Cell 2: Run backtest
await run_backtest(symbol="QQQ", days=365, starting_equity=100000.0)

# Cell 3: Load and analyze results
import os
base_dir = "backtests/QQQ"
folders = sorted([f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))])
latest_folder = folders[-1]

# Load trades
trades_df = pd.read_csv(f"{base_dir}/{latest_folder}/trades.csv")
equity_df = pd.read_csv(f"{base_dir}/{latest_folder}/equity_curve.csv")

print(f"Total trades: {len(trades_df)}")
print(f"Win rate: {(trades_df['pnl'] > 0).mean():.1%}")
print(f"Average trade: ${trades_df['pnl'].mean():.2f}")

# Cell 4: Plot results
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Equity curve
equity_df['date'] = pd.to_datetime(equity_df.index)
ax1.plot(equity_df.index, equity_df['equity'])
ax1.set_title('Equity Curve')
ax1.set_ylabel('Portfolio Value ($)')

# P&L distribution
trades_df['pnl'].hist(bins=30, ax=ax2)
ax2.set_title('P&L Distribution')
ax2.set_xlabel('Profit/Loss ($)')
ax2.set_ylabel('Frequency')

plt.tight_layout()
plt.show()
```

### Command Line Usage

```bash
# Basic backtest
python backtest_ibkr.py

# Multi-symbol comparison
python multi_symbol_backtest.py

# Parameter optimization
python optimize_parameters.py

# Live trading (4 hours)
python live_trading_monitor.py

# Test IBKR connection
python test_ibkr_connection.py

# Check data quality
python check_data_integrity.py
```

---

## 📱 Mobile/Remote Monitoring

### Email Alerts Setup

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailAlerter:
    def __init__(self, smtp_server, port, username, password):
        self.smtp_server = smtp_server
        self.port = port
        self.username = username
        self.password = password
    
    def send_trade_alert(self, trade_details, recipient):
        """Send email when trade is executed"""
        subject = f"🤖 Trade Alert: {trade_details['side']} {trade_details['symbol']}"
        
        body = f"""
        Trade Executed:
        
        Symbol: {trade_details['symbol']}
        Side: {trade_details['side']}
        Quantity: {trade_details['quantity']}
        Entry Price: ${trade_details['entry_price']:.2f}
        P&L: ${trade_details['pnl']:+.2f}
        
        Account Equity: ${trade_details['current_equity']:,.2f}
        """
        
        # Send email
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            print(f"📧 Trade alert sent to {recipient}")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")

# Usage in strategy:
# emailer = EmailAlerter('smtp.gmail.com', 587, 'your_email@gmail.com', 'your_password')
# emailer.send_trade_alert(trade_details, 'recipient@email.com')
```

---

## 🛠️ Development and Testing

### Unit Testing Example

```python
import unittest
from unittest.mock import Mock
import pandas as pd
from intraday_supertrend_ma_strategy import IntradaySupertrendMA, compute_supertrend

class TestStrategy(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Note: IBKR connection required for testing
        # self.ibkr_broker = IBKRBroker(name="test_broker")
        self.params = {
            'symbol': 'TEST',
            'quantity': 10,
            'starting_equity': 10000.0,
        }
        # self.strategy = IntradaySupertrendMA("Test", self.ibkr_broker, self.params)
    
    def test_supertrend_calculation(self):
        """Test SuperTrend indicator calculation"""
        # Create test data
        test_data = pd.DataFrame({
            'high': [100, 102, 101, 103, 105],
            'low': [98, 100, 99, 101, 103],
            'close': [99, 101, 100, 102, 104]
        })
        
        result = compute_supertrend(test_data, period=3, multiplier=2.0)
        
        # Check result is a pandas Series
        self.assertIsInstance(result, pd.Series)
        # Check length matches input
        self.assertEqual(len(result), len(test_data))
        # Check values are boolean
        self.assertTrue(all(isinstance(x, (bool, type(pd.NA))) for x in result))
    
    def test_position_tracking(self):
        """Test position state management"""
        # Initially flat
        self.assertEqual(self.strategy.position, 0)
        
        # Simulate long entry
        self.strategy.position = 1
        self.strategy.entry_price = 100.0
        
        self.assertEqual(self.strategy.position, 1)
        self.assertEqual(self.strategy.entry_price, 100.0)
    
    def test_market_hours(self):
        """Test market hours filtering"""
        from datetime import time, datetime
        
        # During market hours
        market_time = datetime(2024, 1, 15, 14, 30)  # 2:30 PM
        self.assertTrue(self.strategy.is_market_open(market_time))
        
        # Outside market hours
        after_hours = datetime(2024, 1, 15, 18, 30)  # 6:30 PM
        self.assertFalse(self.strategy.is_market_open(after_hours))

if __name__ == '__main__':
    unittest.main()
```

### Performance Profiling

```python
import cProfile
import pstats
import io
from intraday_supertrend_ma_strategy import IntradaySupertrendMA

def profile_strategy():
    """Profile strategy performance"""
    pr = cProfile.Profile()
    pr.enable()
    
    # Run strategy code here
    # ... strategy execution ...
    
    pr.disable()
    
    # Print stats
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    
    print("🔍 Performance Profile:")
    print(s.getvalue())

# Usage
profile_strategy()
```

---

**These examples provide a comprehensive foundation for using the trading strategy in various scenarios, from basic backtesting to advanced live trading and monitoring. Start with the simpler examples and gradually work your way up to more complex implementations.**
