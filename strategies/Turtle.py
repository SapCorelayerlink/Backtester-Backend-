import pandas as pd
import numpy as np
import ta
from core.base import StrategyBase
from core.registry import StrategyRegistry

@StrategyRegistry.register("TurtleStrategy")
class TurtleStrategy(StrategyBase):
    """
    Turtle Trading Strategy adapted for the IBKR framework.
    Preserves all original trading conditions and logic.
    """
    
    def __init__(self, name: str, broker: 'BrokerBase', params: dict = None):
        super().__init__(name, broker, params)
        
        # Strategy parameters (preserving original conditions)
        self.stop_n = self.params.get('stop_n', 2.0)
        self.risk_percent = self.params.get('risk_percent', 0.01)
        self.pyramid_n = self.params.get('pyramid_n', 0.5)
        self.max_units = self.params.get('max_units', 5)
        self.atr_period = self.params.get('atr_period', 14)
        self.l1_long = self.params.get('l1_long', 20)
        self.l2_long = self.params.get('l2_long', 55)
        self.l1_long_exit = self.params.get('l1_long_exit', 10)
        self.l2_long_exit = self.params.get('l2_long_exit', 20)
        self.initial_capital = self.params.get('initial_capital', 100000)
        
        # Trading parameters
        self.symbol = self.params.get('symbol', 'AAPL')
        self.timeframe = self.params.get('timeframe', '1h')  # 1-hour bars (intraday)
        self.quantity = self.params.get('quantity', 100)
        
        # State variables (preserving original logic)
        self.reset_state()
        
        # Data storage
        self.price_data = []

    def reset_state(self):
        """Reset all strategy state variables (preserving original logic)."""
        self.win = False
        self.buy_price = 0.0
        self.next_buy_price = 0.0
        self.stop_price = np.nan
        self.total_buys = 0
        self.in_buy = False
        self.mode = 'L1'
        self.fake = False
        self.fake_buy_price = 0.0
        self.capital_left = self.initial_capital
        self.position_size = 0
        self.position_avg_price = 0.0
        self.net_profit = 0.0
        
        # IBKR integration state
        self.position = 0  # 0 = no position, 1 = long, -1 = short
        self.entry_price = 0.0
        self.entry_time = None

    async def init(self):
        """Initialize the strategy by pre-loading historical data."""
        print(f"Initializing {self.name} Turtle strategy")
        print(f"Parameters: ATR({self.atr_period}), L1({self.l1_long}), L2({self.l2_long})")
        print(f"Stop N: {self.stop_n}, Risk: {self.risk_percent:.1%}")
        print(f"Pyramid N: {self.pyramid_n}, Max Units: {self.max_units}")
        print(f"Symbol: {self.symbol}, Timeframe: {self.timeframe} (1-hour bars - intraday)")
        print(f"{self.name}: Initialization complete.")

    def calculate_indicators(self, df):
        """Calculate required technical indicators (preserving original logic)."""
        # Handle column name mapping - check for uppercase and create lowercase versions
        for lower_col, upper_col in [('high', 'High'), ('low', 'Low'), ('close', 'Close'), 
                                   ('volume', 'Volume'), ('timestamp', 'Timestamp')]:
            if upper_col in df.columns and lower_col not in df.columns:
                df[lower_col] = df[upper_col]
        
        # Calculate ATR for 1-hour timeframe
        df['atr'] = ta.volatility.AverageTrueRange(
            high=df['high'], 
            low=df['low'], 
            close=df['close'], 
            window=self.atr_period
        ).average_true_range()
        
        # Calculate highest highs and lowest lows for 1-hour bars
        df['l1_long'] = df['high'].rolling(window=self.l1_long).max()
        df['l2_long'] = df['high'].rolling(window=self.l2_long).max()
        df['l1_long_exit'] = df['low'].rolling(window=self.l1_long_exit).min()
        df['l2_long_exit'] = df['low'].rolling(window=self.l2_long_exit).min()
        
        return df

    async def on_bar(self, bar_data: pd.Series):
        """Process each new bar and execute trading logic (preserving original conditions)."""
        # Extract bar data - handle both lowercase and uppercase column names
        current_price = bar_data.get('close') or bar_data.get('Close')
        current_time = bar_data.get('timestamp') or bar_data.get('Timestamp')
        high = bar_data.get('high') or bar_data.get('High')
        low = bar_data.get('low') or bar_data.get('Low')
        
        # Add to price data
        self.price_data.append({
            'timestamp': current_time,
            'open': bar_data.get('open') or bar_data.get('Open'),
            'high': high,
            'low': low,
            'close': current_price,
            'volume': bar_data.get('volume') or bar_data.get('Volume', 100)
        })
        
        # Need enough data for indicators
        if len(self.price_data) < max(self.l2_long, self.atr_period):
            return
        
        # Convert to DataFrame for indicator calculation
        df = pd.DataFrame(self.price_data)
        df = self.calculate_indicators(df)
        
        # Get current and previous values
        if len(df) < 2:
            return
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Get current values
        atr_val = current['atr']
        
        # Skip if ATR is not available
        if pd.isna(atr_val):
            return
        
        # Entry conditions for 1-hour timeframe (preserving original logic)
        l1_breakout = high > previous['l1_long']
        l2_breakout = high > previous['l2_long']
        
        # Check for fake trade (skip if last trade was winning L1)
        if not self.in_buy and l1_breakout and self.win and not l2_breakout:
            self.fake = True
            self.fake_buy_price = current_price
        
        # Reset fake if L2 breakout occurs
        if l2_breakout:
            self.fake = False
        
        # Entry logic (preserving original logic)
        enter_long = False
        long_level = None
        
        if not self.in_buy and (l1_breakout or l2_breakout) and not self.fake:
            enter_long = True
            self.in_buy = True
            
            if l2_breakout:
                long_level = 'L2'
                self.mode = 'L2'
            else:
                long_level = 'L1' 
                self.mode = 'L1'
            
            # Initialize position
            self.buy_price = current_price
            self.total_buys = 1
            self.stop_price = current_price - (self.stop_n * atr_val)
            self.next_buy_price = current_price + (self.pyramid_n * atr_val)
            
            # Calculate position size based on risk
            risk_amount = (self.initial_capital + self.net_profit) * self.risk_percent
            shares = int(risk_amount / (self.stop_n * atr_val))
            self.position_size = shares
            self.position_avg_price = current_price
            
            # Update IBKR state
            self.position = 1
            self.entry_price = current_price
            self.entry_time = current_time
            
            # Place order via IBKR
            try:
                order = {
                    'symbol': self.symbol,
                    'qty': self.quantity,
                    'side': 'BUY',
                    'order_type': 'MKT'
                }
                await self.broker.place_order(order)
                print(f"{current_time}: TURTLE LONG ENTRY for {self.symbol} at {current_price:.2f} ({long_level})")
            except Exception as e:
                print(f"{self.name}: Failed to place TURTLE LONG order: {e}")
        
        # Pyramid logic (add to position) - preserving original logic
        elif (self.in_buy and high > self.next_buy_price and 
              self.total_buys < self.max_units):
            enter_long = True
            long_level = 'P'
            
            # Update position
            old_value = self.position_size * self.position_avg_price
            additional_shares = self.position_size  # Add same amount
            new_total_shares = self.position_size + additional_shares
            
            self.position_avg_price = (old_value + additional_shares * current_price) / new_total_shares
            self.position_size = new_total_shares
            
            self.buy_price = current_price
            self.total_buys += 1
            self.stop_price = current_price - (self.stop_n * atr_val)
            self.next_buy_price = current_price + (self.pyramid_n * atr_val)
            
            # Place additional order via IBKR
            try:
                order = {
                    'symbol': self.symbol,
                    'qty': self.quantity,
                    'side': 'BUY',
                    'order_type': 'MKT'
                }
                await self.broker.place_order(order)
                print(f"{current_time}: TURTLE PYRAMID for {self.symbol} at {current_price:.2f} (Unit {self.total_buys})")
            except Exception as e:
                print(f"{self.name}: Failed to place TURTLE PYRAMID order: {e}")
        
        # Exit conditions (preserving original logic)
        exit_long = False
        
        if self.in_buy:
            # Stop loss hit
            if low < self.stop_price:
                exit_long = True
                self.win = current_price >= self.position_avg_price
                long_level = 'SG' if self.win else 'SR'
            
            # Exit on low break (L1 or L2 depending on mode)
            elif ((self.mode == 'L1' and low < previous['l1_long_exit']) or
                  (self.mode == 'L2' and low < previous['l2_long_exit'])):
                exit_long = True
                self.win = current_price >= self.position_avg_price
                long_level = 'SG' if self.win else 'SR'
            
            # Reset position on exit
            if exit_long:
                self.in_buy = False
                self.total_buys = 0
                
                # Calculate PnL
                pnl = (current_price - self.position_avg_price) * self.position_size
                self.net_profit += pnl
                
                # Place exit order via IBKR
                try:
                    order = {
                        'symbol': self.symbol,
                        'qty': self.quantity * self.position_size,
                        'side': 'SELL',
                        'order_type': 'MKT'
                    }
                    await self.broker.place_order(order)
                    
                    # Record trade
                    self.record_trade(
                        entry_time=self.entry_time,
                        exit_time=current_time,
                        symbol=self.symbol,
                        quantity=self.quantity * self.position_size,
                        side='long',
                        entry_price=self.position_avg_price,
                        exit_price=current_price,
                        pnl=pnl
                    )
                    
                    # Update equity
                    self.current_equity += pnl
                    print(f"{current_time}: TURTLE EXIT for {self.symbol} at {current_price:.2f}, PnL: {pnl:.2f} ({long_level})")
                    
                except Exception as e:
                    print(f"{self.name}: Failed to place TURTLE EXIT order: {e}")
                
                # Reset IBKR state
                self.position = 0
                self.entry_price = 0.0
                self.entry_time = None
                self.position_size = 0
                self.position_avg_price = 0.0
        
        # Handle fake trade completion
        if self.fake and not self.in_buy and exit_long:
            self.fake = False
            self.win = current_price >= self.fake_buy_price

    def generate_signals(self, df):
        """
        Legacy signal generation method for compatibility (preserving original logic).
        This method is kept for backward compatibility but the main execution
        should use the IBKR framework via on_bar().
        """
        df = self.calculate_indicators(df)
        
        signals = []
        long_levels = []
        
        for i in range(1, len(df)):
            current = df.iloc[i]
            previous = df.iloc[i-1]
            
            # Get current values
            high = current['high']
            low = current['low']
            close = current['close']
            atr_val = current['atr']
            
            # Skip if ATR is not available
            if pd.isna(atr_val):
                signals.append(0)
                long_levels.append(None)
                continue
            
            # Entry conditions for 1-hour timeframe
            l1_breakout = high > previous['l1_long']
            l2_breakout = high > previous['l2_long']
            
            # Check for fake trade (skip if last trade was winning L1)
            if not self.in_buy and l1_breakout and self.win and not l2_breakout:
                self.fake = True
                self.fake_buy_price = close
            
            # Reset fake if L2 breakout occurs
            if l2_breakout:
                self.fake = False
            
            # Entry logic
            enter_long = False
            long_level = None
            
            if not self.in_buy and (l1_breakout or l2_breakout) and not self.fake:
                enter_long = True
                self.in_buy = True
                
                if l2_breakout:
                    long_level = 'L2'
                    self.mode = 'L2'
                else:
                    long_level = 'L1' 
                    self.mode = 'L1'
                
                # Initialize position
                self.buy_price = close
                self.total_buys = 1
                self.stop_price = close - (self.stop_n * atr_val)
                self.next_buy_price = close + (self.pyramid_n * atr_val)
                
                # Calculate position size based on risk
                risk_amount = (self.initial_capital + self.net_profit) * self.risk_percent
                shares = int(risk_amount / (self.stop_n * atr_val))
                self.position_size = shares
                self.position_avg_price = close
            
            # Pyramid logic (add to position)
            elif (self.in_buy and high > self.next_buy_price and 
                  self.total_buys < self.max_units):
                enter_long = True
                long_level = 'P'
                
                # Update position
                old_value = self.position_size * self.position_avg_price
                additional_shares = self.position_size  # Add same amount
                new_total_shares = self.position_size + additional_shares
                
                self.position_avg_price = (old_value + additional_shares * close) / new_total_shares
                self.position_size = new_total_shares
                
                self.buy_price = close
                self.total_buys += 1
                self.stop_price = close - (self.stop_n * atr_val)
                self.next_buy_price = close + (self.pyramid_n * atr_val)
            
            # Exit conditions
            exit_long = False
            
            if self.in_buy:
                # Stop loss hit
                if low < self.stop_price:
                    exit_long = True
                    self.win = close >= self.position_avg_price
                    long_level = 'SG' if self.win else 'SR'
                
                # Exit on low break (L1 or L2 depending on mode)
                elif ((self.mode == 'L1' and low < previous['l1_long_exit']) or
                      (self.mode == 'L2' and low < previous['l2_long_exit'])):
                    exit_long = True
                    self.win = close >= self.position_avg_price
                    long_level = 'SG' if self.win else 'SR'
                
                # Reset position on exit
                if exit_long:
                    self.in_buy = False
                    self.total_buys = 0
                    self.position_size = 0
                    self.position_avg_price = 0.0
            
            # Handle fake trade completion
            if self.fake and not self.in_buy and exit_long:
                self.fake = False
                self.win = close >= self.fake_buy_price
            
            # Generate signal
            if enter_long and not self.fake:
                signals.append(1)  # Buy signal
            elif exit_long and not self.fake:
                signals.append(-1)  # Sell signal
            else:
                signals.append(0)  # Hold
            
            long_levels.append(long_level)
        
        # Add first row
        signals.insert(0, 0)
        long_levels.insert(0, None)
        
        df['signal'] = signals
        df['long_level'] = long_levels
        
        return df

    def backtest(self, df):
        """
        Legacy backtest method for compatibility (preserving original logic).
        This method is kept for backward compatibility but the main execution
        should use the IBKR framework via on_bar().
        """
        self.reset_state()
        df = self.generate_signals(df)
        
        # Calculate returns
        df['strategy_returns'] = 0.0
        position = 0
        
        for i in range(1, len(df)):
            signal = df.iloc[i]['signal']
            current_price = df.iloc[i]['close']
            
            if signal == 1:  # Buy
                position = 1
            elif signal == -1:  # Sell
                position = 0
            
            if position == 1:
                df.iloc[i, df.columns.get_loc('strategy_returns')] = \
                    (current_price - df.iloc[i-1]['close']) / df.iloc[i-1]['close']
        
        # Calculate cumulative returns
        df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
        
        return df

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

# Legacy function for backward compatibility
def run_turtle_strategy(ohlcv_data):
    """
    Run Turtle Strategy on 1-hour OHLCV data (legacy function)
    
    Parameters:
    ohlcv_data: pandas DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
                and datetime index at 1-hour intervals
    
    Returns:
    pandas DataFrame with signals and strategy performance
    """
    
    strategy = TurtleStrategy(
        name="LegacyTurtle",
        broker=None,  # Not used in legacy mode
        params={
            'stop_n': 2.0,
            'risk_percent': 0.01,
            'pyramid_n': 0.5,
            'max_units': 5,
            'atr_period': 14,
            'l1_long': 20,    # 20 hours for L1
            'l2_long': 55,    # 55 hours for L2  
            'l1_long_exit': 10,  # 10 hours for L1 exit
            'l2_long_exit': 20,  # 20 hours for L2 exit
            'initial_capital': 100000
        }
    )
    
    results = strategy.backtest(ohlcv_data)
    return results
