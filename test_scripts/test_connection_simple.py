#!/usr/bin/env python3
"""
Simple IBKR Connection Test with Extended Timeout
"""

import asyncio
import sys
import os
import socket

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_port():
    """Check if port 4001 is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(('127.0.0.1', 4001))
        sock.close()
        if result == 0:
            print("✅ Port 4001 is open")
            return True
        else:
            print(f"❌ Port 4001 is closed (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Error checking port: {e}")
        return False

async def test_connection():
    """Test IBKR connection with extended timeout"""
    print("🔌 Testing IBKR Connection with extended timeout...")
    
    try:
        from brokers.ibkr_manager import ibkr_manager
        
        print("   🔌 Attempting to connect with 30 second timeout...")
        
        # Try to connect with longer timeout
        await asyncio.wait_for(
            ibkr_manager.connect(host='127.0.0.1', port=4001, clientId=1),
            timeout=30.0
        )
        
        if ibkr_manager.is_connected():
            print("   ✅ Successfully connected to IBKR!")
            
            # Get account info
            print("\n💰 Getting account information...")
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
            
            return True
        else:
            print("   ❌ Failed to connect to IBKR")
            return False
            
    except asyncio.TimeoutError:
        print("   ❌ Connection timed out after 30 seconds")
        print("   💡 Make sure IBKR Gateway is fully loaded and configured")
        return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

async def main():
    """Main function"""
    print("🚀 Simple IBKR Connection Test")
    print("=" * 40)
    
    # Check port first
    print("1. Checking port 4001...")
    if not check_port():
        print("\n❌ IBKR Gateway doesn't seem to be running on port 4001")
        print("   Please check:")
        print("   - IBKR Gateway is started")
        print("   - API connections are enabled")
        print("   - Port 4001 is configured")
        return
    
    # Test connection
    print("\n2. Testing connection...")
    if await test_connection():
        print("\n✅ Connection successful!")
        print("🎉 Your IBKR Gateway is working!")
    else:
        print("\n❌ Connection failed")
        print("💡 Check IBKR Gateway configuration and try again")

if __name__ == "__main__":
    asyncio.run(main())
