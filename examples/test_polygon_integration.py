#!/usr/bin/env python3
"""
Test script for Polygon.io integration.
This script tests the data provider and basic functionality.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.polygon_data import polygon_data
import config

async def test_historical_data():
    """Test historical data retrieval."""
    print("Testing historical data retrieval...")
    
    try:
        # Get historical data for AAPL
        from_date = datetime.now() - timedelta(days=7)
        to_date = datetime.now()
        
        df = await polygon_data.get_historical_bars(
            symbol='AAPL',
            from_date=from_date,
            to_date=to_date,
            interval='1D'
        )
        
        if not df.empty:
            print(f"✓ Retrieved {len(df)} bars for AAPL")
            print(f"  Date range: {df.index[0]} to {df.index[-1]}")
            print(f"  Latest close: ${df['close'].iloc[-1]:.2f}")
        else:
            print("✗ No historical data retrieved")
            
    except Exception as e:
        print(f"✗ Error retrieving historical data: {e}")

async def test_real_time_price():
    """Test real-time price retrieval."""
    print("\nTesting real-time price retrieval...")
    
    try:
        price = await polygon_data.get_real_time_price('AAPL')
        if price:
            print(f"✓ Current AAPL price: ${price:.2f}")
        else:
            print("✗ No real-time price available")
            
    except Exception as e:
        print(f"✗ Error retrieving real-time price: {e}")

async def test_quote():
    """Test quote retrieval."""
    print("\nTesting quote retrieval...")
    
    try:
        quote = await polygon_data.get_quote('AAPL')
        if quote:
            print(f"✓ AAPL Quote:")
            print(f"  Bid: ${quote['bid']:.2f} (Size: {quote['bid_size']})")
            print(f"  Ask: ${quote['ask']:.2f} (Size: {quote['ask_size']})")
            print(f"  Spread: ${quote['ask'] - quote['bid']:.2f}")
        else:
            print("✗ No quote available")
            
    except Exception as e:
        print(f"✗ Error retrieving quote: {e}")

async def test_live_streaming():
    """Test live price streaming."""
    print("\nTesting live price streaming...")
    print("This will run for 10 seconds and show price updates...")
    
    price_updates = []
    
    def on_price_update(tick_data):
        price_updates.append(tick_data)
        print(f"  {tick_data['symbol']}: ${tick_data['price']:.2f} at {tick_data['timestamp']}")
    
    try:
        # Start streaming for 10 seconds
        streaming_task = asyncio.create_task(
            polygon_data.stream_live_prices(['AAPL', 'MSFT'], on_price_update)
        )
        
        # Wait for 10 seconds
        await asyncio.sleep(10)
        
        # Stop streaming
        await polygon_data.stop_streaming()
        
        print(f"✓ Received {len(price_updates)} price updates")
        
    except Exception as e:
        print(f"✗ Error in live streaming: {e}")

async def test_paper_executor():
    """Test paper trading executor."""
    print("\nTesting paper trading executor...")
    
    try:
        from brokers.paper_executor import PaperExecutor
        
        # Create executor
        executor = PaperExecutor(starting_cash=10000)
        
        # Place a market order
        order_result = await executor.place_order(
            symbol='AAPL',
            side='buy',
            quantity=10,
            order_type='market'
        )
        
        print(f"✓ Placed order: {order_result}")
        
        # Simulate a price update
        tick_data = {
            'symbol': 'AAPL',
            'price': 150.0,
            'timestamp': datetime.now(),
            'size': 100
        }
        
        await executor.process_price_update(tick_data)
        
        # Get portfolio summary
        portfolio = executor.get_portfolio_summary()
        print(f"✓ Portfolio summary:")
        print(f"  Cash: ${portfolio['cash']:,.2f}")
        print(f"  Total Equity: ${portfolio['total_equity']:,.2f}")
        print(f"  Unrealized PnL: ${portfolio['unrealized_pnl']:,.2f}")
        
    except Exception as e:
        print(f"✗ Error testing paper executor: {e}")

async def main():
    """Main test function."""
    print("="*60)
    print("POLYGON.IO INTEGRATION TEST")
    print("="*60)
    
    # Check API key
    if config.POLYGON_API_KEY == "YOUR_API_KEY":
        print("✗ Please set your Polygon.io API key in config.py or environment variable")
        print("  Example: export POLYGON_API_KEY='your_api_key_here'")
        return
    
    print(f"✓ Using API key: {config.POLYGON_API_KEY[:10]}...")
    
    # Run tests
    await test_historical_data()
    await test_real_time_price()
    await test_quote()
    await test_paper_executor()
    
    # Note: Live streaming test is commented out as it requires market hours
    # Uncomment the line below to test live streaming during market hours
    # await test_live_streaming()
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
