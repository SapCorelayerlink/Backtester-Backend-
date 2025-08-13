#!/usr/bin/env python3
"""
Paper Trading System for Bactester
Integrates Polygon.io data with strategy execution and portfolio management.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.polygon_data import polygon_data
from brokers.paper_broker import PaperBroker
from core.registry import BrokerRegistry, StrategyRegistry
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PaperTrader:
    """
    Main paper trading system that coordinates data, strategy, and execution.
    """
    
    def __init__(
        self,
        symbols: List[str],
        strategy_name: str,
        starting_cash: float = None,
        strategy_params: Dict[str, Any] = None
    ):
        self.symbols = symbols
        self.strategy_name = strategy_name
        self.starting_cash = starting_cash or config.PAPER_STARTING_CASH
        self.strategy_params = strategy_params or {}
        
        # Initialize components
        self.broker = None
        self.strategy = None
        self.data_provider = polygon_data
        
        # State management
        self.is_running = False
        self.price_cache = {}  # Cache latest prices for each symbol
        
        logger.info(f"Paper trader initialized for symbols: {symbols}")
        logger.info(f"Strategy: {strategy_name}")
        logger.info(f"Starting cash: ${self.starting_cash:,.2f}")
    
    async def initialize(self):
        """Initialize the paper trading system."""
        try:
            # Initialize broker
            broker_config = {'starting_cash': self.starting_cash}
            self.broker = PaperBroker("paper_broker", broker_config)
            await self.broker.connect()
            
            # Get strategy class
            if self.strategy_name not in StrategyRegistry.strategies:
                raise ValueError(f"Strategy '{self.strategy_name}' not found. Available: {list(StrategyRegistry.strategies.keys())}")
            
            strategy_class = StrategyRegistry.strategies[self.strategy_name]
            
            # Initialize strategy
            self.strategy = strategy_class(
                name=self.strategy_name,
                broker=self.broker,
                params=self.strategy_params
            )
            
            # Initialize strategy
            await self.strategy.init()
            
            logger.info("Paper trading system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize paper trading system: {e}")
            raise
    
    async def start(self):
        """Start the paper trading system."""
        if self.is_running:
            logger.warning("Paper trader is already running")
            return
        
        try:
            await self.initialize()
            self.is_running = True
            
            logger.info("Starting paper trading system...")
            
            # Set up price update callback
            await self.data_provider.stream_live_prices(
                symbols=self.symbols,
                on_price_callback=self._handle_price_update
            )
            
        except Exception as e:
            logger.error(f"Failed to start paper trading system: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop the paper trading system."""
        if not self.is_running:
            return
        
        logger.info("Stopping paper trading system...")
        self.is_running = False
        
        try:
            # Stop data streaming
            await self.data_provider.stop_streaming()
            
            # Disconnect broker
            if self.broker:
                await self.broker.disconnect()
            
            logger.info("Paper trading system stopped")
            
        except Exception as e:
            logger.error(f"Error stopping paper trading system: {e}")
    
    async def _handle_price_update(self, tick_data: Dict[str, Any]):
        """
        Handle incoming price updates from Polygon WebSocket.
        
        Args:
            tick_data: Price tick data from Polygon
        """
        if not self.is_running:
            return
        
        try:
            symbol = tick_data['symbol']
            price = tick_data['price']
            timestamp = tick_data['timestamp']
            
            # Update price cache
            self.price_cache[symbol] = {
                'price': price,
                'timestamp': timestamp,
                'volume': tick_data.get('size', 0)
            }
            
            # Process price update in broker (for order execution)
            await self.broker.process_price_update(tick_data)
            
            # Create bar data for strategy
            bar_data = self._create_bar_data(symbol, tick_data)
            
            # Run strategy logic
            if self.strategy and bar_data is not None:
                await self.strategy.on_bar(bar_data)
            
            # Log significant price movements
            if self._is_significant_price_move(symbol, price):
                logger.info(f"Significant price move: {symbol} at ${price:.2f}")
            
        except Exception as e:
            logger.error(f"Error handling price update: {e}")
    
    def _create_bar_data(self, symbol: str, tick_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create bar data from tick data for strategy consumption.
        In a real implementation, this would aggregate ticks into bars.
        
        Args:
            symbol: Stock symbol
            tick_data: Price tick data
            
        Returns:
            Bar data or None if insufficient data
        """
        # For now, create a simple bar from the tick
        # In a real implementation, you'd aggregate multiple ticks into bars
        return {
            'symbol': symbol,
            'timestamp': tick_data['timestamp'],
            'open': tick_data['price'],
            'high': tick_data['price'],
            'low': tick_data['price'],
            'close': tick_data['price'],
            'volume': tick_data.get('size', 0)
        }
    
    def _is_significant_price_move(self, symbol: str, price: float) -> bool:
        """Check if a price move is significant enough to log."""
        if symbol not in self.price_cache:
            return False
        
        last_price = self.price_cache[symbol]['price']
        if last_price == 0:
            return False
        
        # Log if price change is more than 1%
        price_change = abs(price - last_price) / last_price
        return price_change > 0.01
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the paper trading system."""
        if not self.broker:
            return {'status': 'not_initialized'}
        
        portfolio = self.broker.get_portfolio_summary()
        
        return {
            'status': 'running' if self.is_running else 'stopped',
            'symbols': self.symbols,
            'strategy': self.strategy_name,
            'portfolio': portfolio,
            'price_cache': {
                symbol: {
                    'price': data['price'],
                    'timestamp': data['timestamp'].isoformat()
                }
                for symbol, data in self.price_cache.items()
            }
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.broker:
            return {}
        
        portfolio = self.broker.get_portfolio_summary()
        trades = self.broker.get_trade_history()
        equity_history = self.broker.get_equity_history()
        
        # Calculate performance metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        
        return {
            'portfolio': portfolio,
            'trades': trades,
            'equity_history': equity_history,
            'metrics': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'total_return': portfolio.get('total_return', 0)
            }
        }

async def main():
    """Main entry point for paper trading."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Paper Trading System')
    parser.add_argument('--symbols', nargs='+', default=['AAPL', 'MSFT'], 
                       help='List of symbols to trade')
    parser.add_argument('--strategy', default='sample_strategy', 
                       help='Strategy to use')
    parser.add_argument('--cash', type=float, default=100000, 
                       help='Starting cash amount')
    parser.add_argument('--params', type=str, default='{}', 
                       help='Strategy parameters as JSON')
    
    args = parser.parse_args()
    
    try:
        # Parse strategy parameters
        strategy_params = json.loads(args.params)
        
        # Create paper trader
        trader = PaperTrader(
            symbols=args.symbols,
            strategy_name=args.strategy,
            starting_cash=args.cash,
            strategy_params=strategy_params
        )
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(trader.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start trading
        await trader.start()
        
        # Keep running until interrupted
        while trader.is_running:
            await asyncio.sleep(1)
            
            # Print status every 30 seconds
            if datetime.now().second % 30 == 0:
                status = trader.get_status()
                portfolio = status['portfolio']
                print(f"\nStatus: {status['status']}")
                print(f"Equity: ${portfolio['total_equity']:,.2f}")
                print(f"Cash: ${portfolio['cash']:,.2f}")
                print(f"Unrealized PnL: ${portfolio['unrealized_pnl']:,.2f}")
                print(f"Total Return: {portfolio['total_return']:.2f}%")
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        if 'trader' in locals():
            await trader.stop()
        
        # Print final performance summary
        if 'trader' in locals():
            performance = trader.get_performance_summary()
            print("\n" + "="*50)
            print("FINAL PERFORMANCE SUMMARY")
            print("="*50)
            print(f"Total Trades: {performance['metrics']['total_trades']}")
            print(f"Win Rate: {performance['metrics']['win_rate']:.1f}%")
            print(f"Total PnL: ${performance['metrics']['total_pnl']:,.2f}")
            print(f"Total Return: {performance['metrics']['total_return']:.2f}%")
            print(f"Final Equity: ${performance['portfolio']['total_equity']:,.2f}")

if __name__ == "__main__":
    asyncio.run(main())
