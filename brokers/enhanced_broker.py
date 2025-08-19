import asyncio
import logging
import pandas as pd
from typing import Any, Dict, Optional
from core.base import BrokerBase
from core.registry import BrokerRegistry
from brokers.paper_broker import PaperBroker

logger = logging.getLogger(__name__)

@BrokerRegistry.register("enhanced")
class EnhancedBroker(BrokerBase):
    """
    Enhanced broker that uses paper trading with Polygon.io data.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        
        # Initialize paper broker
        self.paper_broker = None
        self.current_broker = None
        
        # Setup broker
        self._setup_brokers()
    
    def _setup_brokers(self):
        """Setup paper broker."""
        try:
            # Initialize paper broker
            self.paper_broker = PaperBroker("paper_broker", self.config)
            self.current_broker = self.paper_broker
            logger.info("Paper broker initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to setup broker: {e}")
            raise
    
    async def _get_available_broker(self) -> BrokerBase:
        """Get the available broker."""
        if self.current_broker:
            return self.current_broker
        else:
            raise Exception("No broker available")
    
    async def _is_broker_available(self, broker: BrokerBase) -> bool:
        """Check if a broker is available."""
        try:
            if isinstance(broker, PaperBroker):
                return True  # Paper broker is always available
            else:
                return False
        except Exception as e:
            logger.error(f"Broker availability check failed: {e}")
            return False
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information from available broker."""
        try:
            broker = await self._get_available_broker()
            return await broker.get_account_info()
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    async def place_order(
        self, 
        order: Dict[str, Any], 
        stop_loss: float = None, 
        take_profit: float = None
    ) -> Dict[str, Any]:
        """Place order with available broker."""
        try:
            broker = await self._get_available_broker()
            result = await broker.place_order(order, stop_loss, take_profit)
            
            # Add broker info to result
            result['broker_used'] = 'paper'
            
            return result
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    async def get_positions(self) -> list[Dict[str, Any]]:
        """Get positions from available broker."""
        try:
            broker = await self._get_available_broker()
            return await broker.get_positions()
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise
    
    async def get_orders(self) -> list[Dict[str, Any]]:
        """Get orders from available broker."""
        try:
            broker = await self._get_available_broker()
            return await broker.get_orders()
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel order with available broker."""
        try:
            broker = await self._get_available_broker()
            return await broker.cancel_order(order_id)
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise
    
    async def cancel_all_orders(self) -> Dict[str, Any]:
        """Cancel all orders with available broker."""
        try:
            broker = await self._get_available_broker()
            return await broker.cancel_all_orders()
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            raise
    
    async def get_open_orders(self) -> list[Dict[str, Any]]:
        """Get open orders from available broker."""
        try:
            broker = await self._get_available_broker()
            return await broker.get_open_orders()
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    async def get_historical_data(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical data from available broker."""
        try:
            broker = await self._get_available_broker()
            return await broker.get_historical_data(symbol, timeframe, start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return pd.DataFrame()
    
    async def stream_market_data(self, symbol: str, on_data: callable, asset_type: str = "stock"):
        """Stream market data from available broker."""
        try:
            broker = await self._get_available_broker()
            return await broker.stream_market_data(symbol, on_data, asset_type)
        except Exception as e:
            logger.error(f"Failed to stream market data: {e}")
            raise
    
    async def get_broker_status(self) -> Dict[str, Any]:
        """Get status of broker."""
        status = {}
        
        if self.paper_broker:
            status['paper'] = {
                'available': await self._is_broker_available(self.paper_broker),
                'type': 'primary',
                'connected': True  # Paper broker is always connected
            }
        
        return status
    
    async def get_trading_mode(self) -> str:
        """Get current trading mode."""
        return "paper"
