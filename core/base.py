from abc import ABC, abstractmethod
from typing import Any, Dict
import pandas as pd

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
    def get_historical_data(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
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