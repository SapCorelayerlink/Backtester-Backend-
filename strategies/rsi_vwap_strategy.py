import pandas as pd
import numpy as np
from core.base import StrategyBase
from core.registry import StrategyRegistry

@StrategyRegistry.register("RSIVWAPStrategy")
class RSIVWAPStrategy(StrategyBase):
    """
    RSI + VWAP Strategy adapted for the IBKR framework.
    Preserves all original trading conditions and logic.
    """
    
    def __init__(self, name: str, broker: 'BrokerBase', params: dict = None):
        super().__init__(name, broker, params)
        
        # Strategy parameters (preserving original conditions)
        self.rsi_length_long = self.params.get('rsi_length_long', 17)
        self.oversold_long = self.params.get('oversold_long', 19)
        self.oversold2_long = self.params.get('oversold2_long', 38)
        self.overbought_long = self.params.get('overbought_long', 78)
        self.rsi_length_short = self.params.get('rsi_length_short', 17)
        self.oversold_short = self.params.get('oversold_short', 19)
        self.overbought_short = self.params.get('overbought_short', 80)
        self.overbought2_short = self.params.get('overbought2_short', 59)
        self.max_pyramiding = self.params.get('max_pyramiding', 10)
        self.stop_loss_pct = self.params.get('stop_loss_pct', 0.10)
        self.take_profit_pct = self.params.get('take_profit_pct', 0.05)
        self.partial_tp_pct = self.params.get('partial_tp_pct', 0.50)
        
        # Trading parameters
        self.symbol = self.params.get('symbol', 'AAPL')
        self.timeframe = self.params.get('timeframe', '4h')  # 4-hour bars
        self.quantity = self.params.get('quantity', 100)
        
        # State variables (preserving original logic)
        self.in_long = False
        self.in_short = False
        self.n_longs = 0
        self.n_shorts = 0
        self.entry_price = 0.0
        self.position_size = 0
        self.avg_price = 0.0
        
        # Data storage
        self.price_data = []
        self.vwap_values = []
        self.rsi_vwap_long_values = []
        self.rsi_vwap_short_values = []

    async def init(self):
        """Initialize the strategy by pre-loading historical data."""
        print(f"Initializing {self.name} RSI+VWAP strategy")
        print(f"Parameters: RSI Long({self.rsi_length_long}), Short({self.rsi_length_short})")
        print(f"Oversold Long: {self.oversold_long}, {self.oversold2_long}")
        print(f"Overbought Short: {self.overbought_short}, {self.overbought2_short}")
        print(f"Stop Loss: {self.stop_loss_pct:.1%}, Take Profit: {self.take_profit_pct:.1%}")
        print(f"Timeframe: {self.timeframe} (4-hour bars)")
        print(f"{self.name}: Initialization complete.")

    def prepare_indicators(self, df):
        """Calculate VWAP and RSI indicators (preserving original logic)."""
        # VWAP calculation
        cum_vol = df['volume'].cumsum()
        cum_vwap = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum()
        df['vwap'] = cum_vwap / cum_vol
        
        # RSI on VWAP for long
        delta = df['vwap'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(self.rsi_length_long).mean()
        avg_loss = loss.rolling(self.rsi_length_long).mean()
        rs = avg_gain / avg_loss
        df['rsi_vwap_long'] = 100 - (100 / (1 + rs))
        
        # RSI on VWAP for short (using same VWAP RSI length)
        df['rsi_vwap_short'] = df['rsi_vwap_long']
        
        return df

    async def on_bar(self, bar_data: pd.Series):
        """Process each new bar and execute trading logic (preserving original conditions)."""
        # Extract bar data
        current_price = bar_data['close']
        current_time = bar_data['timestamp']
        high = bar_data['high']
        low = bar_data['low']
        volume = bar_data.get('volume', 100)
        
        # Add to price data
        self.price_data.append({
            'timestamp': current_time,
            'open': bar_data['open'],
            'high': high,
            'low': low,
            'close': current_price,
            'volume': volume
        })
        
        # Need enough data for indicators
        if len(self.price_data) < max(self.rsi_length_long, 20):
            return
        
        # Convert to DataFrame for indicator calculation
        df = pd.DataFrame(self.price_data)
        df = self.prepare_indicators(df)
        
        # Get current and previous values
        if len(df) < 2:
            return
            
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Long entry conditions (preserving original logic)
        cond1 = (prev['rsi_vwap_long'] < self.oversold_long and
                 curr['rsi_vwap_long'] > self.oversold_long and self.n_longs < self.max_pyramiding)
        cond2 = (prev['rsi_vwap_long'] < self.oversold2_long and
                 curr['rsi_vwap_long'] > self.oversold2_long and self.n_longs < self.max_pyramiding)

        # Short entry conditions (preserving original logic)
        cond3 = (prev['rsi_vwap_short'] > self.overbought_short and
                 curr['rsi_vwap_short'] < self.overbought_short and self.n_shorts < self.max_pyramiding)
        cond4 = (prev['rsi_vwap_short'] > self.overbought2_short and
                 curr['rsi_vwap_short'] < self.overbought2_short and self.n_shorts < self.max_pyramiding)

        # Exit conditions (preserving original logic)
        stop_long = low <= self.entry_price * (1 - self.stop_loss_pct)
        tp_long = high >= self.entry_price * (1 + self.take_profit_pct)
        stop_short = high >= self.entry_price * (1 + self.stop_loss_pct)
        tp_short = low <= self.entry_price * (1 - self.take_profit_pct)

        # Handle long entries & pyramiding (preserving original logic)
        if (cond1 or cond2) and not self.in_long:
            self.in_long = True
            self.n_longs += 1
            self.entry_price = current_price
            self.position_size = 1
            self.avg_price = self.entry_price
            
            # Place order via IBKR
            try:
                order = {
                    'symbol': self.symbol,
                    'qty': self.quantity,
                    'side': 'BUY',
                    'order_type': 'market'
                }
                await self.broker.place_order(order)
                print(f"{current_time}: LONG ENTRY for {self.symbol} at {current_price:.2f} (RSI: {curr['rsi_vwap_long']:.1f})")
            except Exception as e:
                print(f"{self.name}: Failed to place LONG order: {e}")

        elif self.in_long and (stop_long or tp_long):
            # Exit entire long position
            self.in_long = False
            pnl = (current_price - self.avg_price) * self.position_size
            
            # Place exit order via IBKR
            try:
                order = {
                    'symbol': self.symbol,
                    'qty': self.quantity,
                    'side': 'SELL',
                    'order_type': 'market'
                }
                await self.broker.place_order(order)
                
                # Record trade
                self.record_trade(
                    entry_time=self.entry_time if hasattr(self, 'entry_time') else current_time,
                    exit_time=current_time,
                    symbol=self.symbol,
                    quantity=self.quantity,
                    side='long',
                    entry_price=self.avg_price,
                    exit_price=current_price,
                    pnl=pnl
                )
                
                # Update equity
                self.current_equity += pnl
                print(f"{current_time}: LONG EXIT for {self.symbol} at {current_price:.2f}, PnL: {pnl:.2f}")
                
            except Exception as e:
                print(f"{self.name}: Failed to place LONG EXIT order: {e}")
            
            self.n_longs = 0
            self.entry_price = 0.0
            self.avg_price = 0.0

        # Handle short entries & pyramiding (preserving original logic)
        if (cond3 or cond4) and not self.in_short:
            self.in_short = True
            self.n_shorts += 1
            self.entry_price = current_price
            self.position_size = 1
            self.avg_price = self.entry_price
            
            # Place order via IBKR
            try:
                order = {
                    'symbol': self.symbol,
                    'qty': self.quantity,
                    'side': 'SELL',
                    'order_type': 'market'
                }
                await self.broker.place_order(order)
                print(f"{current_time}: SHORT ENTRY for {self.symbol} at {current_price:.2f} (RSI: {curr['rsi_vwap_short']:.1f})")
            except Exception as e:
                print(f"{self.name}: Failed to place SHORT order: {e}")

        elif self.in_short and (stop_short or tp_short):
            # Exit entire short position
            self.in_short = False
            pnl = (self.avg_price - current_price) * self.position_size
            
            # Place exit order via IBKR
            try:
                order = {
                    'symbol': self.symbol,
                    'qty': self.quantity,
                    'side': 'BUY',
                    'order_type': 'market'
                }
                await self.broker.place_order(order)
                
                # Record trade
                self.record_trade(
                    entry_time=self.entry_time if hasattr(self, 'entry_time') else current_time,
                    exit_time=current_time,
                    symbol=self.symbol,
                    quantity=self.quantity,
                    side='short',
                    entry_price=self.avg_price,
                    exit_price=current_price,
                    pnl=pnl
                )
                
                # Update equity
                self.current_equity += pnl
                print(f"{current_time}: SHORT EXIT for {self.symbol} at {current_price:.2f}, PnL: {pnl:.2f}")
                
            except Exception as e:
                print(f"{self.name}: Failed to place SHORT EXIT order: {e}")
            
            self.n_shorts = 0
            self.entry_price = 0.0
            self.avg_price = 0.0

    def run_backtest(self, df):
        """
        Legacy backtest method for compatibility (preserving original logic).
        This method is kept for backward compatibility but the main execution
        should use the IBKR framework via on_bar().
        """
        df = df.copy()
        self.prepare_indicators(df)
        
        # Filter by date range if specified
        start_date = self.params.get('start_date')
        end_date = self.params.get('end_date')
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]

        # State variables
        in_long = False
        in_short = False
        n_longs = 0
        n_shorts = 0
        entry_price = 0.0
        position_size = 0
        avg_price = 0.0

        # Results
        df['signal'] = 0
        df['position'] = 0
        df['avg_price'] = np.nan
        df['pnl'] = 0.0

        for i in range(1, len(df)):
            prev = df.iloc[i-1]
            curr = df.iloc[i]
            idx = df.index[i]

            # Long entry conditions
            cond1 = (prev['rsi_vwap_long'] < self.oversold_long and
                     curr['rsi_vwap_long'] > self.oversold_long and n_longs < self.max_pyramiding)
            cond2 = (prev['rsi_vwap_long'] < self.oversold2_long and
                     curr['rsi_vwap_long'] > self.oversold2_long and n_longs < self.max_pyramiding)

            # Short entry conditions
            cond3 = (prev['rsi_vwap_short'] > self.overbought_short and
                     curr['rsi_vwap_short'] < self.overbought_short and n_shorts < self.max_pyramiding)
            cond4 = (prev['rsi_vwap_short'] > self.overbought2_short and
                     curr['rsi_vwap_short'] < self.overbought2_short and n_shorts < self.max_pyramiding)

            # Exit conditions
            stop_long = curr['low'] <= entry_price * (1 - self.stop_loss_pct)
            tp_long = curr['high'] >= entry_price * (1 + self.take_profit_pct)
            stop_short = curr['high'] >= entry_price * (1 + self.stop_loss_pct)
            tp_short = curr['low'] <= entry_price * (1 - self.take_profit_pct)

            # Handle long entries & pyramiding
            if (cond1 or cond2) and not in_long:
                in_long = True
                n_longs += 1
                entry_price = curr['close']
                position_size = 1
                avg_price = entry_price

            elif in_long and (stop_long or tp_long):
                # exit entire long
                in_long = False
                pnl = (curr['close'] - avg_price) * position_size
                df.at[idx, 'pnl'] = pnl
                n_longs = 0

            # Handle short entries & pyramiding
            if (cond3 or cond4) and not in_short:
                in_short = True
                n_shorts += 1
                entry_price = curr['close']
                position_size = 1
                avg_price = entry_price

            elif in_short and (stop_short or tp_short):
                in_short = False
                pnl = (avg_price - curr['close']) * position_size
                df.at[idx, 'pnl'] = pnl
                n_shorts = 0

            # Record state
            df.at[idx, 'signal'] = 1 if in_long else (-1 if in_short else 0)
            df.at[idx, 'position'] = position_size if in_long else (-position_size if in_short else 0)
            df.at[idx, 'avg_price'] = avg_price

        return df
