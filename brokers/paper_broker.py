from core.base import BrokerBase
from core.registry import BrokerRegistry
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
import pandas as pd
from .paper_executor import PaperExecutor

logger = logging.getLogger(__name__)

@BrokerRegistry.register("paper")
class PaperBroker(BrokerBase):
    """
    Paper trading broker that simulates real trading without actual money.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        starting_cash = config.get('starting_cash', 100000) if config else 100000
        self.executor = PaperExecutor(starting_cash=starting_cash)
        self.is_connected = True  # Paper broker is always "connected"
        
        logger.info(f"Paper broker initialized with ${starting_cash:,.2f} starting cash")
    
    async def connect(self) -> bool:
        """Connect to the paper trading system."""
        self.is_connected = True
        logger.info("Paper broker connected")
        return True
    
    async def disconnect(self) -> bool:
        """Disconnect from the paper trading system."""
        self.is_connected = False
        logger.info("Paper broker disconnected")
        return True
    
    async def is_connected(self) -> bool:
        """Check if the broker is connected."""
        return self.is_connected
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        if not self.is_connected:
            raise Exception("Broker not connected")
        
        portfolio = self.executor.get_portfolio_summary()
        
        return {
            "account_summary": [
                {
                    "tag": "NetLiquidation",
                    "value": str(portfolio['total_equity']),
                    "currency": "USD",
                    "account": "PAPER"
                },
                {
                    "tag": "AvailableFunds",
                    "value": str(portfolio['cash']),
                    "currency": "USD",
                    "account": "PAPER"
                },
                {
                    "tag": "UnrealizedPnL",
                    "value": str(portfolio['unrealized_pnl']),
                    "currency": "USD",
                    "account": "PAPER"
                },
                {
                    "tag": "RealizedPnL",
                    "value": str(portfolio['realized_pnl']),
                    "currency": "USD",
                    "account": "PAPER"
                }
            ],
            "portfolio": portfolio
        }
    
    async def place_order(
        self, 
        order: Dict[str, Any], 
        stop_loss: float = None, 
        take_profit: float = None
    ) -> Dict[str, Any]:
        """
        Place an order through the paper trading system.
        
        Args:
            order: Order dictionary with keys: symbol, qty, side, order_type, limit_price
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
            
        Returns:
            Order response
        """
        if not self.is_connected:
            raise Exception("Broker not connected")
        
        try:
            symbol = order.get('symbol')
            qty = order.get('qty', 1)
            side = order.get('side', 'buy').lower()
            order_type = order.get('order_type', 'market').lower()
            limit_price = order.get('limit_price')
            
            # Validate inputs
            if not symbol:
                raise ValueError("Symbol is required")
            
            if qty <= 0:
                raise ValueError("Quantity must be positive")
            
            if side not in ['buy', 'sell']:
                raise ValueError("Side must be 'buy' or 'sell'")
            
            if order_type not in ['market', 'limit']:
                raise ValueError("Order type must be 'market' or 'limit'")
            
            if order_type == 'limit' and limit_price is None:
                raise ValueError("Limit price is required for limit orders")
            
            # Place the order
            result = await self.executor.place_order(
                symbol=symbol,
                side=side,
                quantity=qty,
                order_type=order_type,
                limit_price=limit_price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            logger.info(f"Placed paper order: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error placing paper order: {e}")
            raise
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        if not self.is_connected:
            raise Exception("Broker not connected")
        
        portfolio = self.executor.get_portfolio_summary()
        positions = []
        
        for pos in portfolio['positions']:
            positions.append({
                "symbol": pos['symbol'],
                "exchange": "PAPER",
                "currency": "USD",
                "position": pos['quantity'],
                "avg_cost": pos['avg_price'],
                "unrealized_pnl": pos['unrealized_pnl'],
                "realized_pnl": pos['realized_pnl'],
                "last_price": pos['last_price']
            })
        
        return positions
    
    async def get_open_orders(self) -> List[Dict[str, Any]]:
        """Get open orders."""
        if not self.is_connected:
            raise Exception("Broker not connected")
        
        portfolio = self.executor.get_portfolio_summary()
        return portfolio['open_orders']
    
    async def get_orders(self) -> List[Dict[str, Any]]:
        """Get open orders (alias for get_open_orders)."""
        return await self.get_open_orders()
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if not self.is_connected:
            raise Exception("Broker not connected")
        
        return await self.executor.cancel_order(order_id)
    
    async def cancel_all_orders(self, symbol: str = None) -> int:
        """Cancel all orders, optionally for a specific symbol."""
        if not self.is_connected:
            raise Exception("Broker not connected")
        
        return await self.executor.cancel_all_orders(symbol)
    
    async def get_trade_history(self) -> List[Dict[str, Any]]:
        """Get trade history."""
        if not self.is_connected:
            raise Exception("Broker not connected")
        
        return self.executor.get_trade_history()
    
    async def get_equity_history(self) -> List[Dict[str, Any]]:
        """Get equity history."""
        if not self.is_connected:
            raise Exception("Broker not connected")
        
        return self.executor.get_equity_history()
    
    async def process_price_update(self, tick_data: Dict[str, Any]):
        """
        Process a price update from the data provider.
        This method should be called by the paper trader when new price data arrives.
        """
        if not self.is_connected:
            return
        
        await self.executor.process_price_update(tick_data)
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary."""
        return self.executor.get_portfolio_summary()
    
    async def get_historical_data(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get historical OHLCV market data for a specific symbol and timeframe.
        This method is required by the BrokerBase interface.
        """
        # In paper trading, this would typically come from the data provider
        # For now, return empty DataFrame
        import pandas as pd
        return pd.DataFrame()
    
    async def stream_market_data(self, symbol: str, on_data: callable, asset_type: str = "stock"):
        """
        Stream real-time market data for a given symbol.
        This method is required by the BrokerBase interface.
        """
        # In paper trading, this would be handled by the data provider
        logger.info(f"Stream market data requested for {symbol} - handled by data provider")
        return True
    
    async def get_market_data(self, symbol: str, bar_size: str = "1 min", duration: str = "1 D") -> List[Dict[str, Any]]:
        """
        Get market data for a symbol.
        This is a placeholder - in paper trading, this would typically come from the data provider.
        """
        # In a real implementation, this would fetch data from the data provider
        # For now, return empty list
        return []
    
    async def subscribe_market_data(self, symbol: str, bar_size: str = "1 min"):
        """
        Subscribe to market data for a symbol.
        This is a placeholder - in paper trading, this would be handled by the data provider.
        """
        logger.info(f"Subscribed to market data for {symbol}")
        return True
    
    async def unsubscribe_market_data(self, symbol: str):
        """
        Unsubscribe from market data for a symbol.
        This is a placeholder - in paper trading, this would be handled by the data provider.
        """
        logger.info(f"Unsubscribed from market data for {symbol}")
        return True
