"""
Enhanced Strategy Base Class
Provides improved order execution logic, SELL signals, and timeframe support.
"""

import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from core.base import StrategyBase
from data.enhanced_data_provider import EnhancedDataProvider
from brokers.enhanced_broker import EnhancedBroker

logger = logging.getLogger(__name__)

class EnhancedStrategyBase(StrategyBase):
    """
    Enhanced strategy base that integrates with Polygon.io data provider
    and supports paper trading.
    """
    
    def __init__(self, name: str, broker: EnhancedBroker, params: dict = None):
        super().__init__(name, broker, params)
        
        # Initialize data provider
        self.data_provider = None
        self._setup_data_provider()
        
        # Strategy state
        self.is_running = False
        self.current_data = {}
        self.subscriptions = {}
        
        # Performance tracking
        self.trades = []
        self.initial_equity = 100000  # Default starting equity
        self.current_equity = self.initial_equity
        
    def _setup_data_provider(self):
        """Setup the enhanced data provider with Polygon.io."""
        try:
            # Get configuration from params or use defaults
            polygon_api_key = getattr(self.params, 'polygon_api_key', None) if self.params else None
            
            # If not in params, try to get from config
            if not polygon_api_key:
                try:
                    import config
                    polygon_api_key = getattr(config, 'POLYGON_API_KEY', None)
                except ImportError:
                    polygon_api_key = None
            
            # Initialize enhanced data provider
            self.data_provider = EnhancedDataProvider(
                polygon_api_key=polygon_api_key
            )
            
            logger.info(f"Enhanced data provider initialized for {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to setup data provider for {self.name}: {e}")
            raise
    
    async def init(self):
        """Initialize the strategy with data provider and broker."""
        try:
            print(f"Initializing {self.name} Enhanced Strategy")
            
            # Check data provider status
            if self.data_provider:
                provider_status = await self.data_provider.get_provider_status()
                print(f"Data Provider Status: {provider_status}")
            
            # Check broker status
            if isinstance(self.broker, EnhancedBroker):
                broker_status = await self.broker.get_broker_status()
                print(f"Broker Status: {broker_status}")
                
                trading_mode = await self.broker.get_trading_mode()
                print(f"Trading Mode: {trading_mode}")
            
            print(f"{self.name}: Enhanced initialization complete.")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.name}: {e}")
            raise
    
    async def get_historical_data(
        self, 
        symbol: str, 
        from_date: datetime, 
        to_date: datetime, 
        interval: str = "15"
    ) -> pd.DataFrame:
        """Get historical data using the enhanced data provider."""
        try:
            if not self.data_provider:
                raise Exception("Data provider not initialized")
            
            return await self.data_provider.get_historical_bars(
                symbol, from_date, to_date, interval
            )
            
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            raise
    
    async def subscribe_to_realtime_data(
        self, 
        symbol: str, 
        interval: str, 
        callback
    ) -> bool:
        """Subscribe to real-time data using the enhanced data provider."""
        try:
            if not self.data_provider:
                return False
            
            success = await self.data_provider.subscribe_to_stream(symbol, interval, callback)
            if success:
                self.subscriptions[symbol] = {
                    'interval': interval,
                    'callback': callback
                }
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to subscribe to real-time data for {symbol}: {e}")
            return False
    
    async def place_trade_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: int, 
        order_type: str = 'market',
        limit_price: float = None,
        stop_loss: float = None,
        take_profit: float = None
    ) -> Dict[str, Any]:
        """Place a trade order using the enhanced broker."""
        try:
            order = {
                'symbol': symbol,
                'qty': quantity,
                'side': side,
                'order_type': order_type
            }
            
            if limit_price:
                order['limit_price'] = limit_price
            
            result = await self.broker.place_order(order, stop_loss, take_profit)
            
            # Log the trade
            trade_info = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'order_type': order_type,
                'limit_price': limit_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'order_id': result.get('order_id'),
                'broker_used': result.get('broker_used', 'unknown'),
                'status': result.get('status', 'unknown')
            }
            
            self.trades.append(trade_info)
            
            logger.info(f"Trade placed: {trade_info}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to place trade order: {e}")
            raise
    
    async def get_current_positions(self) -> List[Dict[str, Any]]:
        """Get current positions from the enhanced broker."""
        try:
            return await self.broker.get_positions()
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information from the enhanced broker."""
        try:
            return await self.broker.get_account_info()
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {}
    
    async def run_backtest(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime, 
        interval: str = "15"
    ) -> Dict[str, Any]:
        """Run a backtest using historical data."""
        try:
            print(f"Running backtest for {symbol} from {start_date} to {end_date}")
            
            # Get historical data
            historical_data = await self.get_historical_data(
                symbol, start_date, end_date, interval
            )
            
            if historical_data.empty:
                return {"error": "No historical data available"}
            
            # Initialize strategy
            await self.init()
            
            # Process each bar
            results = []
            for timestamp, bar in historical_data.iterrows():
                # Convert bar to expected format
                bar_data = {
                    'timestamp': timestamp,
                    'open': bar['open'],
                    'high': bar['high'],
                    'low': bar['low'],
                    'close': bar['close'],
                    'volume': bar.get('volume', 0)
                }
                
                # Process the bar
                await self.on_bar(bar_data)
                
                # Track results
                results.append({
                    'timestamp': timestamp,
                    'close': bar['close'],
                    'equity': self.current_equity,
                    'positions': await self.get_current_positions()
                })
            
            # Get final results
            final_results = self.get_results()
            final_results['backtest_data'] = results
            
            return final_results
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return {"error": str(e)}
    
    def get_results(self) -> Dict[str, Any]:
        """Get strategy results with enhanced metrics."""
        try:
            total_trades = len(self.trades)
            winning_trades = len([t for t in self.trades if t.get('pnl', 0) > 0])
            losing_trades = len([t for t in self.trades if t.get('pnl', 0) < 0])
            
            total_pnl = self.current_equity - self.initial_equity
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'strategy_name': self.name,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'initial_equity': self.initial_equity,
                'current_equity': self.current_equity,
                'return_percentage': (total_pnl / self.initial_equity * 100) if self.initial_equity > 0 else 0,
                'trades': self.trades
            }
            
        except Exception as e:
            logger.error(f"Failed to get results: {e}")
            return {}
    
    async def start_live_trading(self, symbols: List[str], interval: str = "15"):
        """Start live trading with real-time data."""
        try:
            print(f"Starting live trading for {self.name}")
            
            # Initialize strategy
            await self.init()
            
            # Subscribe to real-time data for each symbol
            for symbol in symbols:
                success = await self.subscribe_to_realtime_data(
                    symbol, interval, self.on_bar
                )
                if success:
                    print(f"Subscribed to real-time data for {symbol}")
                else:
                    print(f"Failed to subscribe to real-time data for {symbol}")
            
            self.is_running = True
            print(f"Live trading started for {self.name}")
                
        except Exception as e:
            logger.error(f"Failed to start live trading: {e}")
            raise
    
    async def stop_live_trading(self):
        """Stop live trading."""
        try:
            self.is_running = False
            print(f"Live trading stopped for {self.name}")
        except Exception as e:
            logger.error(f"Failed to stop live trading: {e}")
    
    async def on_bar(self, bar_data: pd.Series):
        """
        Process each new bar. This method should be overridden by subclasses.
        
        Args:
            bar_data: Dictionary containing bar data with keys:
                     - timestamp: datetime
                     - open: float
                     - high: float
                     - low: float
                     - close: float
                     - volume: int
        """
        # This method should be implemented by subclasses
        pass
