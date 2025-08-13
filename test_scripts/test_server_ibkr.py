#!/usr/bin/env python3
"""
Test IBKR Connection using Server's IBKR Manager
================================================

This script tests the IBKR connection using the same manager
that the FastAPI server uses.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_server_ibkr():
    """Test IBKR connection using the server's manager"""
    print("🔌 Testing IBKR Connection with Server Manager")
    print("=" * 50)
    
    try:
        # Import the server's IBKR manager
        from brokers.ibkr_manager import ibkr_manager
        
        print("1. Checking current connection status...")
        if ibkr_manager.is_connected():
            print("   ✅ Already connected to IBKR!")
            return True
        
        print("2. Attempting to connect...")
        print("   🔌 Connecting to IBKR Gateway...")
        
        # Try to connect
        await ibkr_manager.connect(host='127.0.0.1', port=4001, clientId=1)
        
        if ibkr_manager.is_connected():
            print("   ✅ Successfully connected to IBKR!")
            
            # Test account info
            print("\n3. Testing account information...")
            try:
                account_summary = await ibkr_manager.ib.accountSummaryAsync()
                if account_summary:
                    print("   ✅ Account info retrieved:")
                    for item in account_summary:
                        if item.tag in ['BuyingPower', 'NetLiquidation', 'TotalCashValue', 'AvailableFunds']:
                            print(f"      {item.tag}: ${item.value}")
                else:
                    print("   ⚠️  No account information available")
            except Exception as e:
                print(f"   ⚠️  Could not get account info: {e}")
            
            # Test market data
            print("\n4. Testing market data...")
            try:
                from ib_insync import Stock
                contract = Stock('AAPL', 'SMART', 'USD')
                
                print("   📡 Requesting AAPL market data...")
                ticker = ibkr_manager.ib.reqMktData(contract)
                
                # Wait a bit for data
                await asyncio.sleep(2)
                
                if ticker.last > 0:
                    print(f"   ✅ Market data working: AAPL = ${ticker.last:.2f}")
                else:
                    print("   ⚠️  No market data received (market might be closed)")
                
                # Cancel the market data request
                ibkr_manager.ib.cancelMktData(contract)
                
            except Exception as e:
                print(f"   ⚠️  Market data test failed: {e}")
            
            print("\n🎉 IBKR connection test successful!")
            print("💡 Your server should now be able to connect to IBKR")
            return True
            
        else:
            print("   ❌ Failed to connect to IBKR")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

async def main():
    """Main function"""
    try:
        success = await test_server_ibkr()
        
        if success:
            print("\n" + "=" * 50)
            print("✅ SUCCESS: IBKR Connection Working!")
            print("=" * 50)
            print("🎯 Next Steps:")
            print("1. Your server is now connected to IBKR")
            print("2. Test the API endpoints:")
            print("   - http://127.0.0.1:8000/api/v1/broker/ibkr/account-info")
            print("   - http://127.0.0.1:8000/api/v1/broker/ibkr/positions")
            print("3. Start your trading strategies!")
        else:
            print("\n" + "=" * 50)
            print("❌ FAILED: IBKR Connection Issues")
            print("=" * 50)
            print("🔧 Troubleshooting:")
            print("1. Make sure IBKR Gateway is logged in")
            print("2. Check API settings in IBKR Gateway:")
            print("   - Enable 'ActiveX and Socket Clients'")
            print("   - Set Socket port to 4001")
            print("   - Enable 'Allow connections from localhost'")
            print("3. Try temporarily disabling Windows Firewall")
            print("4. Check IBKR Gateway logs for errors")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
