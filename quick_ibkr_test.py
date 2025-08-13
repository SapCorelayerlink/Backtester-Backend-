#!/usr/bin/env python3
"""
Quick IBKR Connection Test
==========================

A simple script to test IBKR Gateway connection without starting the full API server.
This is useful for quick connectivity checks.

Usage:
    python quick_ibkr_test.py
"""

import asyncio
import sys
import os
import socket
import time

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_port_open(host='127.0.0.1', port=4001):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

async def quick_ibkr_test():
    """Quick test of IBKR connection"""
    print("🔍 Quick IBKR Connection Test")
    print("=" * 40)
    
    # Check if port is open
    print("1. Checking if IBKR Gateway is running...")
    if check_port_open():
        print("   ✅ Port 4001 is open (IBKR Gateway likely running)")
    else:
        print("   ❌ Port 4001 is closed")
        print("   📋 Please start IBKR Gateway first:")
        print("      - Open IBKR Gateway application")
        print("      - Configure port 4001")
        print("      - Enable API connections")
        return False
    
    # Test connection
    print("\n2. Testing IBKR connection...")
    try:
        from brokers.ibkr_manager import ibkr_manager
        
        print("   🔌 Attempting to connect...")
        await ibkr_manager.connect(host='127.0.0.1', port=4001, clientId=1)
        
        if ibkr_manager.is_connected():
            print("   ✅ Successfully connected to IBKR!")
            
            # Get basic account info
            print("\n3. Getting account information...")
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
            
            print("\n✅ IBKR connection test successful!")
            print("🎉 Your system is ready for trading!")
            return True
            
        else:
            print("   ❌ Failed to connect to IBKR")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

async def test_strategy_connection():
    """Test if we can create and initialize a strategy"""
    print("\n5. Testing strategy initialization...")
    
    try:
        from strategies.Supertrend import IntradaySupertrendMA
        from brokers.ibkr_broker import IBKRBroker
        
        # Create broker and strategy
        broker = IBKRBroker("test_broker")
        strategy_params = {
            'symbol': 'AAPL',
            'quantity': 1,
            'use_bracket_orders': False,
            'place_market_orders': False,
            'backfill_days': 0  # No backfill for quick test
        }
        
        strategy = IntradaySupertrendMA("test_strategy", broker, strategy_params)
        
        # Initialize strategy
        await strategy.init()
        print("   ✅ Strategy initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Strategy test failed: {e}")
        return False

async def main():
    """Main function"""
    try:
        # Test basic connection
        if not await quick_ibkr_test():
            return
        
        # Test strategy
        await test_strategy_connection()
        
        print("\n" + "=" * 40)
        print("🎯 All tests completed!")
        print("💡 You can now run the full test with: python test_ibkr_connection.py")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
