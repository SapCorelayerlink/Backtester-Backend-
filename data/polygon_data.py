import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Callable, Optional, Dict, Any
import pandas as pd
from polygon import RESTClient, WebSocketClient
from polygon.websocket import WebSocketMessage, WebSocketClient
from polygon.websocket.models import WebSocketMessage
import config

logger = logging.getLogger(__name__)

class PolygonDataProvider:
    """
    Data provider for Polygon.io API and WebSocket streaming.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.POLYGON_API_KEY
        if self.api_key == "YOUR_API_KEY":
            raise ValueError("Please set your Polygon.io API key in config.py or environment variable POLYGON_API_KEY")
        
        self.rest_client = RESTClient(self.api_key)
        self.ws_client = None
        self.is_connected = False
        self.price_callbacks = []
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests to avoid rate limits
        
    async def get_historical_bars(
        self, 
        symbol: str, 
        from_date: datetime, 
        to_date: datetime, 
        interval: str = "1"
    ) -> pd.DataFrame:
        """
        Get historical bar data from Polygon.io.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            from_date: Start date
            to_date: End date
            interval: Time interval in minutes (1, 5, 15, 30, 60, 240, 1D, 1W, 1M)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Rate limiting - ensure minimum time between requests
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - time_since_last)
            
            # Convert interval to Polygon format
            if interval == "1D":
                multiplier = 1
                timespan = "day"
            elif interval == "1W":
                multiplier = 1
                timespan = "week"
            elif interval == "1M":
                multiplier = 1
                timespan = "month"
            else:
                multiplier = int(interval)
                timespan = "minute"
            
            # Get historical data with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    bars = self.rest_client.get_aggs(
                        ticker=symbol,
                        multiplier=multiplier,
                        timespan=timespan,
                        from_=from_date.strftime('%Y-%m-%d'),
                        to=to_date.strftime('%Y-%m-%d'),
                        limit=50000
                    )
                    self.last_request_time = time.time()
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit for {symbol}, retrying in {2 ** attempt} seconds...")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        raise e
            
            if not bars:
                logger.warning(f"No historical data found for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for bar in bars:
                data.append({
                    'timestamp': datetime.fromtimestamp(bar.timestamp / 1000),
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                    'vwap': bar.vwap if hasattr(bar, 'vwap') else None,
                    'transactions': bar.transactions if hasattr(bar, 'transactions') else None
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            logger.info(f"Retrieved {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def stream_live_prices(
        self, 
        symbols: List[str], 
        on_price_callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Stream live price data using Polygon WebSocket.
        
        Args:
            symbols: List of symbols to stream (e.g., ['AAPL', 'MSFT'])
            on_price_callback: Callback function to handle price updates
        """
        try:
            # Initialize WebSocket client
            self.ws_client = WebSocketClient(
                cluster="wss://delayed.polygon.io",  # Use delayed for paper trading
                auth_key=self.api_key
            )
            
            # Subscribe to trades for each symbol
            for symbol in symbols:
                self.ws_client.subscribe(f"T.{symbol}")
                logger.info(f"Subscribed to {symbol}")
            
            # Set up message handler
            @self.ws_client.on("T")
            def handle_trade(message: WebSocketMessage):
                try:
                    data = message.data
                    if data:
                        tick_data = {
                            'symbol': data.get('sym'),
                            'price': data.get('p'),
                            'size': data.get('s'),
                            'timestamp': datetime.fromtimestamp(data.get('t') / 1000),
                            'exchange': data.get('x'),
                            'conditions': data.get('c', [])
                        }
                        
                        # Call the callback function
                        on_price_callback(tick_data)
                        
                except Exception as e:
                    logger.error(f"Error processing trade message: {e}")
            
            # Set up connection handler
            @self.ws_client.on("connected")
            def handle_connected(message: WebSocketMessage):
                self.is_connected = True
                logger.info("Connected to Polygon WebSocket")
            
            @self.ws_client.on("disconnected")
            def handle_disconnected(message: WebSocketMessage):
                self.is_connected = False
                logger.info("Disconnected from Polygon WebSocket")
            
            # Start the WebSocket connection
            self.ws_client.run()
            
        except Exception as e:
            logger.error(f"Error setting up live price streaming: {e}")
            raise
    
    async def stop_streaming(self):
        """Stop the live price streaming."""
        if self.ws_client and self.is_connected:
            self.ws_client.close()
            self.is_connected = False
            logger.info("Stopped live price streaming")
    
    async def get_real_time_price(self, symbol: str) -> Optional[float]:
        """
        Get the current real-time price for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price or None if not available
        """
        try:
            # Get the latest trade
            trades = self.rest_client.get_last_trade(symbol)
            if trades:
                return trades.price
            return None
        except Exception as e:
            logger.error(f"Error getting real-time price for {symbol}: {e}")
            return None
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current quote (bid/ask) for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote data or None if not available
        """
        try:
            quote = self.rest_client.get_last_quote(symbol)
            if quote:
                return {
                    'symbol': symbol,
                    'bid': quote.bid_price,
                    'ask': quote.ask_price,
                    'bid_size': quote.bid_size,
                    'ask_size': quote.ask_size,
                    'timestamp': datetime.fromtimestamp(quote.timestamp / 1000)
                }
            return None
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None

# Global instance
polygon_data = PolygonDataProvider()
