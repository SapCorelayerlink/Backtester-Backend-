import pandas as pd
import numpy as np
from core.base import StrategyBase
from core.registry import StrategyRegistry

@StrategyRegistry.register("PivotStrategy")
class PivotStrategy(StrategyBase):
    """
    Pivot Point and CPR (Central Pivot Range) Strategy.
    Uses daily pivot points and CPR levels for intraday trading.
    """
    
    def __init__(self, name: str, broker: 'BrokerBase', params: dict = None):
        super().__init__(name, broker, params)
        
        # Strategy parameters
        self.symbol = self.params.get('symbol', 'SPY')
        self.timeframe = self.params.get('timeframe', '15min')
        self.quantity = self.params.get('quantity', 100)
        
        # Pivot parameters
        self.use_cpr = self.params.get('use_cpr', True)
        self.entry_threshold = self.params.get('entry_threshold', 0.1)
        
        # State variables
        self.in_position = False
        self.position_side = None
        self.entry_price = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        
        # Data storage
        self.price_data = []
        self.pivot_data = []

    async def init(self):
        """Initialize the strategy."""
        print(f"Initializing {self.name} Pivot Strategy")
        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {self.timeframe}")
        print(f"Use CPR: {self.use_cpr}")
        print(f"{self.name}: Initialization complete.")

    def calculate_pivot_cpr(self, df):
        """Calculate daily pivot points and CPR using previous day's data."""
        # Resample to daily data and shift by 1 day to get previous day's data
        df_daily = df.resample('1D').agg({
            'high': 'max', 
            'low': 'min', 
            'close': 'last'
        }).shift(1)
        
        # Calculate pivot point (P)
        df_daily['P'] = (df_daily['high'] + df_daily['low'] + df_daily['close']) / 3
        
        # Calculate BC (Bottom Central) and TC (Top Central)
        df_daily['BC'] = (df_daily['high'] + df_daily['low']) / 2
        df_daily['TC'] = 2 * df_daily['P'] - df_daily['BC']
        
        return df_daily[['P', 'BC', 'TC']]

    def attach_pivot_to_intraday(self, df, df_daily_pivots):
        """Map daily pivot/CPR levels to each intraday row by date."""
        df['date'] = df.index.date
        df_daily_pivots.index = df_daily_pivots.index.date
        df = df.join(df_daily_pivots, on='date')
        df.drop(columns=['date'], inplace=True)
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
        
        # Need at least 2 days of data to calculate pivots
        if len(self.price_data) < 48:  # Assuming 15min bars, need 48 for 2 days
            return
        
        # Convert price data to DataFrame
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
            print(f"PivotStrategy: Error processing timestamps: {e}")
            return
        
        # Calculate pivot levels
        pivot_levels = self.calculate_pivot_cpr(df)
        df_with_pivots = self.attach_pivot_to_intraday(df, pivot_levels)
        
        # Get current day's data
        try:
            if current_time is not None:
                current_date = current_time.date()
                df_today = df_with_pivots[df_with_pivots.index.date == current_date]
            else:
                # If current_time is None, use the latest available date
                current_date = df_with_pivots.index.date[-1]
                df_today = df_with_pivots[df_with_pivots.index.date == current_date]
        except Exception as e:
            print(f"PivotStrategy: Error getting current date: {e}")
            return
        
        if df_today.empty:
            return
        
        # Get pivot levels for today
        today_pivots = df_today.iloc[0]
        P = today_pivots.get('P')
        BC = today_pivots.get('BC')
        TC = today_pivots.get('TC')
        
        if pd.isna(P) or pd.isna(BC) or pd.isna(TC):
            return
        
        # Determine bias based on open price versus CPR
        open_price = df_today.iloc[0]['open']
        
        if open_price > TC:
            bias = 'bullish'
        elif open_price < BC:
            bias = 'bearish'
        else:
            bias = 'neutral'
        
        # Trading logic
        if not self.in_position:
            # LONG Entry Conditions
            if bias == 'bullish':
                # Enter LONG when price touches BC or P and closes above it
                entry_levels = [BC, P]
                for level in entry_levels:
                    if low <= level <= current_price:
                        self.entry_price = current_price
                        self.stop_loss = BC if level == P else BC - (TC - BC) * 0.1
                        self.take_profit = TC + (TC - BC)
                        
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
                            print(f"{current_time}: LONG ENTRY for {self.symbol} at {self.entry_price:.2f} (Pivot: {level:.2f})")
                        break
            
            # SHORT Entry Conditions
            elif bias == 'bearish':
                # Enter SHORT when price touches TC or P and closes below it
                entry_levels = [TC, P]
                for level in entry_levels:
                    if high >= level >= current_price:
                        self.entry_price = current_price
                        self.stop_loss = TC if level == P else TC + (TC - BC) * 0.1
                        self.take_profit = BC - (TC - BC)
                        
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
                            print(f"{current_time}: SHORT ENTRY for {self.symbol} at {self.entry_price:.2f} (Pivot: {level:.2f})")
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

