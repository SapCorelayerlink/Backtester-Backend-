import pandas as pd
import numpy as np
from core.base import StrategyBase
from core.registry import StrategyRegistry

@StrategyRegistry.register("BB5EMAStrategy")
class BB5EMAStrategy(StrategyBase):
    """
    Combined Bollinger Band & 5-EMA Strategy adapted for the IBKR framework.
    Preserves all original trading conditions and logic.
    """
    
    def __init__(self, name: str, broker: 'BrokerBase', params: dict = None):
        super().__init__(name, broker, params)
        
        # Strategy parameters (preserving original conditions)
        self.bb_length = self.params.get('bb_length', 20)
        self.bb_std = self.params.get('bb_std', 1.5)
        self.ema_length = self.params.get('ema_length', 5)
        self.extra_sl = self.params.get('extra_sl', False)
        self.sl_buffer = self.params.get('sl_buffer', 5)
        self.rrr_bb = self.params.get('rrr_bb', 4)
        self.rrr_combined = self.params.get('rrr_combined', 3)
        self.candle_condition = self.params.get('candle_condition', False)
        self.show_signals = self.params.get('show_signals', True)
        
        # Trading parameters
        self.symbol = self.params.get('symbol', 'AAPL')
        self.timeframe = self.params.get('timeframe', '4h')  # 4-hour bars
        self.quantity = self.params.get('quantity', 100)
        
        # State variables
        self.position = 0  # 0 = no position, 1 = long, -1 = short
        self.entry_price = 0.0
        self.entry_time = None
        self.in_long = False
        self.long_entry_price = 0.0
        self.sl = 0.0
        self.tp = 0.0
        
        # Data storage
        self.price_data = []

    async def init(self):
        """Initialize the strategy by pre-loading historical data."""
        print(f"Initializing {self.name} Bollinger + 5EMA strategy")
        print(f"Parameters: BB Length({self.bb_length}), BB Std({self.bb_std})")
        print(f"EMA Length: {self.ema_length}, Extra SL: {self.extra_sl}")
        print(f"RRR BB: {self.rrr_bb}, RRR Combined: {self.rrr_combined}")
        print(f"Symbol: {self.symbol}, Timeframe: {self.timeframe} (4-hour bars)")
        print(f"{self.name}: Initialization complete.")

    def calculate_indicators(self, df):
        """Calculate Bollinger Bands and EMA indicators (preserving original logic)."""
        df = df.copy()
        
        # Handle column name mapping - check for uppercase and create lowercase versions
        for lower_col, upper_col in [('high', 'High'), ('low', 'Low'), ('close', 'Close'), 
                                   ('volume', 'Volume'), ('timestamp', 'Timestamp')]:
            if upper_col in df.columns and lower_col not in df.columns:
                df[lower_col] = df[upper_col]
        
        # Bollinger Bands
        df['basis_bb'] = df['close'].rolling(self.bb_length).mean()
        df['std_bb'] = df['close'].rolling(self.bb_length).std()
        df['upper_bb'] = df['basis_bb'] + self.bb_std * df['std_bb']
        df['lower_bb'] = df['basis_bb'] - self.bb_std * df['std_bb']

        # 5-period EMA
        df['ema5'] = df['close'].ewm(span=self.ema_length, adjust=False).mean()
        
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
        if len(self.price_data) < self.bb_length:
            return
        
        # Convert to DataFrame for indicator calculation
        df = pd.DataFrame(self.price_data)
        df = self.calculate_indicators(df)
        
        # Get current and previous values
        if len(df) < 2:
            return
            
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Conditions for combined strategy (price crosses below lower BB and EMA) - preserving original logic
        cond_buy_bb = prev['low'] < prev['lower_bb'] and curr['high'] > curr['lower_bb']
        cond_buy_ema = prev['low'] < prev['ema5'] and curr['high'] > curr['ema5']
        cond_buy = cond_buy_bb and cond_buy_ema

        if self.candle_condition:
            cond_buy = cond_buy and curr['close'] > prev['close']

        # Pure BB trap (cross below lower BB only) - preserving original logic
        pure_bb_buy = prev['low'] < prev['lower_bb'] and curr['high'] > curr['lower_bb']
        if self.candle_condition:
            pure_bb_buy = pure_bb_buy and curr['close'] > prev['close']

        # Combined SELL conditions (cross above upper BB + EMA) - preserving original logic
        cond_sell_bb = prev['high'] > prev['upper_bb'] and curr['low'] < curr['upper_bb']
        cond_sell_ema = prev['high'] > prev['ema5'] and curr['low'] < curr['ema5']
        cond_sell = cond_sell_bb and cond_sell_ema

        if self.candle_condition:
            cond_sell = cond_sell and curr['close'] < prev['close']

        pure_bb_sell = prev['high'] > prev['upper_bb'] and curr['low'] < curr['upper_bb']
        if self.candle_condition:
            pure_bb_sell = pure_bb_sell and curr['close'] < prev['close']

        # Entry logic (preserving original logic)
        if not self.in_long:
            if cond_buy:
                self.in_long = True
                self.long_entry_price = current_price
                # stop-loss below lowest of BB and EMA cross + buffer
                self.sl = (curr['lower_bb'] if cond_buy_bb else curr['ema5']) - (self.sl_buffer if self.extra_sl else 0)
                # take-profit based on combined RRR
                self.tp = self.long_entry_price + (self.long_entry_price - self.sl) * self.rrr_combined
                
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
                    print(f"{current_time}: BB5EMA LONG ENTRY for {self.symbol} at {current_price:.2f} (Combined)")
                except Exception as e:
                    print(f"{self.name}: Failed to place BB5EMA LONG order: {e}")
                    
            elif pure_bb_buy:
                self.in_long = True
                self.long_entry_price = current_price
                self.sl = curr['lower_bb'] - (self.sl_buffer if self.extra_sl else 0)
                self.tp = self.long_entry_price + (self.long_entry_price - self.sl) * self.rrr_bb
                
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
                    print(f"{current_time}: BB5EMA LONG ENTRY for {self.symbol} at {current_price:.2f} (Pure BB)")
                except Exception as e:
                    print(f"{self.name}: Failed to place BB5EMA LONG order: {e}")

        # Exit logic (preserving original logic)
        if self.in_long:
            # stop-loss hit
            if low <= self.sl:
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
                    print(f"{current_time}: BB5EMA STOP LOSS for {self.symbol} at {current_price:.2f}, PnL: {pnl:.2f}")
                    
                except Exception as e:
                    print(f"{self.name}: Failed to place BB5EMA STOP LOSS order: {e}")
                
                # Reset position
                self.in_long = False
                self.position = 0
                self.entry_price = 0.0
                self.entry_time = None
                
            # take-profit hit
            elif high >= self.tp:
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
                    print(f"{current_time}: BB5EMA TAKE PROFIT for {self.symbol} at {current_price:.2f}, PnL: {pnl:.2f}")
                    
                except Exception as e:
                    print(f"{self.name}: Failed to place BB5EMA TAKE PROFIT order: {e}")
                
                # Reset position
                self.in_long = False
                self.position = 0
                self.entry_price = 0.0
                self.entry_time = None

    def bb_5ema_strategy(self, df):
        """
        Legacy strategy method for compatibility (preserving original logic).
        This method is kept for backward compatibility but the main execution
        should use the IBKR framework via on_bar().
        """
        df = df.copy()
        
        # Bollinger Bands
        df['basis_bb'] = df['Close'].rolling(self.bb_length).mean()
        df['std_bb'] = df['Close'].rolling(self.bb_length).std()
        df['upper_bb'] = df['basis_bb'] + self.bb_std * df['std_bb']
        df['lower_bb'] = df['basis_bb'] - self.bb_std * df['std_bb']

        # 5-period EMA
        df['ema5'] = df['Close'].ewm(span=self.ema_length, adjust=False).mean()

        # Initialize signal columns
        df['signal'] = 0
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan

        # State trackers
        in_long = False
        long_entry_price = 0.0
        sl = tp = 0.0

        for i in range(1, len(df)):
            prev = df.iloc[i-1]
            curr = df.iloc[i]

            # Conditions for combined strategy (price crosses below lower BB and EMA)
            cond_buy_bb = prev['Low'] < prev['lower_bb'] and curr['High'] > curr['lower_bb']
            cond_buy_ema = prev['Low'] < prev['ema5'] and curr['High'] > curr['ema5']
            cond_buy = cond_buy_bb and cond_buy_ema

            if self.candle_condition:
                cond_buy = cond_buy and curr['Close'] > prev['Close']

            # Pure BB trap (cross below lower BB only)
            pure_bb_buy = prev['Low'] < prev['lower_bb'] and curr['High'] > curr['lower_bb']
            if self.candle_condition:
                pure_bb_buy = pure_bb_buy and curr['Close'] > prev['Close']

            # Combined SELL conditions (cross above upper BB + EMA)
            cond_sell_bb = prev['High'] > prev['upper_bb'] and curr['Low'] < curr['upper_bb']
            cond_sell_ema = prev['High'] > prev['ema5'] and curr['Low'] < curr['ema5']
            cond_sell = cond_sell_bb and cond_sell_ema

            if self.candle_condition:
                cond_sell = cond_sell and curr['Close'] < prev['Close']

            pure_bb_sell = prev['High'] > prev['upper_bb'] and curr['Low'] < curr['upper_bb']
            if self.candle_condition:
                pure_bb_sell = pure_bb_sell and curr['Close'] < prev['Close']

            # Entry logic
            if not in_long:
                if cond_buy:
                    in_long = True
                    long_entry_price = curr['Close']
                    # stop-loss below lowest of BB and EMA cross + buffer
                    sl = (curr['lower_bb'] if cond_buy_bb else curr['ema5']) - (self.sl_buffer if self.extra_sl else 0)
                    # take-profit based on combined RRR
                    tp = long_entry_price + (long_entry_price - sl) * self.rrr_combined
                    df.iat[i, df.columns.get_loc('signal')] = 1
                elif pure_bb_buy:
                    in_long = True
                    long_entry_price = curr['Close']
                    sl = curr['lower_bb'] - (self.sl_buffer if self.extra_sl else 0)
                    tp = long_entry_price + (long_entry_price - sl) * self.rrr_bb
                    df.iat[i, df.columns.get_loc('signal')] = 1

            # Exit logic
            if in_long:
                # stop-loss hit
                if curr['Low'] <= sl:
                    df.iat[i, df.columns.get_loc('signal')] = -1
                    in_long = False
                # take-profit hit
                elif curr['High'] >= tp:
                    df.iat[i, df.columns.get_loc('signal')] = -1
                    in_long = False

            # Record SL/TP for plotting or backtesting
            df.iat[i, df.columns.get_loc('stop_loss')] = sl if in_long else np.nan
            df.iat[i, df.columns.get_loc('take_profit')] = tp if in_long else np.nan

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
def bb_5ema_strategy(df,
                     bb_length=20,
                     bb_std=1.5,
                     ema_length=5,
                     extra_sl=False,
                     sl_buffer=5,
                     rrr_bb=4,
                     rrr_combined=3,
                     candle_condition=False,
                     show_signals=True):
    """
    Combined Bollinger Band & 5-EMA strategy (legacy function).
    
    Parameters:
    - df: DataFrame with ['Open','High','Low','Close','Volume']
    - bb_length: lookback for Bollinger basis
    - bb_std: standard-deviation multiplier
    - ema_length: lookback for 5-EMA
    - extra_sl: enable extra SL buffer
    - sl_buffer: number of points for extra SL
    - rrr_bb: risk-reward ratio for pure BB trades
    - rrr_combined: risk-reward ratio for combined BB+5EMA trades
    - candle_condition: require close vs prior close for entries
    - show_signals: whether to mark signals

    Returns:
    DataFrame with added columns:
    - upper_bb, lower_bb, basis_bb, ema5
    - signal (1=buy, -1=sell, 0=none)
    - stop_loss, take_profit
    """
    
    strategy = BB5EMAStrategy(
        name="LegacyBB5EMA",
        broker=None,  # Not used in legacy mode
        params={
            'bb_length': bb_length,
            'bb_std': bb_std,
            'ema_length': ema_length,
            'extra_sl': extra_sl,
            'sl_buffer': sl_buffer,
            'rrr_bb': rrr_bb,
            'rrr_combined': rrr_combined,
            'candle_condition': candle_condition,
            'show_signals': show_signals
        }
    )
    
    return strategy.bb_5ema_strategy(df)
