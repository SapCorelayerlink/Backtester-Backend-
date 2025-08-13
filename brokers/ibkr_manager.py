import asyncio
import random
# import threading # No longer needed
from ib_insync import IB

class IBKRManager:
    """
    Manages a single, persistent connection to Interactive Brokers
    using the existing asyncio event loop.
    """
    def __init__(self):
        self.ib = IB()

    async def connect(self, host='127.0.0.1', port=4001, clientId=None):
        """Asynchronously connects to IBKR."""
        if self.ib.isConnected():
            print("Already connected to IBKR.")
            return

        if clientId is None:
            # Use a fixed client ID to ensure stable reconnections without creating competing sessions.
            # This allows the app to reclaim its session on auto-reload.
            clientId = 1

        try:
            print(f"Connecting to IBKR with clientId {clientId}...")
            # connectAsync will use the running asyncio event loop
            await self.ib.connectAsync(host, port, clientId, timeout=20)
            print("Successfully connected to IBKR.")
        except Exception as e:
            print(f"API connection failed: {e}")
            # Re-raise to stop application startup, which is the correct behavior
            raise

    def disconnect(self):
        """Disconnects from IBKR."""
        if self.ib.isConnected():
            print("Disconnecting from IBKR...")
            self.ib.disconnect()
        print("Disconnected.")

    def is_connected(self):
        """Returns True if connected to IBKR."""
        return self.ib.isConnected()

# Create a single, global instance of the manager
ibkr_manager = IBKRManager() 