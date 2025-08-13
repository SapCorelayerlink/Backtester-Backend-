#!/usr/bin/env python3
"""
Test IBKR Connection with Different Client IDs
"""

import asyncio
import sys
import os
import random

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_with_client_id(client_id):
    """Test connection with a specific client ID"""
    print(f"🔌 Testing with client ID: {client_id}")
    
    try:
        from brokers.ibkr_manager import ibkr_manager
        
        # Try to connect
        await asyncio.wait_for(
            ibkr_manager.connect(host='127.0.0.1', port=4001, clientId=client_id),
            timeout=15.0
        )
        
        if ibkr_manager.is_connected():
            print(f"   ✅ Successfully connected with client ID {client_id}!")
            return True
        else:
            print(f"   ❌ Failed to connect with client ID {client_id}")
            return False
            
    except asyncio.TimeoutError:
        print(f"   ⏰ Timeout with client ID {client_id}")
        return False
    except Exception as e:
        print(f"   ❌ Error with client ID {client_id}: {e}")
        return False

async def main():
    """Main function"""
    print("🚀 Testing IBKR Connection with Different Client IDs")
    print("=" * 50)
    
    # Try different client IDs
    client_ids = [1, 2, 3, 100, 101, 102, 999, 1000]
    
    for client_id in client_ids:
        try:
            from brokers.ibkr_manager import ibkr_manager
            
            # Disconnect if already connected
            if ibkr_manager.is_connected():
                ibkr_manager.disconnect()
                await asyncio.sleep(1)
            
            # Test connection
            if await test_with_client_id(client_id):
                print(f"\n🎉 Success! Connected with client ID {client_id}")
                
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
                
                return
            else:
                print(f"   ❌ Failed with client ID {client_id}")
                
        except Exception as e:
            print(f"   ❌ Error testing client ID {client_id}: {e}")
        
        # Wait a bit between attempts
        await asyncio.sleep(2)
    
    print("\n❌ All client IDs failed")
    print("💡 Please check:")
    print("   - IBKR Gateway API settings")
    print("   - API connections are enabled")
    print("   - No other applications are using the connection")

if __name__ == "__main__":
    asyncio.run(main())
