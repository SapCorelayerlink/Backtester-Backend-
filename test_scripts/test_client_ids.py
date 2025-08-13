#!/usr/bin/env python3
"""
Test different client IDs for IBKR connection
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_client_id(client_id):
    """Test connection with a specific client ID"""
    try:
        from brokers.ibkr_manager import ibkr_manager
        
        print(f"Testing client ID: {client_id}")
        
        # Try to connect
        await ibkr_manager.connect(host='127.0.0.1', port=4001, clientId=client_id)
        
        if ibkr_manager.is_connected():
            print(f"   ✅ SUCCESS with client ID {client_id}")
            return True
        else:
            print(f"   ❌ FAILED with client ID {client_id}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR with client ID {client_id}: {e}")
        return False

async def main():
    """Test multiple client IDs"""
    print("🔍 Testing Different Client IDs")
    print("=" * 40)
    
    # Common client IDs to test
    client_ids = [1, 2, 199, 999, 1000]
    
    for client_id in client_ids:
        success = await test_client_id(client_id)
        if success:
            print(f"\n🎉 Found working client ID: {client_id}")
            print("💡 Update your ibkr_manager.py to use this client ID")
            break
        print()
    
    if not any([await test_client_id(cid) for cid in client_ids]):
        print("\n❌ No client ID worked")
        print("🔧 Check IBKR Gateway API settings:")

if __name__ == "__main__":
    asyncio.run(main())
