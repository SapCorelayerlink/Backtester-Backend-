import pandas as pd
import numpy as np
from core.base import StrategyBase
from core.registry import StrategyRegistry

@StrategyRegistry.register("SwingFailureStrategy")
class SwingFailureStrategy(StrategyBase):
    """
    Swing Failure Pattern Strategy adapted for the IBKR framework.
    Preserves all original trading conditions and logic.
    """
    
    def __init__(self, name: str, broker: 'BrokerBase', params: dict = None):
        super().__init__(name, broker, params)
        
        # Strategy parameters (preserving original conditions)
        self.swing_period = self.params.get('swing_period', 50)
        self.max_swing_back = self.params.get('max_swing_back', 100)
        self.back_to_break = self.params.get('back_to_break', 4)
        self.sfp_type = self.params.get('sfp_type', 'Real SFP')
        
        # Trading parameters
        self.symbol = self.params.get('symbol', 'AAPL')
        self.timeframe = self.params.get('timeframe', '1h')  # 1-hour bars
        self.quantity = self.params.get('quantity', 100)
        
        # State variables
        self.position = 0  # 0 = no position, 1 = long, -1 = short
        self.entry_price = 0.0
        self.entry_time = None
        
        # Data storage
        self.price_data = []

    async def init(self):
        """Initialize the strategy by pre-loading historical data."""
        print(f"Initializing {self.name} Swing Failure strategy")
        print(f"Parameters: Swing Period({self.swing_period}), Max Swing Back({self.max_swing_back})")
        print(f"Back to Break: {self.back_to_break}, SFP Type: {self.sfp_type}")
        print(f"Symbol: {self.symbol}, Timeframe: {self.timeframe} (1-hour bars)")
        print(f"{self.name}: Initialization complete.")

    def detect_sfp(self, df):
        """
        Detect Swing Failure Patterns on 1H OHLC data (preserving original logic).
        Returns a DataFrame with boolean flags 'sfp_high' and 'sfp_low'.
        """
        df = df.copy()
        
        # Handle column name mapping - check for uppercase and create lowercase versions
        for lower_col, upper_col in [('high', 'High'), ('low', 'Low'), ('close', 'Close'), 
                                   ('volume', 'Volume'), ('timestamp', 'Timestamp')]:
            if upper_col in df.columns and lower_col not in df.columns:
                df[lower_col] = df[upper_col]
        
        # Identify pivot highs/lows
        df['pivot_high'] = (
            (df['high'].shift(self.swing_period) >
             df['high'].shift(self.swing_period+1)) &
            (df['high'].shift(self.swing_period) >
             df['high'].shift(self.swing_period-1))
        )
        df['pivot_low'] = (
            (df['low'].shift(self.swing_period) <
             df['low'].shift(self.swing_period+1)) &
            (df['low'].shift(self.swing_period) <
             df['low'].shift(self.swing_period-1))
        )

        # Collect pivot prices and times
        piv_h = []  # list of (idx, price)
        piv_l = []
        df['sfp_high'] = False
        df['sfp_low'] = False

        for i in range(len(df)):
            idx = df.index[i]
            row = df.iloc[i]

            # Register new pivot
            if row['pivot_high']:
                piv_h.append((idx, row['high']))
            if row['pivot_low']:
                piv_l.append((idx, row['low']))

            # Keep only last max_swing_back pivots
            if len(piv_h) > self.max_swing_back:
                piv_h.pop(0)
            if len(piv_l) > self.max_swing_back:
                piv_l.pop(0)

            # Check high-SFP: price retraces into pivot high then closes below its low end
            for pivot_idx, price in reversed(piv_h):
                bars_since = (idx - pivot_idx) / pd.Timedelta('1H')
                if bars_since <= self.back_to_break:
                    # Real SFP: high pivot > current high > current close
                    cond_real = (price > row['high'] > row['close'])
                    # Considerable SFP: price dipped then close < prior close
                    cond_cons = (row['close'] < df['close'].shift(1).iat[i]
                                 and row['low'] < df['low'].shift(1).iat[i])
                    if (self.sfp_type in ['All', 'Real SFP'] and cond_real) or \
                       (self.sfp_type in ['All', 'Considerable SFP'] and cond_cons):
                        df.at[idx, 'sfp_high'] = True
                        break
                else:
                    break

            # Check low-SFP similarly
            for pivot_idx, price in reversed(piv_l):
                bars_since = (idx - pivot_idx) / pd.Timedelta('1H')
                if bars_since <= self.back_to_break:
                    cond_real = (price < row['low'] < row['close'])
                    cond_cons = (row['close'] > df['close'].shift(1).iat[i]
                                 and row['high'] > df['high'].shift(1).iat[i])
                    if (self.sfp_type in ['All', 'Real SFP'] and cond_real) or \
                       (self.sfp_type in ['All', 'Considerable SFP'] and cond_cons):
                        df.at[idx, 'sfp_low'] = True
                        break
                else:
                    break

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
        
        # Need enough data for indicators (at least swing_period + 10 bars)
        if len(self.price_data) < self.swing_period + 10:
            return
        
        # Convert to DataFrame for indicator calculation
        df = pd.DataFrame(self.price_data)
        df = self.detect_sfp(df)
        
        # Get current values
        if len(df) < 1:
            return
            
        curr = df.iloc[-1]
        
        # Trading logic based on SFP signals (preserving original logic)
        # High SFP (bearish signal) - go short
        if curr['sfp_high'] and self.position == 0:
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
                print(f"{current_time}: SFP SHORT ENTRY for {self.symbol} at {current_price:.2f} (High SFP)")
            except Exception as e:
                print(f"{self.name}: Failed to place SFP SHORT order: {e}")
                
        # Low SFP (bullish signal) - go long
        elif curr['sfp_low'] and self.position == 0:
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
                print(f"{current_time}: SFP LONG ENTRY for {self.symbol} at {current_price:.2f} (Low SFP)")
            except Exception as e:
                print(f"{self.name}: Failed to place SFP LONG order: {e}")
                
        # Exit conditions - opposite SFP signal
        elif self.position == 1 and curr['sfp_high']:
            # Exit long position on high SFP
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
                print(f"{current_time}: SFP LONG EXIT for {self.symbol} at {current_price:.2f}, PnL: {pnl:.2f}")
                
            except Exception as e:
                print(f"{self.name}: Failed to place SFP LONG EXIT order: {e}")
            
            # Reset position
            self.position = 0
            self.entry_price = 0.0
            self.entry_time = None
            
        elif self.position == -1 and curr['sfp_low']:
            # Exit short position on low SFP
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
                print(f"{current_time}: SFP SHORT EXIT for {self.symbol} at {current_price:.2f}, PnL: {pnl:.2f}")
                
            except Exception as e:
                print(f"{self.name}: Failed to place SFP SHORT EXIT order: {e}")
            
            # Reset position
            self.position = 0
            self.entry_price = 0.0
            self.entry_time = None

    def detect_sfp_legacy(self, df,
                         swing_period=50,
                         max_swing_back=100,
                         back_to_break=4,
                         sfp_type='Real SFP'):
        """
        Legacy SFP detection method for compatibility (preserving original logic).
        This method is kept for backward compatibility but the main execution
        should use the IBKR framework via on_bar().
        """
        df = df.copy()
        # Identify pivot highs/lows
        df['pivot_high'] = (
            (df['High'].shift(swing_period) >
             df['High'].shift(swing_period+1)) &
            (df['High'].shift(swing_period) >
             df['High'].shift(swing_period-1))
        )
        df['pivot_low'] = (
            (df['Low'].shift(swing_period) <
             df['Low'].shift(swing_period+1)) &
            (df['Low'].shift(swing_period) <
             df['Low'].shift(swing_period-1))
        )

        # Collect pivot prices and times
        piv_h = []  # list of (idx, price)
        piv_l = []
        df['SFP_High'] = False
        df['SFP_Low'] = False

        for i in range(len(df)):
            idx = df.index[i]
            row = df.iloc[i]

            # Register new pivot
            if row['pivot_high']:
                piv_h.append((idx, row['High']))
            if row['pivot_low']:
                piv_l.append((idx, row['Low']))

            # Keep only last max_swing_back pivots
            if len(piv_h) > max_swing_back:
                piv_h.pop(0)
            if len(piv_l) > max_swing_back:
                piv_l.pop(0)

            # Check high-SFP: price retraces into pivot high then closes below its low end
            for pivot_idx, price in reversed(piv_h):
                bars_since = (idx - pivot_idx) / pd.Timedelta('1H')
                if bars_since <= back_to_break:
                    # Real SFP: high pivot > current high > current close
                    cond_real = (price > row['High'] > row['Close'])
                    # Considerable SFP: price dipped then close < prior close
                    cond_cons = (row['Close'] < df['Close'].shift(1).iat[i]
                                 and row['Low'] < df['Low'].shift(1).iat[i])
                    if (sfp_type in ['All', 'Real SFP'] and cond_real) or \
                       (sfp_type in ['All', 'Considerable SFP'] and cond_cons):
                        df.at[idx, 'SFP_High'] = True
                        break
                else:
                    break

            # Check low-SFP similarly
            for pivot_idx, price in reversed(piv_l):
                bars_since = (idx - pivot_idx) / pd.Timedelta('1H')
                if bars_since <= back_to_break:
                    cond_real = (price < row['Low'] < row['Close'])
                    cond_cons = (row['Close'] > df['Close'].shift(1).iat[i]
                                 and row['High'] > df['High'].shift(1).iat[i])
                    if (sfp_type in ['All', 'Real SFP'] and cond_real) or \
                       (sfp_type in ['All', 'Considerable SFP'] and cond_cons):
                        df.at[idx, 'SFP_Low'] = True
                        break
                else:
                    break

        return df

# Legacy function for backward compatibility
def detect_sfp(df,
               swing_period=50,
               max_swing_back=100,
               back_to_break=4,
               sfp_type='Real SFP'):
    """
    Detect Swing Failure Patterns on 1H OHLC data (legacy function).
    
    Returns a DataFrame with boolean flags 'SFP_High' and 'SFP_Low'.
    """
    strategy = SwingFailureStrategy(
        name="LegacySwingFailure",
        broker=None,  # Not used in legacy mode
        params={
            'swing_period': swing_period,
            'max_swing_back': max_swing_back,
            'back_to_break': back_to_break,
            'sfp_type': sfp_type
        }
    )
    
    return strategy.detect_sfp_legacy(df, swing_period, max_swing_back, back_to_break, sfp_type)

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
