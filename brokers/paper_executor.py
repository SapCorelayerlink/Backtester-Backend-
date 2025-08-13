import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import pandas as pd
import config

logger = logging.getLogger(__name__)

@dataclass
class Order:
    """Represents a trading order."""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: int
    order_type: str  # 'market' or 'limit'
    limit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str = 'pending'  # 'pending', 'filled', 'cancelled', 'rejected'
    filled_price: Optional[float] = None
    filled_quantity: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    commission: float = 0.0

@dataclass
class Position:
    """Represents a position in a symbol."""
    symbol: str
    quantity: int = 0
    avg_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_price: float = 0.0

class PaperExecutor:
    """
    Paper trading execution simulator.
    Handles order execution, portfolio management, and PnL tracking.
    """
    
    def __init__(self, starting_cash: float = None):
        self.starting_cash = starting_cash or config.PAPER_STARTING_CASH
        self.cash = self.starting_cash
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.order_id_counter = 0
        self.trades: List[Dict[str, Any]] = []
        self.equity_history: List[Dict[str, Any]] = []
        
        # Configuration
        self.commission_rate = config.DEFAULT_COMMISSION
        self.slippage_rate = config.DEFAULT_SLIPPAGE
        
        logger.info(f"Paper executor initialized with ${self.starting_cash:,.2f} starting cash")
    
    def generate_order_id(self) -> str:
        """Generate a unique order ID."""
        self.order_id_counter += 1
        return f"PAPER_{self.order_id_counter:06d}"
    
    async def place_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: int, 
        order_type: str = 'market',
        limit_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            quantity: Number of shares
            order_type: 'market' or 'limit'
            limit_price: Limit price for limit orders
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Order details
        """
        order_id = self.generate_order_id()
        
        # Validate order
        if side not in ['buy', 'sell']:
            raise ValueError("Side must be 'buy' or 'sell'")
        
        if order_type == 'limit' and limit_price is None:
            raise ValueError("Limit price required for limit orders")
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        # Check if we have enough cash for buy orders
        if side == 'buy' and order_type == 'market':
            # Estimate cost (will be updated with actual price)
            estimated_cost = quantity * 100  # Rough estimate
            if self.cash < estimated_cost:
                raise ValueError(f"Insufficient cash. Need ~${estimated_cost:,.2f}, have ${self.cash:,.2f}")
        
        # Create order
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.orders[order_id] = order
        
        logger.info(f"Placed {order_type} {side} order for {quantity} {symbol} shares")
        
        return {
            'order_id': order_id,
            'status': 'pending',
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'order_type': order_type
        }
    
    async def process_price_update(self, tick_data: Dict[str, Any]):
        """
        Process a price update and check for order fills.
        
        Args:
            tick_data: Price tick data from Polygon
        """
        symbol = tick_data['symbol']
        price = tick_data['price']
        timestamp = tick_data['timestamp']
        
        # Update position's last price
        if symbol in self.positions:
            self.positions[symbol].last_price = price
        
        # Check pending orders for this symbol
        for order_id, order in self.orders.items():
            if order.symbol == symbol and order.status == 'pending':
                await self._check_order_fill(order, price, timestamp)
        
        # Update unrealized PnL
        self._update_unrealized_pnl()
        
        # Record equity
        self._record_equity(timestamp)
    
    async def _check_order_fill(self, order: Order, current_price: float, timestamp: datetime):
        """Check if an order should be filled at the current price."""
        
        if order.order_type == 'market':
            # Market orders fill immediately
            fill_price = current_price
            fill_quantity = order.quantity
            
        elif order.order_type == 'limit':
            # Limit orders check price conditions
            if order.side == 'buy' and current_price <= order.limit_price:
                fill_price = order.limit_price
                fill_quantity = order.quantity
            elif order.side == 'sell' and current_price >= order.limit_price:
                fill_price = order.limit_price
                fill_quantity = order.quantity
            else:
                return  # No fill
        
        else:
            return  # Unknown order type
        
        # Apply slippage
        if order.side == 'buy':
            fill_price *= (1 + self.slippage_rate)
        else:
            fill_price *= (1 - self.slippage_rate)
        
        # Execute the fill
        await self._execute_fill(order, fill_price, fill_quantity, timestamp)
    
    async def _execute_fill(self, order: Order, fill_price: float, fill_quantity: int, timestamp: datetime):
        """Execute an order fill."""
        
        # Calculate commission
        commission = fill_price * fill_quantity * self.commission_rate
        
        # Update cash
        if order.side == 'buy':
            total_cost = fill_price * fill_quantity + commission
            if self.cash < total_cost:
                logger.warning(f"Insufficient cash for order {order.id}. Need ${total_cost:,.2f}, have ${self.cash:,.2f}")
                order.status = 'rejected'
                return
            
            self.cash -= total_cost
        else:
            total_proceeds = fill_price * fill_quantity - commission
            self.cash += total_proceeds
        
        # Update position
        if order.symbol not in self.positions:
            self.positions[order.symbol] = Position(symbol=order.symbol)
        
        position = self.positions[order.symbol]
        
        if order.side == 'buy':
            # Calculate new average price
            total_cost = position.quantity * position.avg_price + fill_quantity * fill_price
            total_quantity = position.quantity + fill_quantity
            position.avg_price = total_cost / total_quantity if total_quantity > 0 else 0
            position.quantity += fill_quantity
        else:
            # Calculate realized PnL
            if position.quantity > 0:
                realized_pnl = (fill_price - position.avg_price) * min(fill_quantity, position.quantity)
                position.realized_pnl += realized_pnl
            
            position.quantity -= fill_quantity
            if position.quantity <= 0:
                position.quantity = 0
                position.avg_price = 0
        
        # Update order status
        order.filled_price = fill_price
        order.filled_quantity = fill_quantity
        order.commission = commission
        order.status = 'filled'
        
        # Record trade
        trade = {
            'order_id': order.id,
            'symbol': order.symbol,
            'side': order.side,
            'quantity': fill_quantity,
            'price': fill_price,
            'commission': commission,
            'timestamp': timestamp.isoformat()
        }
        self.trades.append(trade)
        
        logger.info(f"Filled {order.side} order for {fill_quantity} {order.symbol} at ${fill_price:.2f}")
    
    def _update_unrealized_pnl(self):
        """Update unrealized PnL for all positions."""
        for position in self.positions.values():
            if position.quantity != 0 and position.last_price > 0:
                if position.quantity > 0:  # Long position
                    position.unrealized_pnl = (position.last_price - position.avg_price) * position.quantity
                else:  # Short position
                    position.unrealized_pnl = (position.avg_price - position.last_price) * abs(position.quantity)
    
    def _record_equity(self, timestamp: datetime):
        """Record current equity."""
        total_equity = self.cash
        for position in self.positions.values():
            total_equity += position.unrealized_pnl
        
        self.equity_history.append({
            'timestamp': timestamp.isoformat(),
            'equity': total_equity,
            'cash': self.cash,
            'unrealized_pnl': sum(p.unrealized_pnl for p in self.positions.values())
        })
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary."""
        total_equity = self.cash
        total_unrealized_pnl = 0
        total_realized_pnl = 0
        
        for position in self.positions.values():
            total_equity += position.unrealized_pnl
            total_unrealized_pnl += position.unrealized_pnl
            total_realized_pnl += position.realized_pnl
        
        return {
            'cash': self.cash,
            'total_equity': total_equity,
            'unrealized_pnl': total_unrealized_pnl,
            'realized_pnl': total_realized_pnl,
            'total_return': ((total_equity - self.starting_cash) / self.starting_cash * 100) if self.starting_cash > 0 else 0,
            'positions': [
                {
                    'symbol': p.symbol,
                    'quantity': p.quantity,
                    'avg_price': p.avg_price,
                    'last_price': p.last_price,
                    'unrealized_pnl': p.unrealized_pnl,
                    'realized_pnl': p.realized_pnl
                }
                for p in self.positions.values() if p.quantity != 0
            ],
            'open_orders': [
                {
                    'order_id': o.id,
                    'symbol': o.symbol,
                    'side': o.side,
                    'quantity': o.quantity,
                    'order_type': o.order_type,
                    'status': o.status
                }
                for o in self.orders.values() if o.status == 'pending'
            ]
        }
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Get trade history."""
        return self.trades.copy()
    
    def get_equity_history(self) -> List[Dict[str, Any]]:
        """Get equity history."""
        return self.equity_history.copy()
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        if order_id in self.orders and self.orders[order_id].status == 'pending':
            self.orders[order_id].status = 'cancelled'
            logger.info(f"Cancelled order {order_id}")
            return True
        return False
    
    async def cancel_all_orders(self, symbol: str = None):
        """Cancel all pending orders, optionally for a specific symbol."""
        cancelled_count = 0
        for order in self.orders.values():
            if order.status == 'pending' and (symbol is None or order.symbol == symbol):
                order.status = 'cancelled'
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} orders")
        return cancelled_count
