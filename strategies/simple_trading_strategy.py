import pandas as pd
from core.base import StrategyBase
from core.registry import StrategyRegistry
from datetime import datetime

@StrategyRegistry.register("SimpleTrading")
class SimpleTrading(StrategyBase):
    """
    A simple trading strategy that generates trades for demonstration.
    Buys every 10 days and sells every 10 days.
    """
    def __init__(self, name: str, broker: 'BrokerBase', params: dict = None):
        super().__init__(name, broker, params)
        self.symbol = self.params.get('symbol', 'AAPL')
        self.timeframe = self.params.get('timeframe', '1d')
        self.day_count = 0
        self.position = 0
        self.entry_price = 0
        self.entry_time = None

    async def init(self):
        """Initialize the strategy."""
        print(f"Initializing {self.name} strategy for {self.symbol}")

    async def on_bar(self, bar_data: pd.Series):
        """Called for each new bar of data."""
        current_price = bar_data['Close']
        current_time = bar_data['timestamp']
        self.day_count += 1

        # Update equity curve
        self.update_equity(current_time, self.current_equity)

        # Simple trading logic: buy every 10 days, sell every 10 days
        if self.day_count % 10 == 0:
            if self.position == 0:  # No position, buy
                self.position = 1
                self.entry_price = current_price
                self.entry_time = current_time
                print(f"{current_time}: BUY {self.symbol} at ${current_price:.2f}")
                
            elif self.position == 1:  # Have position, sell
                pnl = current_price - self.entry_price
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
                self.position = 0
                self.entry_price = 0
                self.entry_time = None
                print(f"{current_time}: SELL {self.symbol} at ${current_price:.2f}, PnL: ${pnl:.2f}")

        # Close any remaining position at the end
        if self.day_count >= 250 and self.position == 1:  # End of year
            pnl = current_price - self.entry_price
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
            self.current_equity += pnl
            self.position = 0
            print(f"{current_time}: FINAL SELL {self.symbol} at ${current_price:.2f}, PnL: ${pnl:.2f}") 