#!/usr/bin/env python3
"""
Simple IBKR connection test script
Run this to verify your IB Gateway setup is working correctly
"""

import asyncio
import sys
from datetime import datetime

def print_header():
    """Print test header"""
    print("=" * 60)
    print("🔌 IBKR CONNECTION TEST")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Testing connection to Interactive Brokers Gateway...")
    print()

async def test_connection():
    """Test IBKR connection with comprehensive checks"""
    
    try:
        from ib_insync import IB, Stock
    except ImportError:
        print("❌ ERROR: ib-insync not installed")
        print("💡 Solution: pip install ib-insync")
        return False
    
    # Test different connection configurations
    test_configs = [
        {"port": 4002, "description": "IB Gateway Paper Trading", "recommended": True},
        {"port": 7497, "description": "TWS Paper Trading", "recommended": False},
        {"port": 4001, "description": "IB Gateway Live Trading", "recommended": False},
        {"port": 7496, "description": "TWS Live Trading", "recommended": False},
    ]
    
    for config in test_configs:
        port = config["port"]
        desc = config["description"]
        recommended = config["recommended"]
        
        print(f"📡 Testing {desc} (port {port}){'  ⭐ RECOMMENDED' if recommended else ''}")
        
        ib = IB()
        success = False
        
        try:
            # Try different client IDs
            for client_id in [999, 998, 997, 1, 2, 3]:
                try:
                    await ib.connectAsync('127.0.0.1', port, clientId=client_id, timeout=5)
                    if ib.isConnected():
                        success = True
                        print(f"   ✅ Connected successfully! (Client ID: {client_id})")
                        
                        # Test account info
                        try:
                            accounts = ib.managedAccounts()
                            if accounts:
                                print(f"   📊 Account(s): {', '.join(accounts)}")
                                
                                # Determine if paper or live
                                account = accounts[0]
                                if account.startswith('DU'):
                                    print(f"   🧪 Paper Trading Account Detected")
                                else:
                                    print(f"   💰 Live Trading Account Detected")
                            else:
                                print(f"   ⚠️ No accounts found")
                        except Exception as e:
                            print(f"   ⚠️ Account info error: {e}")
                        
                        # Test market data
                        try:
                            print(f"   📈 Testing market data...")
                            contract = Stock('QQQ', 'SMART', 'USD')
                            ib.qualifyContracts(contract)
                            
                            ticker = ib.reqMktData(contract)
                            await asyncio.sleep(2)  # Wait for data
                            
                            if hasattr(ticker, 'last') and ticker.last > 0:
                                print(f"   📊 QQQ Price: ${ticker.last:.2f}")
                                if hasattr(ticker, 'bid') and hasattr(ticker, 'ask'):
                                    if ticker.bid > 0 and ticker.ask > 0:
                                        print(f"   📊 Bid/Ask: ${ticker.bid:.2f}/${ticker.ask:.2f}")
                                print(f"   ✅ Market data is working!")
                            else:
                                print(f"   ⚠️ No market data (may be outside market hours)")
                            
                            ib.cancelMktData(contract)
                        except Exception as e:
                            print(f"   ⚠️ Market data test failed: {e}")
                        
                        # Test completed successfully
                        ib.disconnect()
                        print(f"   🔌 Disconnected cleanly")
                        print(f"   🎉 {desc} is working correctly!")
                        print()
                        
                        if recommended:
                            print(f"💡 RECOMMENDATION: Use this configuration for trading")
                            print(f"   Host: 127.0.0.1")
                            print(f"   Port: {port}")
                            print(f"   Client ID: {client_id}")
                            print()
                        
                        return True  # Found working connection
                        
                except Exception as e:
                    error_msg = str(e).lower()
                    if "already in use" in error_msg or "clientid" in error_msg:
                        continue  # Try next client ID
                    else:
                        break  # Different error, try next port
            
            if not success:
                print(f"   ❌ Connection failed")
                
        except Exception as e:
            print(f"   ❌ Connection error: {e}")
        finally:
            if ib.isConnected():
                ib.disconnect()
        
        print()
    
    return False

def print_troubleshooting():
    """Print troubleshooting help"""
    print("🔍 TROUBLESHOOTING GUIDE")
    print("=" * 40)
    print("❌ If all connections failed, check:")
    print()
    print("1. 🏃 IB Gateway/TWS is running and logged in")
    print("   - Launch IB Gateway or TWS")
    print("   - Log in with your IBKR credentials")
    print("   - Select Paper Trading mode (recommended)")
    print()
    print("2. ⚙️ API access is enabled")
    print("   - In Gateway: Configure → Settings → API → Settings")
    print("   - Check 'Enable ActiveX and Socket Clients'")
    print("   - Set Socket Port to 4002 (paper) or 4001 (live)")
    print("   - Add '127.0.0.1' to Trusted IPs")
    print("   - Click OK and restart Gateway")
    print()
    print("3. 🔥 Firewall is not blocking connections")
    print("   - Windows: Allow Python/Gateway through firewall")
    print("   - Mac: Check Security & Privacy settings")
    print("   - Antivirus: May need to add exceptions")
    print()
    print("4. 🔄 Try restarting everything")
    print("   - Close IB Gateway completely")
    print("   - Restart IB Gateway")
    print("   - Log in again")
    print("   - Run this test again")
    print()
    print("5. 🆔 Account issues")
    print("   - Ensure IBKR account is active")
    print("   - Check for any account restrictions")
    print("   - Try logging into IBKR website first")

def print_next_steps():
    """Print next steps for successful connection"""
    print("🚀 NEXT STEPS")
    print("=" * 40)
    print("✅ Your IBKR connection is working!")
    print()
    print("Ready to run the trading strategy:")
    print()
    print("1. 📊 Run a backtest:")
    print("   python backtest_ibkr.py")
    print()
    print("2. 🧪 Test with live data (paper trading):")
    print("   python -c \"")
    print("   import asyncio")
    print("   from intraday_supertrend_ma_strategy import IntradaySupertrendMA")
    print("   from brokers.ibkr_manager import ibkr_manager")
    print("   strategy = IntradaySupertrendMA('Test', ibkr_manager, {'symbol': 'QQQ'})")
    print("   asyncio.run(strategy.test_with_ibkr_gateway('QQQ', 5))\"")
    print()
    print("3. 📖 Read the documentation:")
    print("   - README.md - Complete guide")
    print("   - QUICK_START.md - 15-minute setup")
    print("   - IBKR_SETUP_GUIDE.md - Detailed IBKR setup")
    print()
    print("4. ⚙️ Customize parameters:")
    print("   - CONFIGURATION_GUIDE.md - Parameter details")
    print("   - USAGE_EXAMPLES.md - Example scripts")

async def main():
    """Main test function"""
    print_header()
    
    # Test connection
    success = await test_connection()
    
    print("=" * 60)
    if success:
        print_next_steps()
    else:
        print_troubleshooting()
    
    print("=" * 60)
    print("🎯 Connection test completed")
    
    return success

if __name__ == "__main__":
    try:
        # Handle different Python environments
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            pass
        
        # Run the test
        if sys.platform == "win32":
            # Windows
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        result = asyncio.run(main())
        
        # Exit with appropriate code
        sys.exit(0 if result else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Try running: pip install --upgrade ib-insync")
        sys.exit(1)
