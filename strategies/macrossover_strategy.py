import pandas as pd
from core.base import StrategyBase
from core.registry import StrategyRegistry
from datetime import datetime

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
        
        # Position tracking
        self.position = 0  # 0 = no position, 1 = long, -1 = short
        self.entry_price = 0
        self.entry_time = None
        self.stop_loss_pct = self.params.get('stop_loss_pct', 0.05)

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
        self.prices.append(bar_data['close'])
        current_price = bar_data['close']
        current_time = bar_data['timestamp']

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
            
            # --- Check for stop loss on existing position ---
            if self.position != 0:
                stop_loss_hit = False
                if self.position == 1:  # Long position
                    stop_price = self.entry_price * (1 - self.stop_loss_pct)
                    if current_price <= stop_price:
                        stop_loss_hit = True
                elif self.position == -1:  # Short position
                    stop_price = self.entry_price * (1 + self.stop_loss_pct)
                    if current_price >= stop_price:
                        stop_loss_hit = True
                
                if stop_loss_hit:
                    # Close position due to stop loss
                    pnl = (current_price - self.entry_price) * self.position
                    self.record_trade(
                        entry_time=self.entry_time,
                        exit_time=current_time,
                        symbol=self.symbol,
                        quantity=1,
                        side='buy' if self.position == 1 else 'sell',
                        entry_price=self.entry_price,
                        exit_price=current_price,
                        pnl=pnl
                    )
                    
                    # Update equity
                    self.current_equity += pnl
                    self.position = 0
                    self.entry_price = 0
                    self.entry_time = None
                    
                    print(f"{current_time}: STOP LOSS - Closed position at {current_price:.2f}, PnL: {pnl:.2f}")
            
            # --- Crossover Logic ---
            # Buy signal: Short MA crosses above Long MA
            if current_sma1 > current_sma2 and prev_sma1 <= prev_sma2:
                if self.position == 0:  # No position, can buy
                    self.position = 1
                    self.entry_price = current_price
                    self.entry_time = current_time
                    print(f"{current_time}: BUY SIGNAL for {self.symbol} at {current_price:.2f}")
                elif self.position == -1:  # Short position, close it
                    pnl = (self.entry_price - current_price)  # Profit for short
                    self.record_trade(
                        entry_time=self.entry_time,
                        exit_time=current_time,
                        symbol=self.symbol,
                        quantity=1,
                        side='sell',
                        entry_price=self.entry_price,
                        exit_price=current_price,
                        pnl=pnl
                    )
                    
                    # Update equity
                    self.current_equity += pnl
                    
                    # Open new long position
                    self.position = 1
                    self.entry_price = current_price
                    self.entry_time = current_time
                    print(f"{current_time}: BUY SIGNAL - Closed short and opened long at {current_price:.2f}, PnL: {pnl:.2f}")

            # Sell signal: Short MA crosses below Long MA
            elif current_sma1 < current_sma2 and prev_sma1 >= prev_sma2:
                if self.position == 0:  # No position, can short
                    self.position = -1
                    self.entry_price = current_price
                    self.entry_time = current_time
                    print(f"{current_time}: SELL SIGNAL for {self.symbol} at {current_price:.2f}")
                elif self.position == 1:  # Long position, close it
                    pnl = (current_price - self.entry_price)  # Profit for long
                    self.record_trade(
                        entry_time=self.entry_time,
                        exit_time=current_time,
                        symbol=self.symbol,
                        quantity=1,
                        side='buy',
                        entry_price=self.entry_price,
                        exit_price=current_price,
                        pnl=pnl
                    )
                    
                    # Update equity
                    self.current_equity += pnl
                    
                    # Open new short position
                    self.position = -1
                    self.entry_price = current_price
                    self.entry_time = current_time
                    print(f"{current_time}: SELL SIGNAL - Closed long and opened short at {current_price:.2f}, PnL: {pnl:.2f}")

        # Update the history of our SMAs
        self.sma1.append(current_sma1)
        self.sma2.append(current_sma2) 