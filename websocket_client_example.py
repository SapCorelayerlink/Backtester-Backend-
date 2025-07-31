import asyncio
import websockets
import json

async def listen_to_market_data():
    """
    Connects to the market data WebSocket and prints incoming messages.
    """
    # Use the 'mock' broker for a safe and easy test
    uri = "ws://127.0.0.1:8000/ws/mock/market-data/stock/AAPL"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Successfully connected to {uri}")
            print("Listening for realtime data... (Press CTRL+C to stop)")
            
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"Received data: {data}")
                except websockets.ConnectionClosed:
                    print("Connection closed.")
                    break
    except Exception as e:
        print(f"Failed to connect or an error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(listen_to_market_data()) 