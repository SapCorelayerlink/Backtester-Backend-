import asyncio
import websockets
import json

async def listen_to_stock(symbol):
    """
    Connects to the WebSocket for a given stock symbol and prints incoming messages.
    """
    uri = f"ws://127.0.0.1:8000/ws/IBKRBroker/market-data/stock/{symbol}"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Successfully connected to WebSocket for {symbol}.")
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"Received from {symbol}: {data}")
                except websockets.ConnectionClosed:
                    print(f"Connection closed for {symbol}.")
                    break
                except Exception as e:
                    print(f"An error occurred with {symbol}: {e}")
                    break
    except Exception as e:
        print(f"Failed to connect to WebSocket for {symbol}: {e}")

async def main():
    """
    Sets up concurrent listeners for a list of stock symbols.
    """
    # --- List of stocks to monitor ---
    stocks_to_watch = ["AAPL", "GOOG", "MSFT", "TSLA"]
    
    print("--- Starting WebSocket Test Client ---")
    print(f"Attempting to get real-time data for: {', '.join(stocks_to_watch)}")
    
    # Create a listening task for each stock
    tasks = [listen_to_stock(symbol) for symbol in stocks_to_watch]
    
    # Run all listening tasks concurrently
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    # This setup allows the async main function to be run.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nClient stopped by user.") 