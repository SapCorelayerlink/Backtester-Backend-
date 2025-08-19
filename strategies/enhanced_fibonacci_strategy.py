import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies.enhanced_strategy_base import EnhancedStrategyBase
from core.registry import StrategyRegistry
from typing import Dict, Any

@StrategyRegistry.register("EnhancedFibonacciStrategy")
class EnhancedFibonacciStrategy(EnhancedStrategyBase):
    """
    Enhanced Fibonacci Retracement Strategy with IBKR and Polygon.io integration.
    Uses Fibonacci retracement levels for entry and exit signals with fallback data providers.
    """
    
    def __init__(self, name: str, broker, params: dict = None):
        super().__init__(name, broker, params)
        
        # Strategy parameters
        self.symbol = self.params.get('symbol', 'SPY') if self.params else 'SPY'
        self.timeframe = self.params.get('timeframe', '15') if self.params else '15'
        self.quantity = self.params.get('quantity', 100) if self.params else 100
        
        # Fibonacci parameters
        self.fib_levels = self.params.get('fib_levels', [0.382, 0.5, 0.618]) if self.params else [0.382, 0.5, 0.618]
        self.extension_level = self.params.get('extension_level', 1.272) if self.params else 1.272
        self.first_hour_bars = self.params.get('first_hour_bars', 4) if self.params else 4  # 4 bars for 1 hour in 15min timeframe
        
        # Risk management parameters
        self.stop_loss_pct = self.params.get('stop_loss_pct', 0.02) if self.params else 0.02  # 2% stop loss
        self.take_profit_pct = self.params.get('take_profit_pct', 0.06) if self.params else 0.06  # 6% take profit
        self.max_position_size = self.params.get('max_position_size', 0.1) if self.params else 0.1  # Max 10% of portfolio
        
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
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0

    async def init(self):
        """Initialize the enhanced Fibonacci strategy."""
        await super().init()
        
        print(f"Enhanced Fibonacci Strategy Configuration:")
        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {self.timeframe} minutes")
        print(f"Fibonacci Levels: {self.fib_levels}")
        print(f"Extension Level: {self.extension_level}")
        print(f"Stop Loss: {self.stop_loss_pct * 100}%")
        print(f"Take Profit: {self.take_profit_pct * 100}%")
        print(f"Max Position Size: {self.max_position_size * 100}%")
        print(f"{self.name}: Enhanced initialization complete.")

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

    async def calculate_position_size(self, entry_price: float) -> int:
        """Calculate position size based on risk management rules."""
        try:
            # Get account info
            account_info = await self.get_account_info()
            
            if not account_info or 'account_summary' not in account_info:
                return self.quantity  # Default quantity
            
            # Find NetLiquidation value
            net_liquidation = 0
            for summary in account_info['account_summary']:
                if summary.get('tag') == 'NetLiquidation':
                    net_liquidation = float(summary.get('value', 0))
                    break
            
            if net_liquidation <= 0:
                return self.quantity  # Default quantity
            
            # Calculate position size based on max position size
            max_position_value = net_liquidation * self.max_position_size
            calculated_quantity = int(max_position_value / entry_price)
            
            # Use the smaller of calculated quantity or default quantity
            return min(calculated_quantity, self.quantity)
            
        except Exception as e:
            print(f"Error calculating position size: {e}")
            return self.quantity

    async def on_bar(self, bar_data: pd.Series):
        """Process each new bar and execute trading logic."""
        try:
            # Extract bar data
            current_price = bar_data.get('close') or bar_data.get('Close')
            current_time = bar_data.get('timestamp') or bar_data.get('Timestamp')
            high = bar_data.get('high') or bar_data.get('High')
            low = bar_data.get('low') or bar_data.get('Low')
            open_price = bar_data.get('open') or bar_data.get('Open')
            volume = bar_data.get('volume') or bar_data.get('Volume', 100)
            
            if not all([current_price, current_time, high, low, open_price]):
                return
            
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
                print(f"EnhancedFibonacciStrategy: Error processing timestamps: {e}")
                return
            
            # Get current date safely
            try:
                if current_time is not None:
                    current_date = current_time.date()
                else:
                    # If current_time is None, use the latest available date
                    current_date = df.index.date[-1]
            except Exception as e:
                print(f"EnhancedFibonacciStrategy: Error getting current date: {e}")
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
                
                print(f"{current_time}: Trend determined: {self.current_trend.upper()}")
                print(f"Day High: {day_high:.2f}, Day Low: {day_low:.2f}")
            
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
                            # Calculate position size
                            position_size = await self.calculate_position_size(current_price)
                            
                            # Calculate stop loss and take profit
                            self.entry_price = current_price
                            self.stop_loss = current_price * (1 - self.stop_loss_pct)
                            self.take_profit = current_price * (1 + self.take_profit_pct)
                            
                            # Place order using enhanced broker
                            result = await self.place_trade_order(
                                symbol=self.symbol,
                                side='buy',
                                quantity=position_size,
                                order_type='market',
                                stop_loss=self.stop_loss,
                                take_profit=self.take_profit
                            )
                            
                            if result.get('order_id'):
                                self.in_position = True
                                self.position_side = 'long'
                                self.total_trades += 1
                                print(f"{current_time}: LONG ENTRY for {self.symbol} at {self.entry_price:.2f} (Fib {level:.3f}: {fib_price:.2f})")
                                print(f"Position Size: {position_size}, Stop Loss: {self.stop_loss:.2f}, Take Profit: {self.take_profit:.2f}")
                                print(f"Broker Used: {result.get('broker_used', 'unknown')}")
                            break
                
                elif self.current_trend == "down":
                    # SHORT entry - look for price to touch Fibonacci level and close below it
                    for level in sorted(self.fib_levels):  # Start with lower levels
                        fib_price = fib_levels[level]
                        if high >= fib_price >= current_price:
                            # Calculate position size
                            position_size = await self.calculate_position_size(current_price)
                            
                            # Calculate stop loss and take profit
                            self.entry_price = current_price
                            self.stop_loss = current_price * (1 + self.stop_loss_pct)
                            self.take_profit = current_price * (1 - self.take_profit_pct)
                            
                            # Place order using enhanced broker
                            result = await self.place_trade_order(
                                symbol=self.symbol,
                                side='sell',
                                quantity=position_size,
                                order_type='market',
                                stop_loss=self.stop_loss,
                                take_profit=self.take_profit
                            )
                            
                            if result.get('order_id'):
                                self.in_position = True
                                self.position_side = 'short'
                                self.total_trades += 1
                                print(f"{current_time}: SHORT ENTRY for {self.symbol} at {self.entry_price:.2f} (Fib {level:.3f}: {fib_price:.2f})")
                                print(f"Position Size: {position_size}, Stop Loss: {self.stop_loss:.2f}, Take Profit: {self.take_profit:.2f}")
                                print(f"Broker Used: {result.get('broker_used', 'unknown')}")
                            break
            
            # Exit logic
            elif self.in_position:
                exit_signal = False
                exit_reason = ""
                
                if self.position_side == 'long':
                    # Exit long position
                    if current_price <= self.stop_loss:
                        exit_signal = True
                        exit_reason = "Stop Loss"
                    elif current_price >= self.take_profit:
                        exit_signal = True
                        exit_reason = "Take Profit"
                        
                elif self.position_side == 'short':
                    # Exit short position
                    if current_price >= self.stop_loss:
                        exit_signal = True
                        exit_reason = "Stop Loss"
                    elif current_price <= self.take_profit:
                        exit_signal = True
                        exit_reason = "Take Profit"
                
                if exit_signal:
                    # Calculate PnL
                    if self.position_side == 'long':
                        pnl = (current_price - self.entry_price) * self.quantity
                    else:
                        pnl = (self.entry_price - current_price) * self.quantity
                    
                    # Update performance tracking
                    self.total_pnl += pnl
                    if pnl > 0:
                        self.winning_trades += 1
                    else:
                        self.losing_trades += 1
                    
                    # Place exit order
                    result = await self.place_trade_order(
                        symbol=self.symbol,
                        side='sell' if self.position_side == 'long' else 'buy',
                        quantity=self.quantity,
                        order_type='market'
                    )
                    
                    if result.get('order_id'):
                        print(f"{current_time}: {self.position_side.upper()} EXIT for {self.symbol} at {current_price:.2f}")
                        print(f"PnL: {pnl:.2f} ({exit_reason})")
                        print(f"Total PnL: {self.total_pnl:.2f}")
                        print(f"Win Rate: {(self.winning_trades / self.total_trades * 100):.1f}%")
                        print(f"Broker Used: {result.get('broker_used', 'unknown')}")
                        
                        # Reset position
                        self.in_position = False
                        self.position_side = None
                        self.entry_price = 0.0
                        self.stop_loss = 0.0
                        self.take_profit = 0.0
            
            # Reset Fibonacci levels calculation for new day
            if len(df_today) == 1:  # First bar of the day
                self.fib_levels_calculated = False
                
        except Exception as e:
            print(f"EnhancedFibonacciStrategy: Error in on_bar: {e}")

    def get_results(self) -> Dict[str, Any]:
        """Get enhanced strategy results."""
        base_results = super().get_results()
        
        # Add Fibonacci-specific metrics
        fibonacci_results = {
            'fibonacci_levels': self.fib_levels,
            'extension_level': self.extension_level,
            'current_trend': self.current_trend,
            'in_position': self.in_position,
            'position_side': self.position_side,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_pnl': self.total_pnl,
            'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        }
        
        # Merge results
        base_results.update(fibonacci_results)
        return base_results
