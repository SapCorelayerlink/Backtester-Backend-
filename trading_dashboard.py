#!/usr/bin/env python3
"""
Trading Dashboard
Real-time monitoring of all strategies, trades, PnL, and signals.
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from collections import defaultdict, deque
import logging

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.registry import StrategyRegistry
from brokers.paper_broker import PaperBroker
from data.polygon_data import PolygonDataProvider
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingDashboard:
    """
    Real-time trading dashboard for monitoring all strategies.
    """
    
    def __init__(self, symbols: List[str] = None, starting_cash: float = 100000):
        self.symbols = symbols or ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        self.starting_cash = starting_cash
        self.data_provider = PolygonDataProvider()
        
        # Strategy tracking
        self.strategies = {}
        self.brokers = {}
        self.strategy_signals = defaultdict(list)  # strategy_name -> list of signals
        self.strategy_trades = defaultdict(list)   # strategy_name -> list of trades
        self.strategy_pnl = defaultdict(float)     # strategy_name -> current PnL
        
        # Real-time data
        self.current_prices = {}
        self.price_history = defaultdict(lambda: deque(maxlen=100))
        
        # Dashboard state
        self.is_running = False
        self.start_time = None
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_equity = starting_cash
        
    async def initialize(self):
        """Initialize the dashboard with all strategies."""
        logger.info("Initializing Trading Dashboard...")
        
        try:
            # Get all registered strategies
            available_strategies = StrategyRegistry.list()
            logger.info(f"Found {len(available_strategies)} strategies: {available_strategies}")
            
            # Initialize each strategy
            for strategy_name in available_strategies:
                await self._initialize_strategy(strategy_name)
            
            # Initialize data provider
            await self._initialize_data_provider()
            
            logger.info(f"Dashboard initialized with {len(self.strategies)} strategies")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {e}")
            return False
    
    async def _initialize_strategy(self, strategy_name: str):
        """Initialize a single strategy."""
        try:
            # Create broker for this strategy
            broker = PaperBroker(f"broker_{strategy_name}", {'starting_cash': self.starting_cash})
            await broker.connect()
            self.brokers[strategy_name] = broker
            
            # Get strategy class and create instance
            strategy_class = StrategyRegistry.get(strategy_name)
            strategy = strategy_class(
                name=strategy_name,
                broker=broker,
                params={
                    'symbol': self.symbols[0],  # Default to first symbol
                    'timeframe': '1d',
                    'quantity': 100,
                    'initial_capital': self.starting_cash
                }
            )
            
            # Initialize strategy
            await strategy.init()
            self.strategies[strategy_name] = strategy
            
            logger.info(f"Initialized strategy: {strategy_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize strategy {strategy_name}: {e}")
    
    async def _initialize_data_provider(self):
        """Initialize the data provider for live price streaming."""
        try:
            # Set up price update callback
            await self.data_provider.stream_live_prices(
                symbols=self.symbols,
                on_price_callback=self._handle_price_update
            )
            logger.info("Data provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize data provider: {e}")
    
    async def _handle_price_update(self, tick_data: Dict[str, Any]):
        """Handle incoming price updates."""
        try:
            symbol = tick_data.get('symbol')
            price = tick_data.get('price', 0)
            timestamp = tick_data.get('timestamp', datetime.now())
            
            if not symbol or price <= 0:
                return
            
            # Update current prices
            self.current_prices[symbol] = price
            self.price_history[symbol].append({
                'timestamp': timestamp,
                'price': price
            })
            
            # Process each strategy
            for strategy_name, strategy in self.strategies.items():
                await self._process_strategy_tick(strategy_name, strategy, tick_data)
            
            # Update performance metrics
            await self._update_performance_metrics()
            
        except Exception as e:
            logger.error(f"Error handling price update: {e}")
    
    async def _process_strategy_tick(self, strategy_name: str, strategy, tick_data: Dict[str, Any]):
        """Process a tick for a specific strategy."""
        try:
            # Create bar data for strategy
            bar_data = self._create_bar_data(tick_data)
            
            # Call strategy on_bar method
            await strategy.on_bar(bar_data)
            
            # Check for new trades
            await self._check_for_new_trades(strategy_name, strategy)
            
            # Check for new signals
            await self._check_for_new_signals(strategy_name, strategy, bar_data)
            
        except Exception as e:
            logger.error(f"Error processing tick for {strategy_name}: {e}")
    
    def _create_bar_data(self, tick_data: Dict[str, Any]) -> pd.Series:
        """Create bar data from tick data."""
        symbol = tick_data.get('symbol')
        price = tick_data.get('price', 0)
        timestamp = tick_data.get('timestamp', datetime.now())
        
        # Simple bar creation (in real implementation, you'd aggregate ticks)
        return pd.Series({
            'symbol': symbol,
            'open': price,
            'high': price,
            'low': price,
            'close': price,
            'volume': 1000,  # Default volume
            'timestamp': timestamp
        })
    
    async def _check_for_new_trades(self, strategy_name: str, strategy):
        """Check for new trades from the strategy."""
        try:
            broker = self.brokers[strategy_name]
            trade_history = await broker.get_trade_history()
            
            # Compare with previous trades
            current_trade_count = len(trade_history)
            previous_trade_count = len(self.strategy_trades[strategy_name])
            
            if current_trade_count > previous_trade_count:
                # New trades found
                new_trades = trade_history[previous_trade_count:]
                for trade in new_trades:
                    self.strategy_trades[strategy_name].append(trade)
                    self.total_trades += 1
                    
                    # Update PnL
                    pnl = trade.get('pnl', 0)
                    self.strategy_pnl[strategy_name] += pnl
                    self.total_pnl += pnl
                    
                    if pnl > 0:
                        self.winning_trades += 1
                    
                    logger.info(f"New trade for {strategy_name}: {trade}")
            
        except Exception as e:
            logger.error(f"Error checking trades for {strategy_name}: {e}")
    
    async def _check_for_new_signals(self, strategy_name: str, strategy, bar_data: pd.Series):
        """Check for new trading signals from the strategy."""
        try:
            # This is a simplified signal detection
            # In a real implementation, you'd track strategy state changes
            
            # For now, we'll create signals based on price movements
            symbol = bar_data.get('symbol')
            price = bar_data.get('close', 0)
            timestamp = bar_data.get('timestamp')
            
            # Simple signal generation (replace with actual strategy signal detection)
            if hasattr(strategy, 'positions') and symbol in strategy.positions:
                position = strategy.positions[symbol]
                
                if position > 0:
                    signal = {
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'action': 'BUY',
                        'price': price,
                        'quantity': position,
                        'strategy': strategy_name
                    }
                elif position < 0:
                    signal = {
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'action': 'SELL',
                        'price': price,
                        'quantity': abs(position),
                        'strategy': strategy_name
                    }
                else:
                    signal = {
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'action': 'HOLD',
                        'price': price,
                        'quantity': 0,
                        'strategy': strategy_name
                    }
                
                self.strategy_signals[strategy_name].append(signal)
                
        except Exception as e:
            logger.error(f"Error checking signals for {strategy_name}: {e}")
    
    async def _update_performance_metrics(self):
        """Update overall performance metrics."""
        try:
            # Calculate total equity
            total_equity = self.starting_cash + self.total_pnl
            
            # Update peak equity and drawdown
            if total_equity > self.peak_equity:
                self.peak_equity = total_equity
            
            current_drawdown = (self.peak_equity - total_equity) / self.peak_equity
            if current_drawdown > self.max_drawdown:
                self.max_drawdown = current_drawdown
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    async def start(self):
        """Start the trading dashboard."""
        if self.is_running:
            logger.warning("Dashboard is already running")
            return
        
        success = await self.initialize()
        if not success:
            logger.error("Failed to initialize dashboard")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        logger.info("Trading Dashboard started")
        logger.info(f"Monitoring {len(self.strategies)} strategies")
        logger.info(f"Symbols: {self.symbols}")
        
        # Start the dashboard loop
        await self._dashboard_loop()
    
    async def _dashboard_loop(self):
        """Main dashboard loop."""
        try:
            while self.is_running:
                # Display dashboard
                self._display_dashboard()
                
                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
        finally:
            await self.stop()
    
    def _display_dashboard(self):
        """Display the trading dashboard."""
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
        
        print("=" * 100)
        print("🚀 TRADING DASHBOARD - REAL-TIME MONITORING")
        print("=" * 100)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Running for: {self._get_runtime()}")
        print()
        
        # Overall Performance
        self._display_overall_performance()
        print()
        
        # Current Prices
        self._display_current_prices()
        print()
        
        # Strategy Performance
        self._display_strategy_performance()
        print()
        
        # Recent Trades
        self._display_recent_trades()
        print()
        
        # Recent Signals
        self._display_recent_signals()
        print()
        
        print("=" * 100)
        print("Press Ctrl+C to stop")
    
    def _display_overall_performance(self):
        """Display overall performance metrics."""
        print("📊 OVERALL PERFORMANCE")
        print("-" * 50)
        
        total_equity = self.starting_cash + self.total_pnl
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        print(f"Starting Capital: ${self.starting_cash:,.2f}")
        print(f"Current Equity:   ${total_equity:,.2f}")
        print(f"Total PnL:        ${self.total_pnl:,.2f}")
        print(f"Return:           {(self.total_pnl / self.starting_cash * 100):.2f}%")
        print(f"Total Trades:     {self.total_trades}")
        print(f"Win Rate:         {win_rate:.1f}%")
        print(f"Max Drawdown:     {self.max_drawdown * 100:.2f}%")
    
    def _display_current_prices(self):
        """Display current prices for all symbols."""
        print("💰 CURRENT PRICES")
        print("-" * 50)
        
        for symbol in self.symbols:
            price = self.current_prices.get(symbol, 0)
            if price > 0:
                print(f"{symbol}: ${price:.2f}")
            else:
                print(f"{symbol}: No data")
    
    def _display_strategy_performance(self):
        """Display performance for each strategy."""
        print("📈 STRATEGY PERFORMANCE")
        print("-" * 50)
        
        for strategy_name in self.strategies.keys():
            pnl = self.strategy_pnl[strategy_name]
            trades = len(self.strategy_trades[strategy_name])
            signals = len(self.strategy_signals[strategy_name])
            
            print(f"{strategy_name:20} | PnL: ${pnl:8,.2f} | Trades: {trades:3} | Signals: {signals:3}")
    
    def _display_recent_trades(self):
        """Display recent trades."""
        print("🔄 RECENT TRADES (Last 10)")
        print("-" * 50)
        
        all_trades = []
        for strategy_name, trades in self.strategy_trades.items():
            for trade in trades:
                trade['strategy'] = strategy_name
                all_trades.append(trade)
        
        # Sort by timestamp (most recent first)
        all_trades.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
        
        for trade in all_trades[:10]:
            timestamp = trade.get('timestamp', 'Unknown')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%H:%M:%S')
            
            symbol = trade.get('symbol', 'Unknown')
            side = trade.get('side', 'Unknown')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            pnl = trade.get('pnl', 0)
            strategy = trade.get('strategy', 'Unknown')
            
            pnl_color = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
            
            print(f"{timestamp} | {strategy:15} | {symbol:5} | {side:4} | {quantity:4} @ ${price:6.2f} | {pnl_color} ${pnl:8,.2f}")
    
    def _display_recent_signals(self):
        """Display recent trading signals."""
        print("📡 RECENT SIGNALS (Last 10)")
        print("-" * 50)
        
        all_signals = []
        for strategy_name, signals in self.strategy_signals.items():
            for signal in signals:
                signal['strategy'] = strategy_name
                all_signals.append(signal)
        
        # Sort by timestamp (most recent first)
        all_signals.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
        
        for signal in all_signals[:10]:
            timestamp = signal.get('timestamp', 'Unknown')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%H:%M:%S')
            
            strategy = signal.get('strategy', 'Unknown')
            symbol = signal.get('symbol', 'Unknown')
            action = signal.get('action', 'Unknown')
            price = signal.get('price', 0)
            quantity = signal.get('quantity', 0)
            
            action_icon = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚪"
            
            print(f"{timestamp} | {strategy:15} | {symbol:5} | {action_icon} {action:4} | {quantity:4} @ ${price:6.2f}")
    
    def _get_runtime(self) -> str:
        """Get the runtime duration."""
        if not self.start_time:
            return "0:00:00"
        
        duration = datetime.now() - self.start_time
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        seconds = int(duration.total_seconds() % 60)
        
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    
    async def stop(self):
        """Stop the trading dashboard."""
        self.is_running = False
        
        # Stop data provider
        if self.data_provider:
            self.data_provider.stop_streaming()
        
        # Disconnect brokers
        for broker in self.brokers.values():
            await broker.disconnect()
        
        logger.info("Trading Dashboard stopped")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data for external use."""
        return {
            'timestamp': datetime.now().isoformat(),
            'runtime': self._get_runtime(),
            'symbols': self.symbols,
            'current_prices': self.current_prices,
            'total_pnl': self.total_pnl,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'max_drawdown': self.max_drawdown,
            'strategies': {
                name: {
                    'pnl': self.strategy_pnl[name],
                    'trades': len(self.strategy_trades[name]),
                    'signals': len(self.strategy_signals[name])
                }
                for name in self.strategies.keys()
            },
            'recent_trades': list(self.strategy_trades.values())[-10:],
            'recent_signals': list(self.strategy_signals.values())[-10:]
        }

async def main():
    """Main function to run the trading dashboard."""
    print("🚀 Starting Trading Dashboard...")
    print("This will monitor all strategies in real-time")
    print("Press Ctrl+C to stop")
    print()
    
    # Create dashboard
    dashboard = TradingDashboard(
        symbols=['AAPL', 'MSFT', 'GOOGL', 'TSLA'],
        starting_cash=100000
    )
    
    try:
        await dashboard.start()
    except KeyboardInterrupt:
        print("\n⚠️ Stopping dashboard...")
    except Exception as e:
        print(f"\n❌ Dashboard error: {e}")
    finally:
        await dashboard.stop()

if __name__ == "__main__":
    asyncio.run(main())
