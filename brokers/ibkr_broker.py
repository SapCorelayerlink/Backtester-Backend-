from core.base import BrokerBase
from core.registry import BrokerRegistry
from typing import Any, Dict
from ib_insync import IB, Stock, MarketOrder, LimitOrder, Trade, util, Forex
from fastapi import HTTPException
import nest_asyncio
import pandas as pd
from datetime import datetime
import asyncio
import logging

# Apply nest_asyncio to allow ib_insync to run in FastAPI's event loop
nest_asyncio.apply()

@BrokerRegistry.register("ibkr")
class IBKRBroker(BrokerBase):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        from brokers.ibkr_manager import ibkr_manager
        self.ib: IB = ibkr_manager.ib

    async def get_account_info(self) -> Dict[str, Any]:
        """Asynchronously retrieves account values."""
        if not self.ib.isConnected():
            raise HTTPException(status_code=503, detail="Broker not connected.")
        
        account_summary = await self.ib.accountSummaryAsync()
        
        if not account_summary:
            return {"account_summary": []}

        return {
            "account_summary": [
                {
                    "tag": v.tag, "value": v.value, "currency": v.currency, "account": v.account
                }
                for v in account_summary
            ]
        }

    async def place_order(
        self, order: Dict[str, Any], stop_loss: float = None, take_profit: float = None
    ) -> Dict[str, Any]:
        """Asynchronously places a simple or bracket order."""
        if not self.ib.isConnected():
            raise HTTPException(status_code=503, detail="Broker not connected.")

        symbol = order.get('symbol', 'AAPL')
        qty = order.get('qty', 1)
        side = order.get('side', 'buy').upper()
        order_type = order.get('order_type', 'MKT').upper()
        limit_price = order.get('limit_price')
        contract = Stock(symbol, 'SMART', 'USD')
        
        if stop_loss or take_profit:
            if side not in ['BUY', 'SELL']:
                raise HTTPException(status_code=400, detail="Side must be BUY or SELL for bracket orders.")
            if not limit_price:
                raise HTTPException(status_code=400, detail="Limit price is required for bracket orders.")

            bracket = self.ib.bracketOrder(
                action=side, quantity=qty, limitPrice=limit_price,
                takeProfitPrice=take_profit, stopLossPrice=stop_loss
            )
            trades = [self.ib.placeOrder(contract, o) for o in bracket]
            result = trades 
        else:
            if order_type == 'MKT':
                ib_order = MarketOrder(side, qty)
            elif order_type == 'LMT' and limit_price:
                ib_order = LimitOrder(side, qty, limit_price)
            else:
                raise HTTPException(status_code=400, detail="Unsupported order type or missing limit price for LMT.")
            
            result = self.ib.placeOrder(contract, ib_order)

        if isinstance(result, list): # Bracket Order
            parent_trade = result[0]
            child_trades = result[1:]
            return {
                "parent_order_id": parent_trade.order.orderId,
                "status": parent_trade.orderStatus.status,
                "children": [{"id": t.order.orderId, "type": t.order.orderType, "status": t.orderStatus.status} for t in child_trades]
            }
        elif isinstance(result, Trade): # Simple Order
            return {"order_id": result.order.orderId, "status": result.orderStatus.status}
        else:
            return {"error": "Failed to place order for an unknown reason."}

    async def get_positions(self) -> list[Dict[str, Any]]:
        """Asynchronously retrieves current positions."""
        if not self.ib.isConnected():
            raise HTTPException(status_code=503, detail="Broker not connected.")
        
        positions = await self.ib.reqPositionsAsync()

        return [
            {"symbol": p.contract.symbol, "exchange": p.contract.exchange, "currency": p.contract.currency, "position": p.position, "avg_cost": p.avgCost}
            for p in positions
        ] if positions else []

    async def get_open_orders(self) -> list[Dict[str, Any]]:
        """Asynchronously retrieves all open orders for the account."""
        if not self.ib.isConnected():
            raise HTTPException(status_code=503, detail="Broker not connected.")
            
        orders = await self.ib.reqAllOpenOrdersAsync()
        
        return [
            {"orderId": o.order.orderId, "symbol": o.contract.symbol, "action": o.order.action, "totalQuantity": o.order.totalQuantity, "lmtPrice": o.order.lmtPrice, "orderType": o.order.orderType, "status": o.orderStatus.status}
            for o in orders
        ] if orders else []

    async def cancel_order(self, order_id: int) -> Dict[str, Any]:
        """Asynchronously cancels an open order."""
        if not self.ib.isConnected():
            raise HTTPException(status_code=503, detail="Broker not connected.")

        open_trades = await self.ib.reqOpenOrdersAsync()
        order_to_cancel = next((t.order for t in open_trades if t.order.orderId == order_id), None)
        
        if order_to_cancel:
            trade = self.ib.cancelOrder(order_to_cancel)
            return {"order_id": trade.order.orderId, "status": trade.orderStatus.status}
        else:
            raise HTTPException(status_code=404, detail=f"Order ID {order_id} not found or not open.")

    async def cancel_all_orders(self) -> Dict[str, Any]:
        """Asynchronously cancels all active (pending) open orders on the account."""
        if not self.ib.isConnected():
            raise HTTPException(status_code=503, detail="Broker not connected.")
        
        open_trades = await self.ib.reqAllOpenOrdersAsync()

        orders_to_cancel = [trade.order for trade in open_trades if trade.orderStatus.isActive()]

        if not orders_to_cancel:
            return {"status": "success", "message": "No active orders found to cancel."}

        cancelled_trades = []
        for order in orders_to_cancel:
            trade = self.ib.cancelOrder(order)
            cancelled_trades.append(trade)

        await asyncio.sleep(1) 
        
        return {
            "status": "success",
            "message": f"Attempted to cancel {len(orders_to_cancel)} active orders.",
            "cancelled_orders": [
                {"order_id": t.order.orderId, "status": t.orderStatus.status}
                for t in cancelled_trades
            ]
        }

    async def stream_market_data(self, symbol: str, on_data: callable, asset_type: str = "stock"):
        """
        Streams live market data for a symbol and uses a callback to handle it.
        Dynamically determines contract type (Stock or Forex).
        """
        contract = None
        if asset_type.lower() == 'stock':
            contract = Stock(symbol, 'SMART', 'USD')
        elif asset_type.lower() == 'forex':
            contract = Forex(symbol)
        else:
            raise ValueError(f"Unsupported asset_type: {asset_type}")

        if not contract:
            logging.error(f"Could not create a contract for symbol {symbol} with asset_type {asset_type}")
            return

        generic_tick_list = "165,233,258"
        logging.info(f"Requesting market data for {symbol} with ticks: {generic_tick_list}")
        self.ib.reqMktData(contract, generic_tick_list, False, False)
        logging.info(f"Market data request for {symbol} sent.")

        def on_error(reqId, errorCode, errorString, contract):
            if errorCode in [10197, 2104, 2106, 2103, 2105, 2158]: 
                logging.warning(f"IBKR Info/Warning: reqId={reqId}, code={errorCode}, msg='{errorString}'")
            else:
                logging.error(f"IBKR Error: reqId={reqId}, code={errorCode}, msg='{errorString}'")

        if on_error not in self.ib.errorEvent:
            self.ib.errorEvent += on_error

        def on_pending_ticker(tickers):
            logging.debug(f"IBKR Ticker Event: Received {len(tickers)} tickers.")
            for ticker in tickers:
                if ticker.contract == contract:
                    logging.info(f"Full ticker data for {ticker.contract.symbol}:\n{util.tree(ticker)}")

                    data_to_send = {
                        "symbol": ticker.contract.symbol,
                        "time": ticker.time.isoformat() if ticker.time else None,
                        "last": round(ticker.last, 5) if ticker.last is not None else None,
                        "bid": round(ticker.bid, 5) if ticker.bid is not None else None,
                        "ask": round(ticker.ask, 5) if ticker.ask is not None else None,
                        "close": round(ticker.close, 5) if ticker.close is not None else None,
                        "open": round(ticker.open, 5) if ticker.open is not None else None,
                        "high": round(ticker.high, 5) if ticker.high is not None else None,
                        "low": round(ticker.low, 5) if ticker.low is not None else None,
                        "volume": ticker.volume,
                    }
                    logging.debug(f"Sending data for {ticker.contract.symbol}: {data_to_send}")
                    asyncio.create_task(on_data(data_to_send))

        self.ib.pendingTickersEvent += on_pending_ticker

        try:
            while self.ib.isConnected():
                await asyncio.sleep(1)
        finally:
            self.ib.pendingTickersEvent -= on_pending_ticker
            if on_error in self.ib.errorEvent:
                self.ib.errorEvent -= on_error
            self.ib.cancelMktData(contract)
            logging.info(f"Market data stream for {symbol} stopped and cleaned up.")

    async def get_historical_data(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetches historical data from IBKR.
        """
        if not self.ib.isConnected():
            raise HTTPException(status_code=503, detail="Broker not connected.")

        contract = Stock(symbol, 'SMART', 'USD')
        
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD.")

        duration_days = (end_dt - start_dt).days
        if duration_days <= 0:
            raise HTTPException(status_code=400, detail="end_date must be after start_date.")
        
        duration_str = ''
        if duration_days > 365:
            years = duration_days // 365
            if years > 10: 
                years = 10
            duration_str = f'{years} Y'
        else:
            duration_str = f'{duration_days} D'

        bars = []
        try:
            bars = self.ib.reqHistoricalData(
                contract=contract,
                endDateTime=end_dt,
                durationStr=duration_str,
                barSizeSetting=timeframe,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
        except Exception as e:
            logging.error(f"Error fetching historical data from IBKR: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An error occurred with IBKR: {e}")

        if not bars:
            return pd.DataFrame()

        df = util.df(bars)
        return df 