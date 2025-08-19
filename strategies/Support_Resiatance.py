import pandas as pd
import numpy as np
from core.base import StrategyBase
from core.registry import StrategyRegistry

@StrategyRegistry.register("SRTrend4H")
class SRTrend4H(StrategyBase):
    """
    Support Resistance Trend Strategy adapted for the IBKR framework.
    Preserves all original trading conditions and logic.
    """
    
    def __init__(self, name: str, broker: 'BrokerBase', params: dict = None):
        super().__init__(name, broker, params)
        
        # Strategy parameters (preserving original conditions)
        self.length = self.params.get('length', 21)
        
        # Trading parameters
        self.symbol = self.params.get('symbol', 'AAPL')
        self.timeframe = self.params.get('timeframe', '4h')  # 4-hour bars
        self.quantity = self.params.get('quantity', 100)
        
        # State variables
        self.position = 0  # 0 = no position, 1 = long, -1 = short
        self.entry_price = 0.0
        self.entry_time = None
        
        # Data storage
        self.price_data = []
        self.hvalc = None  # Current high value
        self.lvalc = None  # Current low value
        self.hvalr = None  # Resistance level
        self.lvalr = None  # Support level
        self.trend = 0     # 1 = bullish, -1 = bearish, 0 = neutral

    async def init(self):
        """Initialize the strategy by pre-loading historical data."""
        print(f"Initializing {self.name} Support Resistance strategy")
        print(f"Parameters: Length({self.length})")
        print(f"Symbol: {self.symbol}, Timeframe: {self.timeframe} (4-hour bars)")
        print(f"{self.name}: Initialization complete.")

    def calculate_indicators(self, df):
        """Calculate support/resistance indicators (preserving original logic)."""
        df = df.copy()
        
        # Handle column name mapping - check for uppercase and create lowercase versions
        for lower_col, upper_col in [('high', 'High'), ('low', 'Low'), ('close', 'Close'), 
                                   ('volume', 'Volume'), ('timestamp', 'Timestamp')]:
            if upper_col in df.columns and lower_col not in df.columns:
                df[lower_col] = df[upper_col]
        
        # Identify pivot highs (h) and pivot lows (l)
        df['h'] = ((df['high'].shift(5) < df['high'].shift(4)) &
                   (df['high'].shift(4) < df['high'].shift(3)) &
                   (df['high'].shift(3) > df['high'].shift(2)) &
                   (df['high'].shift(2) > df['high'].shift(1))).astype(int)
        df['l'] = ((df['low'].shift(5) > df['low'].shift(4)) &
                   (df['low'].shift(4) > df['low'].shift(3)) &
                   (df['low'].shift(3) < df['low'].shift(2)) &
                   (df['low'].shift(2) < df['low'].shift(1))).astype(int)

        # Count pivots over lookback window
        df['hn'] = df['h'].rolling(self.length).sum()
        df['ln'] = df['l'].rolling(self.length).sum()

        # Assign pivot values
        df['hval'] = np.where(df['h'] == 1, df['high'].shift(3), 0.0)
        df['lval'] = np.where(df['l'] == 1, df['low'].shift(3), 0.0)

        # Sum pivot values
        df['hsum'] = df['hval'].rolling(self.length).sum()
        df['lsum'] = df['lval'].rolling(self.length).sum()

        # Range average
        df['r'] = np.where((df['hn'] > 0) & (df['ln'] > 0),
                           np.abs(df['hsum'] / df['hn'] - df['lsum'] / df['ln']),
                           0.0)

        # Build dynamic support/resistance lines
        df['hvalc'] = np.nan
        df['lvalc'] = np.nan
        df['hvalr'] = np.nan
        df['lvalr'] = np.nan

        for i in range(len(df)):
            if i == 0:
                continue
            if df['h'].iat[i] and df['r'].iat[i] > 0:
                df.at[df.index[i], 'hvalc'] = df['hval'].iat[i]
                df.at[df.index[i], 'hvalr'] = df['hval'].iat[i] - df['r'].iat[i]
            else:
                df.at[df.index[i], 'hvalc'] = df['hvalc'].iat[i-1]
                df.at[df.index[i], 'hvalr'] = df['hvalr'].iat[i-1]

            if df['l'].iat[i] and df['r'].iat[i] > 0:
                df.at[df.index[i], 'lvalc'] = df['lval'].iat[i]
                df.at[df.index[i], 'lvalr'] = df['lval'].iat[i] + df['r'].iat[i]
            else:
                df.at[df.index[i], 'lvalc'] = df['lvalc'].iat[i-1]
                df.at[df.index[i], 'lvalr'] = df['lvalr'].iat[i-1]

        # Determine trend: 1 = bullish, -1 = bearish, carry prior otherwise
        df['trend'] = 0
        for i in range(len(df)):
            if i == 0:
                df.at[df.index[i], 'trend'] = 0
            else:
                close = df['close'].iat[i]
                if (close > df['lvalr'].iat[i]) and (close > df['hvalr'].iat[i]):
                    df.at[df.index[i], 'trend'] = 1
                elif (close < df['lvalr'].iat[i]) and (close < df['hvalr'].iat[i]):
                    df.at[df.index[i], 'trend'] = -1
                else:
                    df.at[df.index[i], 'trend'] = df['trend'].iat[i-1]

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
        
        # Need enough data for indicators (at least 25 bars for pivot calculation)
        if len(self.price_data) < 25:
            return
        
        # Convert to DataFrame for indicator calculation
        df = pd.DataFrame(self.price_data)
        df = self.calculate_indicators(df)
        
        # Get current values
        if len(df) < 1:
            return
            
        curr = df.iloc[-1]
        
        # Update current support/resistance levels
        if not pd.isna(curr['hvalc']):
            self.hvalc = curr['hvalc']
        if not pd.isna(curr['lvalc']):
            self.lvalc = curr['lvalc']
        if not pd.isna(curr['hvalr']):
            self.hvalr = curr['hvalr']
        if not pd.isna(curr['lvalr']):
            self.lvalr = curr['lvalr']
        
        # Update trend
        self.trend = curr['trend']
        
        # Generate entry/exit signals (preserving original logic)
        signal = 0
        
        # Entry conditions (preserving original logic)
        if self.trend == 1 and current_price > self.hvalc and self.position == 0:
            signal = 1   # go long
        elif self.trend == -1 and current_price < self.lvalc and self.position == 0:
            signal = -1  # go short
        
        # Exit conditions (preserving original logic)
        if self.position == 1 and self.trend == -1:
            signal = -1  # exit long
        elif self.position == -1 and self.trend == 1:
            signal = 1   # exit short
        
        # Execute trades based on signals
        if signal == 1 and self.position == 0:
            # Enter long position
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
                print(f"{current_time}: LONG ENTRY for {self.symbol} at {current_price:.2f} (Trend: {self.trend})")
            except Exception as e:
                print(f"{self.name}: Failed to place LONG order: {e}")
                
        elif signal == -1 and self.position == 0:
            # Enter short position
            self.position = -1
            self.entry_price = current_price
            self.entry_time = current_time
            
            # Place order via IBKR
            try:
                order = {
                    'symbol': self.symbol,
                    'qty': self.quantity,
                    'side': 'SELL',
                    'order_type': 'MKT'
                }
                await self.broker.place_order(order)
                print(f"{current_time}: SHORT ENTRY for {self.symbol} at {current_price:.2f} (Trend: {self.trend})")
            except Exception as e:
                print(f"{self.name}: Failed to place SHORT order: {e}")
                
        elif signal == -1 and self.position == 1:
            # Exit long position
            pnl = (current_price - self.entry_price) * self.quantity
            
            # Place exit order via IBKR
            try:
                order = {
                    'symbol': self.symbol,
                    'qty': self.quantity,
                    'side': 'SELL',
                    'order_type': 'MKT'
                }
                await self.broker.place_order(order)
                
                # Record trade
                self.record_trade(
                    entry_time=self.entry_time,
                    exit_time=current_time,
                    symbol=self.symbol,
                    quantity=self.quantity,
                    side='long',
                    entry_price=self.entry_price,
                    exit_price=current_price,
                    pnl=pnl
                )
                
                # Update equity
                self.current_equity += pnl
                print(f"{current_time}: LONG EXIT for {self.symbol} at {current_price:.2f}, PnL: {pnl:.2f}")
                
            except Exception as e:
                print(f"{self.name}: Failed to place LONG EXIT order: {e}")
            
            # Reset position
            self.position = 0
            self.entry_price = 0.0
            self.entry_time = None
            
        elif signal == 1 and self.position == -1:
            # Exit short position
            pnl = (self.entry_price - current_price) * self.quantity
            
            # Place exit order via IBKR
            try:
                order = {
                    'symbol': self.symbol,
                    'qty': self.quantity,
                    'side': 'BUY',
                    'order_type': 'MKT'
                }
                await self.broker.place_order(order)
                
                # Record trade
                self.record_trade(
                    entry_time=self.entry_time,
                    exit_time=current_time,
                    symbol=self.symbol,
                    quantity=self.quantity,
                    side='short',
                    entry_price=self.entry_price,
                    exit_price=current_price,
                    pnl=pnl
                )
                
                # Update equity
                self.current_equity += pnl
                print(f"{current_time}: SHORT EXIT for {self.symbol} at {current_price:.2f}, PnL: {pnl:.2f}")
                
            except Exception as e:
                print(f"{self.name}: Failed to place SHORT EXIT order: {e}")
            
            # Reset position
            self.position = 0
            self.entry_price = 0.0
            self.entry_time = None

    def backtest(self, df):
        """
        Legacy backtest method for compatibility (preserving original logic).
        This method is kept for backward compatibility but the main execution
        should use the IBKR framework via on_bar().
        """
        df = df.copy()
        
        # Identify pivot highs (h) and pivot lows (l)
        df['h'] = ((df['High'].shift(5) < df['High'].shift(4)) &
                   (df['High'].shift(4) < df['High'].shift(3)) &
                   (df['High'].shift(3) > df['High'].shift(2)) &
                   (df['High'].shift(2) > df['High'].shift(1))).astype(int)
        df['l'] = ((df['Low'].shift(5) > df['Low'].shift(4)) &
                   (df['Low'].shift(4) > df['Low'].shift(3)) &
                   (df['Low'].shift(3) < df['Low'].shift(2)) &
                   (df['Low'].shift(2) < df['Low'].shift(1))).astype(int)

        # Count pivots over lookback window
        df['hn'] = df['h'].rolling(self.length).sum()
        df['ln'] = df['l'].rolling(self.length).sum()

        # Assign pivot values
        df['hval'] = np.where(df['h'] == 1, df['High'].shift(3), 0.0)
        df['lval'] = np.where(df['l'] == 1, df['Low'].shift(3), 0.0)

        # Sum pivot values
        df['hsum'] = df['hval'].rolling(self.length).sum()
        df['lsum'] = df['lval'].rolling(self.length).sum()

        # Range average
        df['r'] = np.where((df['hn'] > 0) & (df['ln'] > 0),
                           np.abs(df['hsum'] / df['hn'] - df['lsum'] / df['ln']),
                           0.0)

        # Build dynamic support/resistance lines
        df['hvalc'] = np.nan
        df['lvalc'] = np.nan
        df['hvalr'] = np.nan
        df['lvalr'] = np.nan

        for i in range(len(df)):
            if i == 0:
                continue
            if df['h'].iat[i] and df['r'].iat[i] > 0:
                df.at[df.index[i], 'hvalc'] = df['hval'].iat[i]
                df.at[df.index[i], 'hvalr'] = df['hval'].iat[i] - df['r'].iat[i]
            else:
                df.at[df.index[i], 'hvalc'] = df['hvalc'].iat[i-1]
                df.at[df.index[i], 'hvalr'] = df['hvalr'].iat[i-1]

            if df['l'].iat[i] and df['r'].iat[i] > 0:
                df.at[df.index[i], 'lvalc'] = df['lval'].iat[i]
                df.at[df.index[i], 'lvalr'] = df['lval'].iat[i] + df['r'].iat[i]
            else:
                df.at[df.index[i], 'lvalc'] = df['lvalc'].iat[i-1]
                df.at[df.index[i], 'lvalr'] = df['lvalr'].iat[i-1]

        # Determine trend: 1 = bullish, -1 = bearish, carry prior otherwise
        df['trend'] = 0
        for i in range(len(df)):
            if i == 0:
                df.at[df.index[i], 'trend'] = 0
            else:
                close = df['Close'].iat[i]
                if (close > df['lvalr'].iat[i]) and (close > df['hvalr'].iat[i]):
                    df.at[df.index[i], 'trend'] = 1
                elif (close < df['lvalr'].iat[i]) and (close < df['hvalr'].iat[i]):
                    df.at[df.index[i], 'trend'] = -1
                else:
                    df.at[df.index[i], 'trend'] = df['trend'].iat[i-1]

        # Generate entry/exit signals
        df['signal'] = 0
        for i in range(len(df)):
            if df['trend'].iat[i] == 1 and df['Close'].iat[i] > df['hvalc'].iat[i]:
                df.at[df.index[i], 'signal'] = 1   # go long
            elif df['trend'].iat[i] == -1 and df['Close'].iat[i] < df['lvalc'].iat[i]:
                df.at[df.index[i], 'signal'] = -1  # go short

        # Exits: flip or close opposing
        df['exit'] = 0
        df['exit'] = np.where(df['trend'] == -1, 1, np.where(df['trend'] == 1, -1, 0))

        return df[['High','Low','Close','hvalc','hvalr','lvalc','lvalr','trend','signal','exit']]

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
