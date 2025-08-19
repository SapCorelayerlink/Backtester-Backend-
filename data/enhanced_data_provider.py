import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class DataProviderBase(ABC):
    """Base class for data providers."""
    
    @abstractmethod
    async def get_historical_bars(self, symbol: str, from_date: datetime, to_date: datetime, interval: str) -> pd.DataFrame:
        """Get historical bar data."""
        pass
    
    @abstractmethod
    async def get_realtime_bars(self, symbol: str, interval: str) -> pd.DataFrame:
        """Get real-time bar data."""
        pass
    
    @abstractmethod
    async def subscribe_to_stream(self, symbol: str, interval: str, callback) -> bool:
        """Subscribe to real-time data stream."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the data provider is available."""
        pass

class PolygonDataProvider(DataProviderBase):
    """Polygon.io data provider for market data."""
    
    def __init__(self, polygon_api_key: str = None):
        self.polygon_api_key = polygon_api_key
        self.subscriptions = {}
        
    async def is_available(self) -> bool:
        """Check if Polygon.io is available."""
        try:
            return self.polygon_api_key is not None and self.polygon_api_key != "YOUR_API_KEY"
        except Exception as e:
            logger.error(f"Polygon.io availability check failed: {e}")
            return False
    
    async def get_historical_bars(
        self, 
        symbol: str, 
        from_date: datetime, 
        to_date: datetime, 
        interval: str = "1"
    ) -> pd.DataFrame:
        """Get historical bar data from Polygon.io."""
        try:
            if not await self.is_available():
                raise Exception("Polygon.io not available")
            
            # Use the existing polygon_data.py implementation
            from data.polygon_data import PolygonDataProvider as PolygonData
            polygon_data = PolygonData(self.polygon_api_key)
            
            return await polygon_data.get_historical_bars(symbol, from_date, to_date, interval)
            
        except Exception as e:
            logger.error(f"Polygon.io historical data error for {symbol}: {e}")
            raise
    
    async def get_realtime_bars(self, symbol: str, interval: str) -> pd.DataFrame:
        """Get real-time bar data from IBKR."""
        try:
            if not await self.is_available():
                raise Exception("IBKR not available")
            
            # This would need to be implemented based on IBKR's real-time data subscription
            # For now, return empty DataFrame
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"IBKR real-time data error for {symbol}: {e}")
            raise
    
    async def subscribe_to_stream(self, symbol: str, interval: str, callback) -> bool:
        """Subscribe to real-time data stream from IBKR."""
        try:
            if not await self.is_available():
                return False
            
            # Implementation would depend on IBKR's streaming API
            # For now, return False to indicate not available
            return False
            
        except Exception as e:
            logger.error(f"IBKR stream subscription error for {symbol}: {e}")
            return False
    
class PolygonDataProvider(DataProviderBase):
    """Polygon.io data provider."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.rest_client = None
        self.ws_client = None
        self.is_connected = False
        self.price_callbacks = []
        self.last_request_time = 0
        self.min_request_interval = 0.1
        
        # Initialize Polygon client
        try:
            from polygon import RESTClient, WebSocketClient
            self.rest_client = RESTClient(self.api_key)
            self.ws_client = WebSocketClient(self.api_key)
        except ImportError:
            logger.error("Polygon library not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Polygon client: {e}")
    
    async def is_available(self) -> bool:
        """Check if Polygon.io is available."""
        try:
            if not self.rest_client:
                return False
            
            # Test with a simple request
            test_bars = self.rest_client.get_aggs(
                ticker="AAPL",
                multiplier=1,
                timespan="minute",
                from_=datetime.now().strftime('%Y-%m-%d'),
                to=datetime.now().strftime('%Y-%m-%d'),
                limit=1
            )
            return len(test_bars) > 0
            
        except Exception as e:
            logger.error(f"Polygon availability check failed: {e}")
            return False
    
    async def get_historical_bars(
        self, 
        symbol: str, 
        from_date: datetime, 
        to_date: datetime, 
        interval: str = "1"
    ) -> pd.DataFrame:
        """Get historical bar data from Polygon.io."""
        try:
            if not await self.is_available():
                raise Exception("Polygon.io not available")
            
            # Rate limiting
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
                        await asyncio.sleep(2 ** attempt)
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
                    'volume': bar.volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            logger.error(f"Polygon historical data error for {symbol}: {e}")
            raise
    
    async def get_realtime_bars(self, symbol: str, interval: str) -> pd.DataFrame:
        """Get real-time bar data from Polygon.io."""
        # Implementation would depend on Polygon's real-time API
        return pd.DataFrame()
    
    async def subscribe_to_stream(self, symbol: str, interval: str, callback) -> bool:
        """Subscribe to real-time data stream from Polygon.io."""
        try:
            if not self.ws_client:
                return False
            
            # Implementation would depend on Polygon's WebSocket API
            return False
            
        except Exception as e:
            logger.error(f"Polygon stream subscription error for {symbol}: {e}")
            return False

class EnhancedDataProvider:
    """
    Enhanced data provider that uses Polygon.io for market data.
    """
    
    def __init__(self, polygon_api_key: str = None):
        self.polygon_provider = PolygonDataProvider(polygon_api_key) if polygon_api_key else None
        self.current_provider = None
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup Polygon.io provider."""
        if self.polygon_provider:
            self.current_provider = self.polygon_provider
        else:
            raise ValueError("Polygon.io data provider must be configured")
    
    async def _get_available_provider(self) -> DataProviderBase:
        """Get the available provider."""
        if self.current_provider and await self.current_provider.is_available():
            return self.current_provider
        else:
            raise Exception("No data providers available")
    
    async def get_historical_bars(
        self, 
        symbol: str, 
        from_date: datetime, 
        to_date: datetime, 
        interval: str = "1"
    ) -> pd.DataFrame:
        """Get historical bar data with fallback logic."""
        try:
            provider = await self._get_available_provider()
            return await provider.get_historical_bars(symbol, from_date, to_date, interval)
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            raise
    
    async def get_realtime_bars(self, symbol: str, interval: str) -> pd.DataFrame:
        """Get real-time bar data with fallback logic."""
        try:
            provider = await self._get_available_provider()
            return await provider.get_realtime_bars(symbol, interval)
        except Exception as e:
            logger.error(f"Failed to get real-time data for {symbol}: {e}")
            raise
    
    async def subscribe_to_stream(self, symbol: str, interval: str, callback) -> bool:
        """Subscribe to real-time data stream with fallback logic."""
        try:
            provider = await self._get_available_provider()
            return await provider.subscribe_to_stream(symbol, interval, callback)
        except Exception as e:
            logger.error(f"Failed to subscribe to stream for {symbol}: {e}")
            return False
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of provider."""
        status = {}
        
        if self.polygon_provider:
            status['polygon'] = {
                'available': await self.polygon_provider.is_available(),
                'type': 'primary'
            }
        
        return status
