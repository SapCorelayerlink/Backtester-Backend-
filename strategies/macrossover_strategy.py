"""
Implements a simple Moving Average Crossover strategy using the backtesting.py framework.
"""
from backtesting import Strategy
from backtesting.lib import crossover

# We will need a way to calculate indicators.
# The backtesting.py library recommends using a function that wraps an indicator library
# like TA-Lib or pandas-ta. For simplicity, we'll create a simple moving average function here.
def sma(arr: list, n: int) -> list:
    """Returns the simple moving average of a list."""
    if len(arr) < n:
        return [float('nan')] * len(arr)
    
    res = [float('nan')] * (n - 1)
    # Calculate the first SMA
    first_sma = sum(arr[:n]) / n
    res.append(first_sma)

    # Efficiently calculate the rest of the SMAs
    for i in range(n, len(arr)):
        next_sma = res[-1] + (arr[i] - arr[i-n]) / n
        res.append(next_sma)
        
    return res


class MACrossover(Strategy):
    """
    A simple moving average crossover strategy.
    
    When the shorter MA crosses above the longer MA, it's a buy signal.
    When the shorter MA crosses below the longer MA, it's a sell signal.
    """
    # Define the two MA windows as class variables.
    # These can be optimized by the backtesting framework.
    n1 = 10  # Short-term window
    n2 = 30  # Long-term window
    stop_loss_pct = 0.05 # Default stop-loss percentage (e.g., 5%)

    def init(self):
        """
        Called once at the start of the backtest.
        Used to initialize indicators and other strategy state.
        """
        # `self.data.Close` is a numpy array of the close prices
        close = self.data.Close
        # Calculate the two moving averages
        self.sma1 = self.I(sma, close, self.n1)
        self.sma2 = self.I(sma, close, self.n2)

    def next(self):
        """
        Called for each bar in the backtest.
        This is where the trading logic resides.
        """
        # Calculate stop-loss price
        sl_price_long = self.data.Close[-1] * (1 - self.stop_loss_pct)
        sl_price_short = self.data.Close[-1] * (1 + self.stop_loss_pct)

        # If the short MA crosses above the long MA, close any existing short
        # position and open a new long position with a stop-loss.
        if crossover(self.sma1, self.sma2):
            self.position.close()
            self.buy(sl=sl_price_long)

        # If the short MA crosses below the long MA, close any existing long
        # position and open a new short position with a stop-loss.
        elif crossover(self.sma2, self.sma1):
            self.position.close()
            self.sell(sl=sl_price_short) 