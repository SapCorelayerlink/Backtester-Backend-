"""
Enhanced Strategy Base Class
Provides improved order execution logic, SELL signals, and timeframe support.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from core.base import StrategyBase
import logging

logger = logging.getLogger(__name__)

class EnhancedStrategyBase(StrategyBase):
    """
    Enhanced strategy base class with improved order execution and position management.
    """
    
    def __init__(self, name: str, broker, params: dict = None):
        super().__init__(name, broker, params)
        
        # Enhanced parameters
        self.timeframe = params.get('timeframe', '1D')  # 1m, 5m, 15m, 30m, 1h, 1D, 1W
        self.max_position_size = params.get('max_position_size', 0.2)  # Max 20% of portfolio per position
        self.stop_loss_pct = params.get('stop_loss_pct', 0.05)  # 5% stop loss
        self.take_profit_pct = params.get('take_profit_pct', 0.15)  # 15% take profit
        self.trailing_stop = params.get('trailing_stop', False)
        self.trailing_stop_pct = params.get('trailing_stop_pct', 0.03)  # 3% trailing stop
        
        # Position management
        self.positions = {}  # symbol -> position info
        self.entry_prices = {}  # symbol -> entry price
        self.stop_losses = {}  # symbol -> stop loss price
        self.take_profits = {}  # symbol -> take profit price
        self.trailing_stops = {}  # symbol -> trailing stop price
        
        # Data storage
        self.price_data = {}  # symbol -> list of price bars
        self.signals = []  # List of generated signals
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        
        logger.info(f"Enhanced strategy {name} initialized with timeframe={self.timeframe}")
    
    async def init(self):
        """Initialize the strategy."""
        logger.info(f"Initializing enhanced strategy {self.name}...")
        
        # Initialize data structures for all symbols
        symbols = self.params.get('symbols', ['AAPL', 'MSFT', 'GOOGL', 'TSLA'])
        for symbol in symbols:
            self.price_data[symbol] = []
            self.positions[symbol] = 0
            self.entry_prices[symbol] = 0.0
            self.stop_losses[symbol] = 0.0
            self.take_profits[symbol] = 0.0
            self.trailing_stops[symbol] = 0.0
        
        logger.info(f"Enhanced strategy {self.name} initialized")
    
    async def on_bar(self, bar_data: pd.Series):
        """
        Enhanced bar processing with position management.
        
        Args:
            bar_data: OHLCV data for the current bar
        """
        try:
            symbol = bar_data.get('symbol')
            if not symbol:
                return
            
            # Extract price data
            close_price = bar_data.get('close', 0)
            high_price = bar_data.get('high', close_price)
            low_price = bar_data.get('low', close_price)
            timestamp = bar_data.get('timestamp')
            
            if close_price <= 0:
                return
            
            # Add to price history
            if symbol not in self.price_data:
                self.price_data[symbol] = []
            
            self.price_data[symbol].append({
                'timestamp': timestamp,
                'open': bar_data.get('open', close_price),
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': bar_data.get('volume', 0)
            })
            
            # Keep only recent data based on timeframe
            max_bars = self._get_max_bars_for_timeframe()
            if len(self.price_data[symbol]) > max_bars:
                self.price_data[symbol] = self.price_data[symbol][-max_bars:]
            
            # Check stop losses and take profits first
            await self._check_exit_conditions(symbol, close_price, high_price, low_price, timestamp)
            
            # Generate trading signals
            await self._generate_signals(symbol, close_price, timestamp)
            
            # Execute signals
            await self._execute_signals(symbol, close_price, timestamp)
            
        except Exception as e:
            logger.error(f"Error in enhanced strategy logic: {e}")
    
    def _get_max_bars_for_timeframe(self) -> int:
        """Get maximum number of bars to keep based on timeframe."""
        timeframe_map = {
            '1m': 1000,
            '5m': 500,
            '15m': 300,
            '30m': 200,
            '1h': 100,
            '1D': 50,
            '1W': 20
        }
        return timeframe_map.get(self.timeframe, 50)
    
    async def _check_exit_conditions(self, symbol: str, close_price: float, high_price: float, low_price: float, timestamp: datetime):
        """Check stop losses, take profits, and trailing stops."""
        current_position = self.positions.get(symbol, 0)
        
        if current_position == 0:
            return
        
        entry_price = self.entry_prices.get(symbol, 0)
        if entry_price == 0:
            return
        
        # Check stop loss
        stop_loss_price = self.stop_losses.get(symbol, 0)
        if stop_loss_price > 0:
            if (current_position > 0 and low_price <= stop_loss_price) or \
               (current_position < 0 and high_price >= stop_loss_price):
                await self._exit_position(symbol, close_price, timestamp, "Stop Loss")
                return
        
        # Check take profit
        take_profit_price = self.take_profits.get(symbol, 0)
        if take_profit_price > 0:
            if (current_position > 0 and high_price >= take_profit_price) or \
               (current_position < 0 and low_price <= take_profit_price):
                await self._exit_position(symbol, close_price, timestamp, "Take Profit")
                return
        
        # Update trailing stop
        if self.trailing_stop and current_position > 0:
            trailing_stop_price = self.trailing_stops.get(symbol, 0)
            new_trailing_stop = close_price * (1 - self.trailing_stop_pct)
            
            if new_trailing_stop > trailing_stop_price:
                self.trailing_stops[symbol] = new_trailing_stop
                self.stop_losses[symbol] = new_trailing_stop
                logger.debug(f"Updated trailing stop for {symbol}: ${new_trailing_stop:.2f}")
            
            # Check if trailing stop is hit
            if low_price <= new_trailing_stop:
                await self._exit_position(symbol, close_price, timestamp, "Trailing Stop")
    
    async def _generate_signals(self, symbol: str, close_price: float, timestamp: datetime):
        """Generate trading signals based on strategy logic. Override in subclasses."""
        # This method should be overridden by specific strategies
        pass
    
    async def _execute_signals(self, symbol: str, close_price: float, timestamp: datetime):
        """Execute pending signals."""
        # This method should be overridden by specific strategies
        pass
    
    async def _place_buy_order(self, symbol: str, price: float, reason: str = "Signal"):
        """Place a buy order with position sizing and risk management."""
        try:
            # Check if we already have a position
            current_position = self.positions.get(symbol, 0)
            if current_position > 0:
                logger.debug(f"Already have long position in {symbol}, skipping buy order")
                return
            
            # Get account info for position sizing
            account_info = await self.broker.get_account_info()
            total_equity = float(account_info['account_summary'][0]['value'])  # NetLiquidation
            available_cash = float(account_info['account_summary'][1]['value'])  # AvailableFunds
            
            # Calculate position size
            max_position_value = total_equity * self.max_position_size
            position_value = min(max_position_value, available_cash * 0.9)  # Use 90% of available cash
            shares = int(position_value / price)
            
            if shares > 0:
                # Calculate stop loss and take profit
                stop_loss_price = price * (1 - self.stop_loss_pct)
                take_profit_price = price * (1 + self.take_profit_pct)
                
                order = {
                    'symbol': symbol,
                    'qty': shares,
                    'side': 'buy',
                    'order_type': 'market',
                    'stop_loss': stop_loss_price,
                    'take_profit': take_profit_price
                }
                
                result = await self.broker.place_order(order)
                logger.info(f"Placed BUY order for {shares} {symbol} shares at ~${price:.2f} ({reason})")
                
                # Update position tracking
                self.positions[symbol] = shares
                self.entry_prices[symbol] = price
                self.stop_losses[symbol] = stop_loss_price
                self.take_profits[symbol] = take_profit_price
                self.trailing_stops[symbol] = stop_loss_price
                
                # Record signal
                self.signals.append({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': 'BUY',
                    'price': price,
                    'quantity': shares,
                    'reason': reason
                })
                
        except Exception as e:
            logger.error(f"Error placing buy order: {e}")
    
    async def _place_sell_order(self, symbol: str, price: float, reason: str = "Signal"):
        """Place a sell order to close position."""
        try:
            current_position = self.positions.get(symbol, 0)
            
            if current_position > 0:
                order = {
                    'symbol': symbol,
                    'qty': current_position,
                    'side': 'sell',
                    'order_type': 'market'
                }
                
                result = await self.broker.place_order(order)
                logger.info(f"Placed SELL order for {current_position} {symbol} shares at ~${price:.2f} ({reason})")
                
                # Clear position tracking
                self.positions[symbol] = 0
                self.entry_prices[symbol] = 0.0
                self.stop_losses[symbol] = 0.0
                self.take_profits[symbol] = 0.0
                self.trailing_stops[symbol] = 0.0
                
                # Record signal
                self.signals.append({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': 'SELL',
                    'price': price,
                    'quantity': current_position,
                    'reason': reason
                })
                
        except Exception as e:
            logger.error(f"Error placing sell order: {e}")
    
    async def _exit_position(self, symbol: str, price: float, timestamp: datetime, reason: str):
        """Exit position due to stop loss, take profit, or other conditions."""
        current_position = self.positions.get(symbol, 0)
        
        if current_position > 0:
            await self._place_sell_order(symbol, price, reason)
    
    def get_strategy_state(self) -> dict:
        """Get current strategy state."""
        return {
            'positions': self.positions.copy(),
            'entry_prices': self.entry_prices.copy(),
            'stop_losses': self.stop_losses.copy(),
            'take_profits': self.take_profits.copy(),
            'trailing_stops': self.trailing_stops.copy(),
            'price_data_lengths': {
                symbol: len(data) for symbol, data in self.price_data.items()
            },
            'total_signals': len(self.signals),
            'parameters': {
                'timeframe': self.timeframe,
                'max_position_size': self.max_position_size,
                'stop_loss_pct': self.stop_loss_pct,
                'take_profit_pct': self.take_profit_pct,
                'trailing_stop': self.trailing_stop
            }
        }
    
    def get_recent_signals(self, count: int = 10) -> List[Dict]:
        """Get recent trading signals."""
        return self.signals[-count:] if self.signals else []
