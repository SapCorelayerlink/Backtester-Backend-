from core.base import BrokerBase
from core.registry import BrokerRegistry
from typing import Dict, Any
import logging
import pandas as pd
import numpy as np
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
        """Generate realistic historical data for backtesting."""
        print(f"MockBroker: Getting historical data for {symbol} from {start_date} to {end_date}")
        
        # Create date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        date_range = pd.date_range(start=start_dt, end=end_dt, freq='D')
        
        # Generate realistic stock data
        base_price = 150.0  # Starting price
        data = []
        
        for i, date in enumerate(date_range):
            # Simulate realistic price movements
            daily_return = np.random.normal(0.001, 0.02)  # 0.1% mean, 2% volatility
            base_price *= (1 + daily_return)
            
            # Generate OHLC data
            open_price = base_price * (1 + np.random.normal(0, 0.005))
            high_price = max(open_price, base_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, base_price) * (1 - abs(np.random.normal(0, 0.01)))
            close_price = base_price
            
            # Ensure high >= max(open, close) and low <= min(open, close)
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            data.append({
                'Open': round(open_price, 2),
                'High': round(high_price, 2),
                'Low': round(low_price, 2),
                'Close': round(close_price, 2),
                'Volume': int(1000000 + np.random.normal(0, 200000))
            })
        
        df = pd.DataFrame(data, index=date_range)
        print(f"MockBroker: Generated {len(df)} days of data for {symbol}")
        print(f"MockBroker: DataFrame shape: {df.shape}")
        print(f"MockBroker: DataFrame columns: {df.columns.tolist()}")
        print(f"MockBroker: First few rows: {df.head()}")
        return df 