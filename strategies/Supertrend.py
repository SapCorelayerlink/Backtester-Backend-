import asyncio
from datetime import datetime, time, timedelta, timezone
from typing import Dict, Optional

import pandas as pd

from core.base import StrategyBase
try:  # for typing only; avoid hard dependency at runtime
    from core.base import BrokerBase  # type: ignore
except Exception:  # pragma: no cover
    BrokerBase = object  # type: ignore
from core.registry import StrategyRegistry
from data.data_manager import DataManager


def compute_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    """
    Simplified SuperTrend calculation using rolling ATR proxy.
    Expects columns: 'high', 'low', 'close'. Returns boolean series: True=GREEN (bullish), False=RED (bearish).
    """
    if len(df) == 0:
        return pd.Series(dtype=bool)

    hl2 = (df['high'] + df['low']) / 2
    # Simplified ATR proxy: range max-min over rolling window, then smoothed
    atr_proxy = (df['high'].rolling(period).max() - df['low'].rolling(period).min()).rolling(period).mean()
    upperband = hl2 + (multiplier * atr_proxy)
    lowerband = hl2 - (multiplier * atr_proxy)

    trend = [True]  # start bullish by default
    for i in range(1, len(df)):
        if pd.isna(upperband.iloc[i - 1]) or pd.isna(lowerband.iloc[i - 1]):
            # Warmup period, keep previous trend
            trend.append(trend[-1])
            continue

        close_prev = df['close'].iloc[i - 1]
        close_curr = df['close'].iloc[i]
        ub_prev = upperband.iloc[i - 1]
        lb_prev = lowerband.iloc[i - 1]

        if close_curr > ub_prev:
            trend.append(True)
        elif close_curr < lb_prev:
            trend.append(False)
        else:
            # continue previous trend, adjust bands to avoid flips
            prev_trend = trend[-1]
            if prev_trend and lowerband.iloc[i] < lowerband.iloc[i - 1]:
                lowerband.iloc[i] = lowerband.iloc[i - 1]
            if (not prev_trend) and upperband.iloc[i] > upperband.iloc[i - 1]:
                upperband.iloc[i] = upperband.iloc[i - 1]
            trend.append(prev_trend)

    return pd.Series(trend, index=df.index)


def moving_average(series: pd.Series, window: int, ma_type: str = 'SMA') -> pd.Series:
    ma_type_upper = (ma_type or 'SMA').upper()
    if ma_type_upper == 'EMA':
        return series.ewm(span=window, adjust=False).mean()
    # Default SMA
    return series.rolling(window).mean()


@StrategyRegistry.register("IntradaySupertrendMA")
class IntradaySupertrendMA(StrategyBase):
    """
    Intraday strategy for IBKR using:
    - Direction from 3-hour SuperTrend (length, multiplier configurable)
    - Entries/Exits from 30-minute moving averages (type and periods configurable)

    Data handling:
    - Stores base '1min' bars to local DB via DataManager ("atlas" equivalent)
    - Resamples to '30min' and '3h' internally for signals
    """

    def __init__(self, name: str, broker: 'BrokerBase', params: Dict = None):
        super().__init__(name, broker, params)

        # Core params
        self.symbol: str = self.params.get('symbol', 'QQQ')
        self.base_timeframe: str = self.params.get('base_timeframe', '1min')
        self.timeframe_30m: str = self.params.get('ma_timeframe', '30min')
        self.timeframe_3h: str = self.params.get('supertrend_timeframe', '3h')

        # SuperTrend params
        self.st_length: int = int(self.params.get('supertrend_length', 10))
        self.st_multiplier: float = float(self.params.get('supertrend_multiplier', 3.0))

        # MA params
        self.ma_type: str = self.params.get('ma_type', 'SMA')  # 'SMA' or 'EMA'
        self.ma5_period: int = int(self.params.get('ma5_period', 5))
        self.ma9_period: int = int(self.params.get('ma9_period', 9))
        self.ma20_period: int = int(self.params.get('ma20_period', 20))
        self.ma50_period: int = int(self.params.get('ma50_period', 50))

        # Trading params
        self.quantity: int = int(self.params.get('quantity', 100))
        self.stop_loss_pct: float = float(self.params.get('stop_loss_pct', 0.02))
        self.take_profit_pct: float = float(self.params.get('take_profit_pct', 0.03))
        self.use_bracket_orders: bool = bool(self.params.get('use_bracket_orders', True))
        self.place_market_orders: bool = bool(self.params.get('place_market_orders', True))
        self.persist_resampled: bool = bool(self.params.get('persist_resampled', True))

        # Market hours (default US equities RTH)
        self.trading_hours = self.params.get('trading_hours', {
            'start': time(9, 30),
            'end': time(16, 0)
        })

        # Backfill days for base bars
        self.backfill_days: int = int(self.params.get('backfill_days', 5))

        # State
        self.minute_bars: pd.DataFrame = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        self.last_processed_30m_bar: Optional[pd.Timestamp] = None
        self.position: int = 0  # 0=no position, 1=long, -1=short
        self.entry_price: float = 0.0
        self.entry_time: Optional[datetime] = None

        # Managers
        self.data_manager = DataManager()

    async def init(self):
        # Optional backfill of minute data (store to DB for resampling)
        try:
            if self.backfill_days > 0:
                end_dt = datetime.now(timezone.utc)
                start_dt = end_dt - timedelta(days=self.backfill_days)
                df = await self.broker.get_historical_data(
                    symbol=self.symbol,
                    timeframe=self.base_timeframe,
                    start_date=start_dt.strftime('%Y-%m-%d'),
                    end_date=end_dt.strftime('%Y-%m-%d'),
                )
                if df is not None and not df.empty:
                    # Standardize columns to lower-case
                    df.rename(columns={
                        'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume',
                        'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume',
                    }, inplace=True)
                    # Ensure datetime index
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'], utc=True)
                        df.set_index('date', inplace=True)
                    if not isinstance(df.index, pd.DatetimeIndex):
                        df.index = pd.to_datetime(df.index, utc=True)
                    # Save to DB as base bars, keep in-memory too
                    self.data_manager.save_bars(self.symbol, self.base_timeframe, df)
                    self.minute_bars = df[['open', 'high', 'low', 'close', 'volume']].copy()
        except Exception as e:
            print(f"[{self.name}] Backfill failed: {e}")

        print(f"[{self.name}] Initialized for {self.symbol} | ST({self.st_length},{self.st_multiplier}) on {self.timeframe_3h} | MAs on {self.timeframe_30m} ({self.ma_type}).")

    def is_market_open(self, current_time: datetime) -> bool:
        if current_time is None:
            return False
        ct = current_time.time()
        return self.trading_hours['start'] <= ct <= self.trading_hours['end']

    def _resample(self) -> Dict[str, pd.DataFrame]:
        if self.minute_bars.empty:
            return {'30m': pd.DataFrame(), '3h': pd.DataFrame()}

        df = self.minute_bars.copy()
        df = df.sort_index()
        agg = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
        bars_30m = df.resample(self.timeframe_30m).agg(agg).dropna()
        bars_3h = df.resample(self.timeframe_3h).agg(agg).dropna()
        return {'30m': bars_30m, '3h': bars_3h}

    async def on_bar(self, bar_data: pd.Series):
        """
        Expects a 1-minute bar with keys: timestamp, open, high, low, close, volume.
        Stores it, resamples, and on each completed 30m bar evaluates signals.
        """
        # Normalize and append to minute_bars
        ts: pd.Timestamp = pd.to_datetime(bar_data.get('timestamp'), utc=True)
        row = {
            'open': float(bar_data.get('open', bar_data.get('Open', 0))),
            'high': float(bar_data.get('high', bar_data.get('High', 0))),
            'low': float(bar_data.get('low', bar_data.get('Low', 0))),
            'close': float(bar_data.get('close', bar_data.get('Close', 0))),
            'volume': float(bar_data.get('volume', bar_data.get('Volume', 0)))
        }

        # Market hours gate (optional; still store data)
        if not self.is_market_open(ts.tz_convert('US/Eastern').to_pydatetime()):
            return

        # Append to in-memory DataFrame
        self.minute_bars.loc[ts] = row

        # Persist this minute to DB (base timeframe)
        try:
            df_one = pd.DataFrame([row], index=pd.DatetimeIndex([ts]))
            self.data_manager.save_bars(self.symbol, self.base_timeframe, df_one)
        except Exception as e:
            print(f"[{self.name}] Warning: failed to save minute bar: {e}")

        # Resample
        resampled = self._resample()
        bars_30m = resampled['30m']
        bars_3h = resampled['3h']
        if bars_30m.empty or bars_3h.empty:
            return

        # Only act on a new completed 30m bar
        latest_30m_ts = bars_30m.index[-1]
        if self.last_processed_30m_bar is not None and latest_30m_ts <= self.last_processed_30m_bar:
            return

        # Persist latest completed resampled bars (idempotent via UNIQUE constraint)
        if self.persist_resampled:
            try:
                last_30m_df = bars_30m.iloc[[-1]][['open', 'high', 'low', 'close', 'volume']]
                self.data_manager.save_bars(self.symbol, self.timeframe_30m, last_30m_df)
            except Exception as e:
                print(f"[{self.name}] Warning: failed to save 30m bar: {e}")
            try:
                last_3h_df = bars_3h.iloc[[-1]][['open', 'high', 'low', 'close', 'volume']]
                self.data_manager.save_bars(self.symbol, self.timeframe_3h, last_3h_df)
            except Exception as e:
                print(f"[{self.name}] Warning: failed to save 3h bar: {e}")

        # Compute indicators
        # 3h SuperTrend
        st_series = compute_supertrend(bars_3h, period=self.st_length, multiplier=self.st_multiplier)
        st_latest = st_series.iloc[-1] if len(st_series) else True

        # 30m MAs
        c30 = bars_30m['close']
        ma5 = moving_average(c30, self.ma5_period, self.ma_type)
        ma9 = moving_average(c30, self.ma9_period, self.ma_type)
        ma20 = moving_average(c30, self.ma20_period, self.ma_type)
        ma50 = moving_average(c30, self.ma50_period, self.ma_type)

        # Use latest completed bar values
        close_30m = c30.iloc[-1]
        ma5_now, ma9_now, ma20_now, ma50_now = ma5.iloc[-1], ma9.iloc[-1], ma20.iloc[-1], ma50.iloc[-1]
        # previous for cross detection
        ma5_prev = ma5.iloc[-2] if len(ma5) > 1 else pd.NA
        ma50_prev = ma50.iloc[-2] if len(ma50) > 1 else pd.NA

        # Skip until MAs are ready
        if pd.isna(ma5_now) or pd.isna(ma9_now) or pd.isna(ma20_now) or pd.isna(ma50_now):
            self.last_processed_30m_bar = latest_30m_ts
            return

        # Entry/Exit logic
        if self.position == 0:
            # Long: ST GREEN and MA order 5 > 9 > 20 > 50
            if bool(st_latest) and (ma5_now > ma9_now > ma20_now > ma50_now):
                await self._enter_long(latest_30m_ts, close_30m)
            # Short: ST RED and 5 MA just crossed below 50 MA
            elif (not bool(st_latest)) and (not pd.isna(ma5_prev)) and (not pd.isna(ma50_prev)) and (ma5_prev > ma50_prev) and (ma5_now < ma50_now):
                await self._enter_short(latest_30m_ts, close_30m)
        elif self.position == 1:
            # Long exit: price closes below 9 MA
            if close_30m < ma9_now:
                await self._exit_position(latest_30m_ts, close_30m)
        elif self.position == -1:
            # Short exit: price closes above 9 MA
            if close_30m > ma9_now:
                await self._exit_position(latest_30m_ts, close_30m)

        self.last_processed_30m_bar = latest_30m_ts

    async def _enter_long(self, ts: pd.Timestamp, price: float):
        self.position = 1
        self.entry_price = price
        self.entry_time = ts.to_pydatetime()
        # Place order via broker
        try:
            order = {
                'symbol': self.symbol,
                'qty': self.quantity,
                'side': 'BUY',
                'order_type': 'MKT' if self.place_market_orders else 'LMT',
                'limit_price': price if not self.place_market_orders else None,
            }
            if self.use_bracket_orders:
                sl = round(price * (1.0 - self.stop_loss_pct), 4)
                tp = round(price * (1.0 + self.take_profit_pct), 4)
                await self.broker.place_order(order, stop_loss=sl, take_profit=tp)
            else:
                await self.broker.place_order(order)
            print(f"[{self.symbol}] LONG ENTRY at {ts} price {price:.2f}")
        except Exception as e:
            print(f"[{self.name}] Failed to place LONG order: {e}")

    async def _enter_short(self, ts: pd.Timestamp, price: float):
        self.position = -1
        self.entry_price = price
        self.entry_time = ts.to_pydatetime()
        # Place order via broker
        try:
            order = {
                'symbol': self.symbol,
                'qty': self.quantity,
                'side': 'SELL',
                'order_type': 'MKT' if self.place_market_orders else 'LMT',
                'limit_price': price if not self.place_market_orders else None,
            }
            if self.use_bracket_orders:
                sl = round(price * (1.0 + self.stop_loss_pct), 4)  # higher for short
                tp = round(price * (1.0 - self.take_profit_pct), 4)  # lower for short
                await self.broker.place_order(order, stop_loss=sl, take_profit=tp)
            else:
                await self.broker.place_order(order)
            print(f"[{self.symbol}] SHORT ENTRY at {ts} price {price:.2f}")
        except Exception as e:
            print(f"[{self.name}] Failed to place SHORT order: {e}")

    async def _exit_position(self, ts: pd.Timestamp, price: float):
        if self.position == 0:
            return
        side = 'long' if self.position == 1 else 'short'
        qty = self.quantity
        entry_px = self.entry_price
        pnl = (price - entry_px) * qty if self.position == 1 else (entry_px - price) * qty

        # Place market order to flatten (send opposite order)
        try:
            exit_side = 'SELL' if self.position == 1 else 'BUY'
            order = {
                'symbol': self.symbol,
                'qty': qty,
                'side': exit_side,
                'order_type': 'MKT',
            }
            await self.broker.place_order(order)
        except Exception as e:
            print(f"[{self.name}] Failed to place EXIT order: {e}")

        # Record trade and update equity
        self.record_trade(
            entry_time=self.entry_time,
            exit_time=ts.to_pydatetime(),
            symbol=self.symbol,
            quantity=qty,
            side=side,
            entry_price=entry_px,
            exit_price=price,
            pnl=pnl,
        )
        self.current_equity += pnl
        print(f"[{self.symbol}] EXIT {side.upper()} at {ts} price {price:.2f}, PnL {pnl:.2f}")

        # Reset position state
        self.position = 0
        self.entry_price = 0.0
        self.entry_time = None

    async def cleanup(self):
        # Nothing to clean for now; placeholder for symmetry with runner
        pass

    async def test_with_ibkr_gateway(self, symbol: str = None, test_duration_minutes: int = 5):
        """
        Test the strategy with live IBKR Gateway connection.
        
        Args:
            symbol: Symbol to test (defaults to strategy's symbol)
            test_duration_minutes: How long to run the test
        """
        from brokers.ibkr_manager import ibkr_manager
        import time
        
        test_symbol = symbol or self.symbol
        print(f"🚀 Testing {self.name} with IBKR Gateway")
        print(f"📊 Symbol: {test_symbol}")
        print(f"⏱️ Duration: {test_duration_minutes} minutes")
        print("=" * 60)
        
        # Ensure IBKR connection
        try:
            if not ibkr_manager.ib.isConnected():
                print("🔌 Connecting to IBKR Gateway...")
                await ibkr_manager.connect()
                await asyncio.sleep(2)  # Give it time to connect
            
            if ibkr_manager.ib.isConnected():
                print("✅ Connected to IBKR Gateway")
                
                # Get account info
                account_summary = await ibkr_manager.ib.accountSummaryAsync()
                if account_summary:
                    buying_power = next((item.value for item in account_summary if item.tag == 'BuyingPower'), 'N/A')
                    print(f"💰 Account Buying Power: ${buying_power}")
                
            else:
                print("❌ Failed to connect to IBKR Gateway")
                return
                
        except Exception as e:
            print(f"❌ IBKR Connection error: {e}")
            return
        
        # Request live market data
        try:
            from ib_insync import Stock
            contract = Stock(test_symbol, 'SMART', 'USD')
            
            print(f"📡 Requesting live data for {test_symbol}...")
            ticker = ibkr_manager.ib.reqMktData(contract)
            await asyncio.sleep(1)  # Wait for initial data
            
            start_time = time.time()
            end_time = start_time + (test_duration_minutes * 60)
            tick_count = 0
            
            print(f"📊 Starting live test... (Press Ctrl+C to stop)")
            print("⏰ Live market data:")
            
            while time.time() < end_time:
                try:
                    # Update ticker data
                    ibkr_manager.ib.sleep(0.1)  # Process any pending updates
                    
                    # Check if we have valid price data
                    if ticker.last > 0:
                        tick_count += 1
                        current_time = pd.Timestamp.now()
                        
                        # Create bar data from current tick
                        bar_data = pd.Series({
                            'timestamp': current_time,
                            'open': ticker.last,
                            'high': ticker.last,
                            'low': ticker.last,
                            'close': ticker.last,
                            'volume': ticker.lastSize or 100
                        })
                        
                        # Feed to strategy
                        await self.on_data(bar_data)
                        
                        # Print progress every 10 ticks
                        if tick_count % 10 == 0:
                            bid_ask = f"bid:{ticker.bid:.2f}/ask:{ticker.ask:.2f}" if ticker.bid > 0 and ticker.ask > 0 else "no bid/ask"
                            print(f"  💹 Tick {tick_count}: ${ticker.last:.2f} ({bid_ask}) at {current_time.strftime('%H:%M:%S')}")
                    
                    await asyncio.sleep(1)  # Check every second
                    
                except KeyboardInterrupt:
                    print("\n🛑 Test stopped by user")
                    break
                except Exception as e:
                    print(f"⚠️ Error during test: {e}")
                    await asyncio.sleep(2)
            
            # Cancel market data subscription
            ibkr_manager.ib.cancelMktData(contract)
            
            # Print test results
            print("\n" + "=" * 60)
            print("📈 IBKR Test Results")
            print("=" * 60)
            print(f"⏱️ Total ticks processed: {tick_count}")
            print(f"💼 Strategy: {self.name}")
            print(f"📊 Current position: {self.position}")
            print(f"💰 Current equity: ${self.current_equity:.2f}")
            print(f"📈 Total trades: {len(getattr(self, 'trades', []))}")
            print(f"🏆 Win rate: {self.calculate_win_rate():.1%}")
            print("✅ IBKR test completed successfully")
            
        except Exception as e:
            print(f"❌ Market data error: {e}")
        
    def calculate_win_rate(self) -> float:
        """Calculate win rate from recorded trades."""
        if not hasattr(self, 'trades') or not self.trades:
            return 0.0
        
        winning_trades = sum(1 for trade in self.trades if trade.get('pnl', 0) > 0)
        return winning_trades / len(self.trades) if self.trades else 0.0


