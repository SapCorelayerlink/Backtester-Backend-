#!/usr/bin/env python3
"""
Historical Trading Dashboard
Backtesting all strategies with Polygon.io historical data and showing trades, PnL, and signals.
"""

import asyncio
import sys
import os
import json
import time
import uuid
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
from data.backtest_database import BacktestDatabase
from sqlalchemy import text
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoricalTradingDashboard:
    """
    Historical backtesting dashboard for monitoring all strategies with Polygon.io data.
    """
    
    def __init__(self, symbols: List[str] = None, starting_cash: float = 100000):
        self.symbols = symbols or ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        self.starting_cash = starting_cash
        self.data_provider = PolygonDataProvider()
        self.database = BacktestDatabase()  # Initialize database connection
        
        # Strategy tracking
        self.strategies = {}
        self.brokers = {}
        self.strategy_signals = defaultdict(list)  # strategy_name -> list of signals
        self.strategy_trades = defaultdict(list)   # strategy_name -> list of trades
        self.strategy_pnl = defaultdict(float)     # strategy_name -> current PnL
        self.strategy_equity_curves = defaultdict(list)  # strategy_name -> equity curve
        
        # Historical data
        self.historical_data = {}
        self.current_bar_index = 0
        
        # Dashboard state
        self.is_running = False
        self.start_time = None
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_equity = starting_cash
        
        # Backtest parameters
        self.start_date = "2024-01-01"
        self.end_date = "2024-12-31"
        self.timeframe = "1D"  # Polygon.io format
        
        # Database tracking
        self.backtest_run_ids = {}  # strategy_name -> run_id
        self.trade_id_counter = 0
        
    async def initialize(self):
        """Initialize the dashboard with all strategies and historical data."""
        logger.info("Initializing Historical Trading Dashboard...")
        
        try:
            # Import all strategies to register them
            await self._import_strategies()
            
            # Get all registered strategies
            available_strategies = StrategyRegistry.list()
            logger.info(f"Found {len(available_strategies)} strategies: {available_strategies}")
            
            # Load historical data for all symbols
            await self._load_historical_data()
            
            # Initialize each strategy
            for strategy_name in available_strategies:
                await self._initialize_strategy(strategy_name)
            
            logger.info(f"Dashboard initialized with {len(self.strategies)} strategies")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {e}")
            return False
    
    async def _import_strategies(self):
        """Import all strategy modules to register them."""
        strategy_modules = [
            "strategies.sample_strategy",
            "strategies.macrossover_strategy", 
            "strategies.simple_paper_strategy",
            "strategies.enhanced_simple_strategy",  # Enhanced strategy
            "strategies.timeframe_strategy",        # Timeframe strategy
            "strategies.RSI+VWAP",
            "strategies.Turtle",
            "strategies.SwingFailure",
            "strategies.Bollinger + 5EMA",
            "strategies.Supertrend",
            "strategies.Support Resiatance ",
            "strategies.intraday_supertrend_ma_strategy"
        ]
        
        for module_name in strategy_modules:
            try:
                __import__(module_name)
                logger.info(f"Imported {module_name}")
            except Exception as e:
                logger.warning(f"Failed to import {module_name}: {e}")
    
    async def _load_historical_data(self):
        """Load historical data for all symbols from Polygon.io."""
        logger.info("Loading historical data from Polygon.io...")
        
        for symbol in self.symbols:
            try:
                logger.info(f"Loading data for {symbol}...")
                
                # Convert dates to datetime objects
                start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
                
                # Get historical data from Polygon
                data = await self.data_provider.get_historical_bars(
                    symbol=symbol,
                    from_date=start_dt,
                    to_date=end_dt,
                    interval=self.timeframe
                )
                
                if data is not None and not data.empty:
                    self.historical_data[symbol] = data
                    logger.info(f"Loaded {len(data)} bars for {symbol}")
                else:
                    logger.warning(f"No data received for {symbol}")
                    
            except Exception as e:
                logger.error(f"Failed to load data for {symbol}: {e}")
    
    async def _initialize_strategy(self, strategy_name: str):
        """Initialize a single strategy."""
        try:
            # Create broker for this strategy
            broker = PaperBroker(f"broker_{strategy_name}", {'starting_cash': self.starting_cash})
            await broker.connect()
            self.brokers[strategy_name] = broker
            
            # Get strategy class and create instance
            strategy_class = StrategyRegistry.get(strategy_name)
            
            # Enhanced parameters for strategies
            strategy_params = {
                'symbols': self.symbols,  # All symbols
                'timeframe': self.timeframe,
                'quantity': 100,
                'initial_capital': self.starting_cash,
                'start_date': self.start_date,
                'end_date': self.end_date,
                # Enhanced parameters
                'max_position_size': 0.2,  # Max 20% per position
                'stop_loss_pct': 0.05,     # 5% stop loss
                'take_profit_pct': 0.15,   # 15% take profit
                'trailing_stop': True,     # Enable trailing stops
                'trailing_stop_pct': 0.03  # 3% trailing stop
            }
            
            strategy = strategy_class(
                name=strategy_name,
                broker=broker,
                params=strategy_params
            )
            
            # Initialize strategy
            await strategy.init()
            self.strategies[strategy_name] = strategy
            
            # Create backtest run record in database
            await self._create_backtest_run(strategy_name, strategy_params)
            
            logger.info(f"Initialized strategy: {strategy_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize strategy {strategy_name}: {e}")
    
    async def _create_backtest_run(self, strategy_name: str, parameters: Dict[str, Any]):
        """Create a backtest run record in the database."""
        try:
            run_id = f"{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
            self.backtest_run_ids[strategy_name] = run_id
            
            # Create initial backtest run record
            run_data = {
                'run_id': run_id,
                'strategy_name': strategy_name,
                'symbol': ', '.join(self.symbols),  # Multiple symbols
                'timeframe': self.timeframe,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'initial_capital': self.starting_cash,
                'final_equity': self.starting_cash,  # Will be updated
                'total_return': 0.0,  # Will be updated
                'total_return_pct': 0.0,  # Will be updated
                'total_trades': 0,  # Will be updated
                'winning_trades': 0,  # Will be updated
                'losing_trades': 0,  # Will be updated
                'win_rate': 0.0,  # Will be updated
                'total_pnl': 0.0,  # Will be updated
                'average_trade_pnl': 0.0,  # Will be updated
                'sharpe_ratio': 0.0,  # Will be updated
                'max_drawdown': 0.0,  # Will be updated
                'parameters': json.dumps(parameters),
                'status': 'running'
            }
            
            # Save to database
            self.database.save_backtest_result(run_data)
            logger.info(f"Created backtest run {run_id} for {strategy_name}")
            
        except Exception as e:
            logger.error(f"Failed to create backtest run for {strategy_name}: {e}")
    
    async def run_backtest(self):
        """Run the complete backtest for all strategies."""
        logger.info("Starting backtest...")
        
        # Get the common date range for all symbols
        common_dates = self._get_common_dates()
        if not common_dates:
            logger.error("No common dates found across symbols")
            return
        
        logger.info(f"Running backtest on {len(common_dates)} bars")
        
        # Process each bar
        for i, date in enumerate(common_dates):
            await self._process_bar(date, i)
            
            # Update dashboard every 10 bars
            if i % 10 == 0:
                self._display_progress(i, len(common_dates))
        
        # Final dashboard display and database updates
        await self._finalize_backtest_results()
        self._display_final_results()
    
    def _get_common_dates(self) -> List[datetime]:
        """Get common dates across all symbols."""
        if not self.historical_data:
            return []
        
        # Get the first symbol's dates as base
        first_symbol = list(self.historical_data.keys())[0]
        base_dates = self.historical_data[first_symbol].index.tolist()
        
        # Find common dates across all symbols
        common_dates = []
        for date in base_dates:
            is_common = True
            for symbol in self.symbols:
                if symbol in self.historical_data:
                    if date not in self.historical_data[symbol].index:
                        is_common = False
                        break
                else:
                    is_common = False
                    break
            
            if is_common:
                common_dates.append(date)
        
        return common_dates
    
    async def _process_bar(self, date: datetime, bar_index: int):
        """Process a single bar for all strategies."""
        try:
            # Create bar data for each symbol
            bar_data = {}
            for symbol in self.symbols:
                if symbol in self.historical_data and date in self.historical_data[symbol].index:
                    symbol_data = self.historical_data[symbol].loc[date]
                    bar_data[symbol] = pd.Series({
                        'symbol': symbol,
                        'open': symbol_data['open'],
                        'high': symbol_data['high'],
                        'low': symbol_data['low'],
                        'close': symbol_data['close'],
                        'volume': symbol_data['volume'],
                        'timestamp': date
                    })
            
            # Process each strategy
            for strategy_name, strategy in self.strategies.items():
                await self._process_strategy_bar(strategy_name, strategy, bar_data, date)
            
            # Update performance metrics
            await self._update_performance_metrics()
            
        except Exception as e:
            logger.error(f"Error processing bar {date}: {e}")
    
    async def _process_strategy_bar(self, strategy_name: str, strategy, bar_data: Dict[str, pd.Series], date: datetime):
        """Process a bar for a specific strategy."""
        try:
            # Process each symbol's bar data
            for symbol, symbol_bar in bar_data.items():
                # Call strategy on_bar method
                await strategy.on_bar(symbol_bar)
                
                # Check for new trades
                await self._check_for_new_trades(strategy_name, strategy, date)
                
                # Check for new signals
                await self._check_for_new_signals(strategy_name, strategy, symbol_bar, date)
            
            # Update equity curve
            await self._update_equity_curve(strategy_name, strategy, date)
            
        except Exception as e:
            logger.error(f"Error processing bar for {strategy_name}: {e}")
    
    async def _check_for_new_trades(self, strategy_name: str, strategy, date: datetime):
        """Check for new trades from the strategy and save them to database."""
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
                    # Enhance trade data with additional details
                    enhanced_trade = await self._enhance_trade_data(trade, strategy_name, date)
                    
                    # Add to local tracking
                    self.strategy_trades[strategy_name].append(enhanced_trade)
                    self.total_trades += 1
                    
                    # Update PnL
                    pnl = enhanced_trade.get('pnl', 0)
                    self.strategy_pnl[strategy_name] += pnl
                    self.total_pnl += pnl
                    
                    if pnl > 0:
                        self.winning_trades += 1
                    
                    # Save trade to database
                    await self._save_trade_to_database(enhanced_trade, strategy_name)
                    
                    logger.info(f"New trade for {strategy_name}: {enhanced_trade}")
            
        except Exception as e:
            logger.error(f"Error checking trades for {strategy_name}: {e}")
    
    async def _enhance_trade_data(self, trade: Dict[str, Any], strategy_name: str, date: datetime) -> Dict[str, Any]:
        """Enhance trade data with additional details for database storage."""
        try:
            # Generate unique trade ID
            self.trade_id_counter += 1
            trade_id = f"TRADE_{strategy_name}_{self.trade_id_counter:06d}"
            
            # Calculate additional metrics
            entry_price = trade.get('price', 0)
            exit_price = trade.get('price', 0)  # For now, same as entry (will be updated when position closes)
            quantity = trade.get('quantity', 0)
            side = trade.get('side', 'unknown')
            
            # Calculate PnL (simplified - will be updated when position closes)
            pnl = 0.0
            if side == 'sell' and quantity > 0:
                # This is a sell order, calculate PnL based on position
                pnl = trade.get('pnl', 0)
            
            # Calculate return percentage
            return_pct = 0.0
            if entry_price > 0:
                return_pct = ((exit_price - entry_price) / entry_price) * 100
            
            # Calculate trade duration (will be updated when position closes)
            trade_duration_hours = 0.0
            
            enhanced_trade = {
                'trade_id': trade_id,
                'order_id': trade.get('order_id', ''),
                'symbol': trade.get('symbol', ''),
                'side': side,
                'quantity': quantity,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'entry_time': date.isoformat(),
                'exit_time': date.isoformat(),  # Will be updated when position closes
                'pnl': pnl,
                'return_pct': return_pct,
                'trade_duration_hours': trade_duration_hours,
                'commission': trade.get('commission', 0.0),
                'timestamp': trade.get('timestamp', date.isoformat()),
                'strategy_name': strategy_name,
                'status': 'open' if side == 'buy' else 'closed'
            }
            
            return enhanced_trade
            
        except Exception as e:
            logger.error(f"Error enhancing trade data: {e}")
            return trade
    
    async def _save_trade_to_database(self, trade: Dict[str, Any], strategy_name: str):
        """Save a trade to the database."""
        try:
            run_id = self.backtest_run_ids.get(strategy_name)
            if not run_id:
                logger.error(f"No run_id found for strategy {strategy_name}")
                return
            
            # Prepare trade data for database
            trade_data = {
                'run_id': run_id,
                'entry_time': trade['entry_time'],
                'exit_time': trade['exit_time'],
                'symbol': trade['symbol'],
                'side': trade['side'],
                'quantity': trade['quantity'],
                'entry_price': trade['entry_price'],
                'exit_price': trade['exit_price'],
                'pnl': trade['pnl'],
                'return_pct': trade['return_pct'],
                'trade_duration_hours': trade['trade_duration_hours']
            }
            
            # Save trade directly to database using SQL
            if hasattr(self.database, 'engine') and self.database.engine:
                # PostgreSQL/TimescaleDB
                with self.database.engine.begin() as conn:
                    conn.execute(text('''
                        INSERT INTO trades (
                            run_id, entry_time, exit_time, symbol, side, quantity,
                            entry_price, exit_price, pnl, return_pct, trade_duration_hours
                        ) VALUES (:run_id, :entry_time, :exit_time, :symbol, :side, :quantity,
                                :entry_price, :exit_price, :pnl, :return_pct, :trade_duration_hours)
                    '''), trade_data)
            else:
                # SQLite
                import sqlite3
                with sqlite3.connect(self.database.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO trades (
                            run_id, entry_time, exit_time, symbol, side, quantity,
                            entry_price, exit_price, pnl, return_pct, trade_duration_hours
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        trade_data['run_id'],
                        trade_data['entry_time'],
                        trade_data['exit_time'],
                        trade_data['symbol'],
                        trade_data['side'],
                        trade_data['quantity'],
                        trade_data['entry_price'],
                        trade_data['exit_price'],
                        trade_data['pnl'],
                        trade_data['return_pct'],
                        trade_data['trade_duration_hours']
                    ))
                    conn.commit()
            
            logger.info(f"Trade saved to database: {trade['symbol']} {trade['side']} {trade['quantity']} @ ${trade['entry_price']:.2f}")
            
        except Exception as e:
            logger.error(f"Error saving trade to database: {e}")
    
    async def _check_for_new_signals(self, strategy_name: str, strategy, bar_data: pd.Series, date: datetime):
        """Check for new trading signals from the strategy."""
        try:
            symbol = bar_data.get('symbol')
            price = bar_data.get('close', 0)
            
            # Enhanced signal detection for strategies with signal tracking
            if hasattr(strategy, 'signals') and strategy.signals:
                # Get the most recent signal for this symbol
                recent_signals = [s for s in strategy.signals if s.get('symbol') == symbol]
                if recent_signals:
                    latest_signal = recent_signals[-1]
                    
                    # Check if this is a new signal (not already recorded)
                    existing_signals = [s for s in self.strategy_signals[strategy_name] 
                                      if s.get('symbol') == symbol and s.get('timestamp') == latest_signal.get('timestamp')]
                    
                    if not existing_signals:
                        signal = {
                            'timestamp': date,
                            'symbol': symbol,
                            'action': latest_signal.get('action', 'HOLD'),
                            'price': price,
                            'quantity': latest_signal.get('quantity', 0),
                            'strategy': strategy_name,
                            'reason': latest_signal.get('reason', 'Signal')
                        }
                        self.strategy_signals[strategy_name].append(signal)
            
            # Fallback to position-based signal detection
            elif hasattr(strategy, 'positions') and symbol in strategy.positions:
                position = strategy.positions[symbol]
                
                if position > 0:
                    signal = {
                        'timestamp': date,
                        'symbol': symbol,
                        'action': 'BUY',
                        'price': price,
                        'quantity': position,
                        'strategy': strategy_name,
                        'reason': 'Position'
                    }
                elif position < 0:
                    signal = {
                        'timestamp': date,
                        'symbol': symbol,
                        'action': 'SELL',
                        'price': price,
                        'quantity': abs(position),
                        'strategy': strategy_name,
                        'reason': 'Position'
                    }
                else:
                    signal = {
                        'timestamp': date,
                        'symbol': symbol,
                        'action': 'HOLD',
                        'price': price,
                        'quantity': 0,
                        'strategy': strategy_name,
                        'reason': 'No Position'
                    }
                
                self.strategy_signals[strategy_name].append(signal)
                
        except Exception as e:
            logger.error(f"Error checking signals for {strategy_name}: {e}")
    
    async def _update_equity_curve(self, strategy_name: str, strategy, date: datetime):
        """Update equity curve for a strategy and save to database."""
        try:
            broker = self.brokers[strategy_name]
            account_info = await broker.get_account_info()
            
            if 'portfolio' in account_info:
                total_equity = account_info['portfolio'].get('total_equity', self.starting_cash)
                equity_data = {
                    'date': date,
                    'equity': total_equity
                }
                self.strategy_equity_curves[strategy_name].append(equity_data)
                
                # Save equity curve to database
                await self._save_equity_to_database(strategy_name, date, total_equity)
                
        except Exception as e:
            logger.error(f"Error updating equity curve for {strategy_name}: {e}")
    
    async def _save_equity_to_database(self, strategy_name: str, date: datetime, equity: float):
        """Save equity curve data to database."""
        try:
            run_id = self.backtest_run_ids.get(strategy_name)
            if not run_id:
                return
            
            # Save equity curve directly to database
            if hasattr(self.database, 'engine') and self.database.engine:
                # PostgreSQL/TimescaleDB
                with self.database.engine.begin() as conn:
                    conn.execute(text('''
                        INSERT INTO equity_curves (run_id, timestamp, equity)
                        VALUES (:run_id, :timestamp, :equity)
                    '''), {
                        'run_id': run_id,
                        'timestamp': date.isoformat(),
                        'equity': equity
                    })
            else:
                # SQLite
                import sqlite3
                with sqlite3.connect(self.database.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO equity_curves (run_id, timestamp, equity)
                        VALUES (?, ?, ?)
                    ''', (run_id, date.isoformat(), equity))
                    conn.commit()
            
            logger.debug(f"Equity data saved for {strategy_name}: {date} - ${equity:,.2f}")
            
        except Exception as e:
            logger.error(f"Error saving equity to database: {e}")
    
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
    
    async def _finalize_backtest_results(self):
        """Finalize backtest results and update database with final metrics."""
        try:
            for strategy_name in self.strategies.keys():
                await self._update_final_backtest_results(strategy_name)
                
        except Exception as e:
            logger.error(f"Error finalizing backtest results: {e}")
    
    async def _update_final_backtest_results(self, strategy_name: str):
        """Update final backtest results for a strategy in the database."""
        try:
            run_id = self.backtest_run_ids.get(strategy_name)
            if not run_id:
                return
            
            # Calculate final metrics
            final_equity = self.starting_cash + self.strategy_pnl[strategy_name]
            total_return = final_equity - self.starting_cash
            total_return_pct = (total_return / self.starting_cash * 100) if self.starting_cash > 0 else 0
            
            trades = self.strategy_trades[strategy_name]
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            total_pnl = sum(t.get('pnl', 0) for t in trades)
            average_trade_pnl = total_pnl / total_trades if total_trades > 0 else 0
            
            # Calculate Sharpe ratio and max drawdown (simplified)
            sharpe_ratio = 0.0
            max_drawdown = self.max_drawdown * 100  # Convert to percentage
            
            # Update backtest run record
            final_results = {
                'run_id': run_id,
                'strategy_name': strategy_name,
                'symbol': ', '.join(self.symbols),
                'timeframe': self.timeframe,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'initial_capital': self.starting_cash,
                'final_equity': final_equity,
                'total_return': total_return,
                'total_return_pct': total_return_pct,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'average_trade_pnl': average_trade_pnl,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'status': 'completed'
            }
            
            # Save final results to database
            self.database.save_backtest_result(final_results)
            
            logger.info(f"Finalized backtest results for {strategy_name}: {total_return_pct:.2f}% return, {total_trades} trades")
            
        except Exception as e:
            logger.error(f"Error updating final backtest results for {strategy_name}: {e}")
    
    def _display_progress(self, current: int, total: int):
        """Display backtest progress."""
        progress = (current / total) * 100
        print(f"\r🔄 Backtest Progress: {progress:.1f}% ({current}/{total})", end="", flush=True)
    
    def _display_final_results(self):
        """Display final backtest results."""
        print("\n" + "=" * 100)
        print("📊 HISTORICAL BACKTEST RESULTS")
        print("=" * 100)
        print(f"Backtest Period: {self.start_date} to {self.end_date}")
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Timeframe: {self.timeframe}")
        print()
        
        # Overall Performance
        self._display_overall_performance()
        print()
        
        # Strategy Performance
        self._display_strategy_performance()
        print()
        
        # All Trades
        self._display_all_trades()
        print()
        
        # All Signals
        self._display_all_signals()
        print()
        
        # Save results to JSON (for backward compatibility)
        self._save_results_to_json()
    
    def _display_overall_performance(self):
        """Display overall performance metrics."""
        print("📊 OVERALL PERFORMANCE")
        print("-" * 50)
        
        total_equity = self.starting_cash + self.total_pnl
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        print(f"Starting Capital: ${self.starting_cash:,.2f}")
        print(f"Final Equity:     ${total_equity:,.2f}")
        print(f"Total PnL:        ${self.total_pnl:,.2f}")
        print(f"Return:           {(self.total_pnl / self.starting_cash * 100):.2f}%")
        print(f"Total Trades:     {self.total_trades}")
        print(f"Win Rate:         {win_rate:.1f}%")
        print(f"Max Drawdown:     {self.max_drawdown * 100:.2f}%")
    
    def _display_strategy_performance(self):
        """Display performance for each strategy."""
        print("📈 STRATEGY PERFORMANCE")
        print("-" * 80)
        print(f"{'Strategy':<20} | {'PnL':<12} | {'Return':<8} | {'Trades':<7} | {'Win Rate':<9} | {'Signals':<7}")
        print("-" * 80)
        
        for strategy_name in self.strategies.keys():
            pnl = self.strategy_pnl[strategy_name]
            trades = len(self.strategy_trades[strategy_name])
            signals = len(self.strategy_signals[strategy_name])
            
            # Calculate win rate for this strategy
            winning_trades = len([t for t in self.strategy_trades[strategy_name] if t.get('pnl', 0) > 0])
            win_rate = (winning_trades / trades * 100) if trades > 0 else 0
            
            # Calculate return
            return_pct = (pnl / self.starting_cash * 100) if self.starting_cash > 0 else 0
            
            print(f"{strategy_name:<20} | ${pnl:<11,.2f} | {return_pct:<7.2f}% | {trades:<7} | {win_rate:<8.1f}% | {signals:<7}")
    
    def _display_all_trades(self):
        """Display all trades."""
        print("🔄 ALL TRADES")
        print("-" * 80)
        print(f"{'Date':<12} | {'Strategy':<15} | {'Symbol':<6} | {'Side':<4} | {'Qty':<4} | {'Price':<8} | {'PnL':<10}")
        print("-" * 80)
        
        all_trades = []
        for strategy_name, trades in self.strategy_trades.items():
            for trade in trades:
                trade['strategy'] = strategy_name
                all_trades.append(trade)
        
        # Sort by timestamp
        all_trades.sort(key=lambda x: x.get('timestamp', datetime.min))
        
        for trade in all_trades:
            timestamp = trade.get('timestamp', 'Unknown')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%Y-%m-%d')
            
            symbol = trade.get('symbol', 'Unknown')
            side = trade.get('side', 'Unknown')
            quantity = trade.get('quantity', 0)
            price = trade.get('entry_price', 0)
            pnl = trade.get('pnl', 0)
            strategy = trade.get('strategy', 'Unknown')
            
            pnl_color = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
            
            print(f"{timestamp:<12} | {strategy:<15} | {symbol:<6} | {side:<4} | {quantity:<4} | ${price:<7.2f} | {pnl_color} ${pnl:<8,.2f}")
    
    def _display_all_signals(self):
        """Display all trading signals."""
        print("📡 ALL SIGNALS")
        print("-" * 90)
        print(f"{'Date':<12} | {'Strategy':<15} | {'Symbol':<6} | {'Action':<6} | {'Qty':<4} | {'Price':<8} | {'Reason':<20}")
        print("-" * 90)
        
        all_signals = []
        for strategy_name, signals in self.strategy_signals.items():
            for signal in signals:
                signal['strategy'] = strategy_name
                all_signals.append(signal)
        
        # Sort by timestamp
        all_signals.sort(key=lambda x: x.get('timestamp', datetime.min))
        
        for signal in all_signals:
            timestamp = signal.get('timestamp', 'Unknown')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%Y-%m-%d')
            
            strategy = signal.get('strategy', 'Unknown')
            symbol = signal.get('symbol', 'Unknown')
            action = signal.get('action', 'Unknown')
            price = signal.get('price', 0)
            quantity = signal.get('quantity', 0)
            reason = signal.get('reason', 'Unknown')
            
            action_icon = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚪"
            
            print(f"{timestamp:<12} | {strategy:<15} | {symbol:<6} | {action_icon} {action:<4} | {quantity:<4} | ${price:<7.2f} | {reason:<20}")
    
    def _save_results_to_json(self):
        """Save backtest results to JSON file (for backward compatibility)."""
        try:
            results = {
                'backtest_info': {
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'symbols': self.symbols,
                    'timeframe': self.timeframe,
                    'starting_cash': self.starting_cash
                },
                'overall_performance': {
                    'total_pnl': self.total_pnl,
                    'total_trades': self.total_trades,
                    'winning_trades': self.winning_trades,
                    'max_drawdown': self.max_drawdown,
                    'final_equity': self.starting_cash + self.total_pnl
                },
                'strategy_performance': {
                    name: {
                        'pnl': self.strategy_pnl[name],
                        'trades': len(self.strategy_trades[name]),
                        'signals': len(self.strategy_signals[name]),
                        'equity_curve': self.strategy_equity_curves[name]
                    }
                    for name in self.strategies.keys()
                },
                'trades': {
                    name: self.strategy_trades[name]
                    for name in self.strategies.keys()
                },
                'signals': {
                    name: self.strategy_signals[name]
                    for name in self.strategies.keys()
                },
                'database_run_ids': self.backtest_run_ids
            }
            
            # Save to JSON file
            filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {filename}")
            print(f"📊 Database run IDs: {self.backtest_run_ids}")
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    async def start(self):
        """Start the historical backtesting dashboard."""
        if self.is_running:
            logger.warning("Dashboard is already running")
            return
        
        success = await self.initialize()
        if not success:
            logger.error("Failed to initialize dashboard")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        logger.info("Historical Trading Dashboard started")
        logger.info(f"Backtesting {len(self.strategies)} strategies")
        logger.info(f"Symbols: {self.symbols}")
        logger.info(f"Period: {self.start_date} to {self.end_date}")
        
        # Run the backtest
        await self.run_backtest()
        
        # Cleanup
        await self.stop()
    
    async def stop(self):
        """Stop the dashboard."""
        self.is_running = False
        
        # Disconnect brokers
        for broker in self.brokers.values():
            await broker.disconnect()
        
        logger.info("Historical Trading Dashboard stopped")

async def main():
    """Main function to run the historical trading dashboard."""
    print("🚀 Starting Historical Trading Dashboard...")
    print("This will backtest all strategies with Polygon.io historical data")
    print()
    
    # Create dashboard
    dashboard = HistoricalTradingDashboard(
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
