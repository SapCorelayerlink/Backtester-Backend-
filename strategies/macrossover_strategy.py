import pandas as pd
from core.base import StrategyBase
from core.registry import StrategyRegistry

@StrategyRegistry.register("MACrossover")
class MACrossover(StrategyBase):
    """
    A Moving Average Crossover strategy adapted for the custom framework.
    """
    def __init__(self, name: str, broker: 'BrokerBase', params: dict = None):
        super().__init__(name, broker, params)
        self.n1 = self.params.get('n1', 10)  # Short-term window
        self.n2 = self.params.get('n2', 30)  # Long-term window
        self.symbol = self.params.get('symbol', 'AAPL')
        self.timeframe = self.params.get('timeframe', '1d')
        
        # Internal state for the strategy
        self.prices = []
        self.sma1 = []
        self.sma2 = []

    async def init(self):
        """
        Initialize the strategy by pre-loading historical data to warm up the indicators.
        """
        print(f"Initializing {self.name} strategy with short window {self.n1} and long window {self.n2}.")
        
        # Load enough historical data to calculate the longest moving average
        # In a real scenario, you'd fetch this from the broker/data_manager
        # For this example, we'll start with an empty list.
        # A more robust implementation would pre-fill `self.prices` here.
        print(f"{self.name}: Initialization complete.")

    async def on_bar(self, bar_data: pd.Series):
        """
        Called for each new bar of data. Implements the core trading logic.
        """
        # Append the new closing price to our price list
        self.prices.append(bar_data['Close'])

        # Don't do anything until we have enough data for the longest MA
        if len(self.prices) < self.n2:
            return

        # --- Calculate Indicators ---
        # In a real strategy, you would use a more efficient library (like pandas-ta or TALib)
        # to calculate indicators rather than doing it manually on each bar.
        current_sma1 = sum(self.prices[-self.n1:]) / self.n1
        current_sma2 = sum(self.prices[-self.n2:]) / self.n2
        
        # We need the previous bar's SMAs to check for a crossover
        if len(self.sma1) > 0:
            prev_sma1 = self.sma1[-1]
            prev_sma2 = self.sma2[-1]
            
            # --- Crossover Logic ---
            # Buy signal: Short MA crosses above Long MA
            if current_sma1 > current_sma2 and prev_sma1 <= prev_sma2:
                print(f"{bar_data['timestamp']}: BUY SIGNAL for {self.symbol} at {bar_data['Close']:.2f}")
                # In a live scenario, you would place an order:
                # await self.broker.place_order({'symbol': self.symbol, 'qty': 1, 'side': 'buy'})

            # Sell signal: Short MA crosses below Long MA
            elif current_sma1 < current_sma2 and prev_sma1 >= prev_sma2:
                print(f"{bar_data['timestamp']}: SELL SIGNAL for {self.symbol} at {bar_data['Close']:.2f}")
                # In a live scenario, you would place an order:
                # await self.broker.place_order({'symbol': self.symbol, 'qty': 1, 'side': 'sell'})

        # Update the history of our SMAs
        self.sma1.append(current_sma1)
        self.sma2.append(current_sma2) 