import asyncio
from ib_insync import IB

async def main():
    ib = IB()
    try:
        print("Attempting to connect to IB Gateway/TWS on 127.0.0.1:7497...")
        # Using a different clientId to avoid conflicts
        await ib.connectAsync('127.0.0.1', 7497, clientId=999, timeout=15)
        print("✅ Connection Successful!")
        print(f"   - Server Version: {ib.serverVersion()}")
        print(f"   - TWS Time: {await ib.reqCurrentTimeAsync()}")
        print(f"   - Managed Accounts: {ib.managedAccounts()}")
        ib.disconnect()
        print("Disconnected.")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("\nPlease check the following:")
        print("1. Is IB Gateway or TWS running on your machine?")
        print("2. Are you fully logged in (not at the username/password screen)?")
        print("3. In TWS/Gateway, go to 'File -> Global Configuration -> API -> Settings'.")
        print("   - Is 'Enable ActiveX and Socket Clients' checked?")
        print("   - Is the 'Socket port' number exactly 7497?")
        print("   - Under 'Trusted IP Addresses', have you added '127.0.0.1'?")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nProgram closed.") 