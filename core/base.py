from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd
import json
import os
from datetime import datetime
import uuid

class StrategyBase(ABC):
    """
    Abstract base class for all trading strategies.
    This class defines the interface that both the backtesting
    and live trading engines will use to run a strategy.
    """
    def __init__(self, name: str, broker: 'BrokerBase', params: Dict[str, Any] = None):
        self.name = name
        self.broker = broker
        self.params = params or {}
        
        # Backtest result tracking
        self.equity_curve = []
        self.trades = []
        self.initial_capital = 0
        self.current_equity = 0
        self.start_time = None
        self.end_time = None

    @abstractmethod
    async def init(self):
        """
        Initialize the strategy. Called once before trading starts.
        Use this to set up indicators, load initial data, etc.
        """
        pass

    @abstractmethod
    async def on_bar(self, bar_data: pd.Series):
        """
        Called for each new bar of historical or live data.
        'bar_data' will be a pandas Series with keys like
        'date', 'open', 'high', 'low', 'close', 'volume'.
        """
        pass

    def record_trade(self, entry_time: datetime, exit_time: datetime, symbol: str, 
                    quantity: float, side: str, entry_price: float, exit_price: float, pnl: float):
        """
        Record a completed trade for result tracking.
        """
        trade = {
            "entry_time": entry_time.isoformat(),
            "exit_time": exit_time.isoformat(),
            "symbol": symbol,
            "quantity": quantity,
            "side": side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl
        }
        self.trades.append(trade)

    def update_equity(self, timestamp: datetime, equity: float):
        """
        Update the equity curve with current equity value.
        """
        self.equity_curve.append([timestamp.isoformat(), equity])
        self.current_equity = equity

    def save_backtest_results(self, run_id: str = None) -> str:
        """
        Save backtest results to both JSON file and database.
        Returns the run_id used for the file.
        """
        if run_id is None:
            run_id = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Create backtest_results directory if it doesn't exist
        results_dir = "backtest_results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Calculate summary metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in self.trades)
        
        # Calculate advanced metrics
        sharpe_ratio = 0
        max_drawdown = 0
        
        if len(self.equity_curve) > 1:
            # Calculate Sharpe Ratio (simplified)
            returns = []
            for i in range(1, len(self.equity_curve)):
                prev_equity = float(self.equity_curve[i-1][1])
                curr_equity = float(self.equity_curve[i][1])
                daily_return = (curr_equity - prev_equity) / prev_equity if prev_equity > 0 else 0
                returns.append(daily_return)
            
            if returns:
                avg_return = sum(returns) / len(returns)
                std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
                sharpe_ratio = avg_return / std_return if std_return > 0 else 0
            
            # Calculate Max Drawdown
            peak = float(self.equity_curve[0][1])
            max_drawdown = 0
            for timestamp, equity in self.equity_curve:
                equity_val = float(equity)
                if equity_val > peak:
                    peak = equity_val
                drawdown = (peak - equity_val) / peak if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            max_drawdown *= 100  # Convert to percentage
        
        # Prepare results data
        results = {
            "run_id": run_id,
            "strategy_name": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "initial_capital": self.initial_capital,
            "final_equity": self.current_equity,
            "total_return": self.current_equity - self.initial_capital,
            "total_return_pct": ((self.current_equity - self.initial_capital) / self.initial_capital * 100) if self.initial_capital > 0 else 0,
            "equity_curve": [[timestamp, str(equity)] for timestamp, equity in self.equity_curve],
            "trades": self.trades,
            "summary": {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": total_trades - winning_trades,
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "average_trade_pnl": total_pnl / total_trades if total_trades > 0 else 0
            },
            "parameters": self.params,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown
        }
        
        # Save to JSON file (for backward compatibility)
        filename = f"{run_id}.json"
        filepath = os.path.join(results_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save to database
        try:
            from data.backtest_database import BacktestDatabase
            db = BacktestDatabase()
            db.save_backtest_result(results)
            print(f"Backtest results saved to database: {run_id}")
        except Exception as e:
            print(f"Warning: Could not save to database: {e}")
        
        print(f"Backtest results saved to: {filepath}")
        return run_id

    async def run(self):
        """
        Default run loop for the strategy. Fetches historical data and calls on_bar for each row.
        Enhanced to track results and save them after completion.
        Returns the run_id for tracking.
        """
        await self.init()
        
        print(f"[{self.name}] Fetching historical data for {self.params.get('symbol')}...")
        
        # This uses the broker instance that was passed to the strategy during creation.
        data = await self.broker.get_historical_data(
            symbol=self.params.get('symbol'),
            timeframe=self.params.get('timeframe'),
            start_date=self.params.get('start_date', '2023-01-01'),
            end_date=self.params.get('end_date', '2024-01-01')
        )
        
        if data is None or data.empty:
            print(f"[{self.name}] No data returned. Stopping strategy.")
            return None

        print(f"[{self.name}] Data fetched. Running strategy on {len(data)} bars...")

        # Initialize backtest tracking
        self.start_time = data.index[0] if not data.empty else None
        self.end_time = data.index[-1] if not data.empty else None
        self.initial_capital = self.params.get('initial_capital', 10000)
        self.current_equity = self.initial_capital
        self.equity_curve = []
        self.trades = []

        # Iterate through the historical data and call on_bar for each time step
        for timestamp, bar in data.iterrows():
            # Add timestamp to bar data for strategies to use
            bar_with_ts = bar.copy()
            bar_with_ts['timestamp'] = timestamp
            await self.on_bar(bar_with_ts)
            
            # Update equity curve (assuming current equity is tracked by the strategy)
            self.update_equity(timestamp, self.current_equity)
            
        print(f"[{self.name}] Strategy run complete.")
        
        # Save results and return run_id
        run_id = self.save_backtest_results()
        print(f"[{self.name}] Results saved with run_id: {run_id}")
        return run_id


class BrokerBase(ABC):
    """
    Abstract base class for all broker interfaces.
    This defines a common contract for how a strategy interacts
    with a brokerage, whether it's a live connection or a backtest simulation.
    """
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    async def place_order(
        self, order: Dict[str, Any], stop_loss: float = None, take_profit: float = None
    ) -> Dict[str, Any]:
        """
        Place an order with the broker. This could be a market, limit, or bracket order.
        In a backtest, this will simulate the order execution.
        In live trading, this will send the order to the actual brokerage.
        """
        pass

    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Retrieve account information (e.g., balance, equity).
        In a backtest, this provides the state of the simulated account.
        """
        pass

    @abstractmethod
    async def get_positions(self) -> list[Dict[str, Any]]:
        """
        Retrieve a list of all current positions held.
        """
        pass

    @abstractmethod
    async def get_open_orders(self) -> list[Dict[str, Any]]:
        """
        Retrieve a list of all currently open (non-filled) orders.
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: int) -> Dict[str, Any]:
        """
        Cancel an existing open order by its ID.
        """
        pass

    @abstractmethod
    async def cancel_all_orders(self) -> Dict[str, Any]:
        """
        Cancel all currently open orders.
        """
        pass

    @abstractmethod
    async def get_historical_data(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get historical OHLCV market data for a specific symbol and timeframe.
        """
        pass

    @abstractmethod
    async def stream_market_data(self, symbol: str, on_data: callable, asset_type: str = "stock"):
        """
        Stream real-time market data for a given symbol.
        The `on_data` callback will be called for each incoming tick.
        NOTE: This is primarily used by the live trading engine, not directly by strategies.
        """
        pass 