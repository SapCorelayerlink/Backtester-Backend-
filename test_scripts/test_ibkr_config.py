#!/usr/bin/env python3
"""
Test IBKR Gateway Configuration
===============================

This script tests different IBKR Gateway connection scenarios
to help identify configuration issues.
"""

import asyncio
import sys
import os
import time

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_connection_scenario(host, port, client_id, description):
    """Test a specific connection scenario"""
    print(f"\n🔌 Testing: {description}")
    print(f"   Host: {host}, Port: {port}, Client ID: {client_id}")
    
    try:
        from ib_insync import IB
        
        # Create a new IB instance
        ib = IB()
        
        # Try to connect
        await asyncio.wait_for(
            ib.connectAsync(host, port, client_id),
            timeout=10.0
        )
        
        if ib.isConnected():
            print(f"   ✅ SUCCESS: {description}")
            ib.disconnect()
            return True
        else:
            print(f"   ❌ FAILED: {description}")
            return False
            
    except asyncio.TimeoutError:
        print(f"   ⏰ TIMEOUT: {description}")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {description} - {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 IBKR Gateway Configuration Test")
    print("=" * 50)
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test different scenarios
    scenarios = [
        # Standard configuration (Paper Trading)
        ('127.0.0.1', 4001, 1, "Standard localhost:4001 with client ID 1"),
        ('127.0.0.1', 4001, 999, "Standard localhost:4001 with client ID 999"),
        ('localhost', 4001, 1, "localhost (name) with client ID 1"),
        
        # Alternative ports (in case IBKR Gateway is configured differently)
        ('127.0.0.1', 4002, 1, "Alternative port 4002"),
        ('127.0.0.1', 4003, 1, "Alternative port 4003"),
        ('127.0.0.1', 7496, 1, "TWS default port 7496"),
        ('127.0.0.1', 7497, 1, "TWS default port 7497"),
        
        # Different client IDs
        ('127.0.0.1', 4001, 100, "Client ID 100"),
        ('127.0.0.1', 4001, 200, "Client ID 200"),
        ('127.0.0.1', 4001, 300, "Client ID 300"),
    ]
    
    successful_tests = 0
    total_tests = len(scenarios)
    
    for host, port, client_id, description in scenarios:
        if await test_connection_scenario(host, port, client_id, description):
            successful_tests += 1
            print(f"   🎉 Found working configuration!")
            break
        await asyncio.sleep(1)  # Wait between tests
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Configuration Test Summary")
    print("=" * 50)
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    
    if successful_tests > 0:
        print("🎉 Found a working configuration!")
        print("💡 Use this configuration in your trading scripts")
    else:
        print("❌ No working configuration found")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check IBKR Gateway API settings:")
        print("   - Enable 'ActiveX and Socket Clients'")
        print("   - Set Socket port to 4001")
        print("   - Enable 'Allow connections from localhost'")
        print("2. Try temporarily disabling Windows Firewall")
        print("3. Check IBKR Gateway logs for specific errors")
        print("4. Verify your IBKR account has API access enabled")
    
    print("\n" + "=" * 50)
    print("🔗 Next Steps:")
    if successful_tests > 0:
        print("1. Use the working configuration")
        print("2. Run: python quick_ibkr_test.py")
        print("3. Start your trading strategies")
    else:
        print("1. Fix IBKR Gateway configuration")
        print("2. Try disabling firewall temporarily")
        print("3. Check IBKR Gateway logs")
        print("4. Contact IBKR support if needed")

if __name__ == "__main__":
    asyncio.run(main())
