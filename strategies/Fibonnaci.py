import pandas as pd
import numpy as np
from core.base import StrategyBase
from core.registry import StrategyRegistry

@StrategyRegistry.register("FibonacciStrategy")
class FibonacciStrategy(StrategyBase):
    """
    Fibonacci Retracement Strategy.
    Uses Fibonacci retracement levels for entry and exit signals.
    """
    
    def __init__(self, name: str, broker: 'BrokerBase', params: dict = None):
        super().__init__(name, broker, params)
        
        # Strategy parameters
        self.symbol = self.params.get('symbol', 'SPY')
        self.timeframe = self.params.get('timeframe', '4h')
        self.quantity = self.params.get('quantity', 100)
        
        # Fibonacci parameters
        self.fib_levels = self.params.get('fib_levels', [0.382, 0.5, 0.618])
        self.extension_level = self.params.get('extension_level', 1.272)
        self.first_hour_bars = self.params.get('first_hour_bars', 4)  # 4 bars for 1 hour in 15min timeframe
        
        # State variables
        self.in_position = False
        self.position_side = None
        self.entry_price = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.current_trend = None
        self.fib_levels_calculated = False
        
        # Data storage
        self.price_data = []
        self.daily_highs = {}
        self.daily_lows = {}

    async def init(self):
        """Initialize the strategy."""
        print(f"Initializing {self.name} Fibonacci Strategy")
        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {self.timeframe}")
        print(f"Fibonacci Levels: {self.fib_levels}")
        print(f"Extension Level: {self.extension_level}")
        print(f"{self.name}: Initialization complete.")

    def calculate_fibonacci_levels(self, high, low, trend):
        """Calculate Fibonacci retracement levels."""
        fib_levels = {}
        range_size = high - low
        
        for level in self.fib_levels:
            if trend == "up":
                fib_levels[level] = high - (range_size * level)
            else:
                fib_levels[level] = low + (range_size * level)
        
        return fib_levels

    def calculate_extension_target(self, high, low, trend):
        """Calculate Fibonacci extension target."""
        range_size = high - low
        
        if trend == "up":
            return high + (range_size * (self.extension_level - 1))
        else:
            return low - (range_size * (self.extension_level - 1))

    async def on_bar(self, bar_data: pd.Series):
        """Process each new bar and execute trading logic."""
        # Extract bar data
        current_price = bar_data.get('close') or bar_data.get('Close')
        current_time = bar_data.get('timestamp') or bar_data.get('Timestamp')
        high = bar_data.get('high') or bar_data.get('High')
        low = bar_data.get('low') or bar_data.get('Low')
        open_price = bar_data.get('open') or bar_data.get('Open')
        volume = bar_data.get('volume') or bar_data.get('Volume', 100)
        
        # Add to price data
        self.price_data.append({
            'timestamp': current_time,
            'open': open_price,
            'high': high,
            'low': low,
            'close': current_price,
            'volume': volume
        })
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(self.price_data)
        
        # Handle timestamp conversion safely
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Remove any NaT values
            df = df.dropna(subset=['timestamp'])
            if df.empty:
                return
            df.set_index('timestamp', inplace=True)
        except Exception as e:
            print(f"FibonacciStrategy: Error processing timestamps: {e}")
            return
        
        # Get current date safely
        try:
            if current_time is not None:
                current_date = current_time.date()
            else:
                # If current_time is None, use the latest available date
                current_date = df.index.date[-1]
        except Exception as e:
            print(f"FibonacciStrategy: Error getting current date: {e}")
            return
        
        # Get today's data
        df_today = df[df.index.date == current_date]
        
        if len(df_today) < self.first_hour_bars:
            return
        
        # Calculate trend and Fibonacci levels for the day
        if not self.fib_levels_calculated or current_date not in self.daily_highs:
            # Use first hour data to determine trend and calculate Fibonacci levels
            first_hour_data = df_today.iloc[:self.first_hour_bars]
            
            day_high = first_hour_data['high'].max()
            day_low = first_hour_data['low'].min()
            day_open = first_hour_data['open'].iloc[0]
            
            # Determine trend based on first hour movement
            if (day_high - day_open) >= (day_open - day_low):
                self.current_trend = "up"
            else:
                self.current_trend = "down"
            
            # Store daily levels
            self.daily_highs[current_date] = day_high
            self.daily_lows[current_date] = day_low
            
            # Calculate Fibonacci levels
            self.fib_levels_calculated = True
        
        # Get today's levels
        day_high = self.daily_highs.get(current_date)
        day_low = self.daily_lows.get(current_date)
        
        if day_high is None or day_low is None:
            return
        
        # Calculate Fibonacci levels
        fib_levels = self.calculate_fibonacci_levels(day_high, day_low, self.current_trend)
        
        # Trading logic
        if not self.in_position:
            # Entry logic
            if self.current_trend == "up":
                # LONG entry - look for price to touch Fibonacci level and close above it
                for level in sorted(self.fib_levels, reverse=True):  # Start with higher levels
                    fib_price = fib_levels[level]
                    if low <= fib_price <= current_price:
                        self.entry_price = current_price
                        self.stop_loss = fib_levels[min(self.fib_levels, key=lambda x: x < level)]
                        self.take_profit = self.calculate_extension_target(day_high, day_low, "up")
                        
                        # Place order
                        order = {
                            'symbol': self.symbol,
                            'qty': self.quantity,
                            'side': 'buy',
                            'order_type': 'market'
                        }
                        
                        result = await self.broker.place_order(order)
                        if result.get('order_id'):
                            self.in_position = True
                            self.position_side = 'long'
                            print(f"{current_time}: LONG ENTRY for {self.symbol} at {self.entry_price:.2f} (Fib {level:.3f}: {fib_price:.2f})")
                        break
            
            elif self.current_trend == "down":
                # SHORT entry - look for price to touch Fibonacci level and close below it
                for level in sorted(self.fib_levels):  # Start with lower levels
                    fib_price = fib_levels[level]
                    if high >= fib_price >= current_price:
                        self.entry_price = current_price
                        self.stop_loss = fib_levels[max(self.fib_levels, key=lambda x: x > level)]
                        self.take_profit = self.calculate_extension_target(day_high, day_low, "down")
                        
                        # Place order
                        order = {
                            'symbol': self.symbol,
                            'qty': self.quantity,
                            'side': 'sell',
                            'order_type': 'market'
                        }
                        
                        result = await self.broker.place_order(order)
                        if result.get('order_id'):
                            self.in_position = True
                            self.position_side = 'short'
                            print(f"{current_time}: SHORT ENTRY for {self.symbol} at {self.entry_price:.2f} (Fib {level:.3f}: {fib_price:.2f})")
                        break
        
        # Exit logic
        elif self.in_position:
            exit_signal = False
            
            if self.position_side == 'long':
                # Exit long position
                if current_price <= self.stop_loss or current_price >= self.take_profit:
                    exit_signal = True
                    exit_reason = "Stop Loss" if current_price <= self.stop_loss else "Take Profit"
                    
            elif self.position_side == 'short':
                # Exit short position
                if current_price >= self.stop_loss or current_price <= self.take_profit:
                    exit_signal = True
                    exit_reason = "Stop Loss" if current_price >= self.stop_loss else "Take Profit"
            
            if exit_signal:
                # Place exit order
                order = {
                    'symbol': self.symbol,
                    'qty': self.quantity,
                    'side': 'sell' if self.position_side == 'long' else 'buy',
                    'order_type': 'market'
                }
                
                result = await self.broker.place_order(order)
                if result.get('order_id'):
                    pnl = (current_price - self.entry_price) * self.quantity
                    if self.position_side == 'short':
                        pnl = -pnl
                    
                    print(f"{current_time}: {self.position_side.upper()} EXIT for {self.symbol} at {current_price:.2f}, PnL: {pnl:.2f} ({exit_reason})")
                    
                    # Reset position
                    self.in_position = False
                    self.position_side = None
                    self.entry_price = 0.0
                    self.stop_loss = 0.0
                    self.take_profit = 0.0
        
        # Reset Fibonacci levels calculation for new day
        if len(df_today) == 1:  # First bar of the day
            self.fib_levels_calculated = False

    def get_results(self):
        """Get strategy results."""
        initial_equity = getattr(self, 'initial_equity', 0)
        return {
            'trades': getattr(self, 'trades', []),
            'total_pnl': getattr(self, 'current_equity', 0) - initial_equity,
            'total_trades': len(getattr(self, 'trades', [])),
            'winning_trades': len([t for t in getattr(self, 'trades', []) if t.get('pnl', 0) > 0]),
            'losing_trades': len([t for t in getattr(self, 'trades', []) if t.get('pnl', 0) < 0])
        }
