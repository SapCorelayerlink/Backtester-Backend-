from core.base import BrokerBase
from core.registry import BrokerRegistry
from typing import Dict, Any
import logging
import pandas as pd
import asyncio
from datetime import datetime

@BrokerRegistry.register("mock")
class MockBroker(BrokerBase):
    def connect(self):
        print(f"{self.name}: Connected (mock)")

    def disconnect(self):
        print(f"{self.name}: Disconnected (mock)")

    async def place_order(
        self, order: Dict[str, Any], stop_loss: float = None, take_profit: float = None
    ) -> Dict[str, Any]:
        print(f"{self.name}: Placing order (mock): {order}")
        if stop_loss:
            print(f"   with stop_loss: {stop_loss}")
        if take_profit:
            print(f"   with take_profit: {take_profit}")
        return {"order_id": 1, "status": "filled"}

    async def get_account_info(self):
        print("MockBroker: Getting account info...")
        return {"account_name": "mock_account", "balance": 100000}

    async def get_positions(self) -> list[Dict[str, Any]]:
        print("MockBroker: Getting positions...")
        return [
            {
                "symbol": "MOCK",
                "exchange": "MOCKEX",
                "currency": "USD",
                "position": 100,
                "avg_cost": 50.0,
            }
        ]

    async def get_open_orders(self) -> list[Dict[str, Any]]:
        print("MockBroker: Getting open orders...")
        return [
            {
                "orderId": 99,
                "symbol": "MOCK",
                "action": "BUY",
                "totalQuantity": 10,
                "lmtPrice": 45.0,
                "orderType": "LMT",
                "status": "Submitted",
            }
        ]

    async def cancel_order(self, order_id: int) -> Dict[str, Any]:
        logging.info(f"MockBroker: Canceling order {order_id}")
        return {"status": "success", "order_id": order_id}

    async def cancel_all_orders(self) -> Dict[str, Any]:
        logging.info("MockBroker: Canceling all orders.")
        return {"status": "success", "message": "All mock orders cancelled."}

    async def stream_market_data(self, symbol: str, on_data: callable):
        """Mocks a stream of market data."""
        logging.info(f"MockBroker: Starting market data stream for {symbol}")
        try:
            price = 100
            while True:
                # Simulate a new tick every second
                await asyncio.sleep(1)
                price += 0.1
                # Create a mock ticker object and send it
                mock_tick = {
                    "symbol": symbol,
                    "last_price": round(price, 4),
                    "timestamp": datetime.now().isoformat()
                }
                await on_data(mock_tick)
        except asyncio.CancelledError:
            logging.info(f"MockBroker: Market data stream for {symbol} cancelled.")

    async def get_historical_data(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        logging.info(f"MockBroker: Getting historical data for {symbol} from {start_date} to {end_date}")
        # Return a sample DataFrame
        try:
            dates = pd.to_datetime([start_date, end_date])
            df = pd.DataFrame(index=pd.date_range(start=dates[0], end=dates[1], freq='D'))
            df['Open'] = [100 + i for i in range(len(df))]
            df['High'] = [105 + i for i in range(len(df))]
            df['Low'] = [95 + i for i in range(len(df))]
            df['Close'] = [102 + i for i in range(len(df))]
            df['Volume'] = [10000 + (i*100) for i in range(len(df))]
            return df
        except (ValueError, IndexError):
            return pd.DataFrame() 