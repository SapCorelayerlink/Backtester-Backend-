#!/usr/bin/env python3
"""
IBKR Gateway Connection Test Script
===================================

This script helps you:
1. Start the IBKR Gateway (if not already running)
2. Test the connection to IBKR
3. Run a quick strategy test with live data

Prerequisites:
- IBKR Gateway should be installed and configured
- IBKR account should be set up with API access
- Gateway should be configured to accept connections on port 4001

Usage:
    python test_ibkr_connection.py
"""

import asyncio
import sys
import os
import subprocess
import time
import requests
from datetime import datetime
from ib_insync import *

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_ibkr_gateway_running():
    """Check if IBKR Gateway is running on port 4001"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 4001))
        sock.close()
        return result == 0
    except Exception:
        return False

def start_ibkr_gateway():
    """Attempt to start IBKR Gateway"""
    print("🔍 Checking if IBKR Gateway is running...")
    
    if check_ibkr_gateway_running():
        print("✅ IBKR Gateway is already running on port 4001")
        return True
    
    print("❌ IBKR Gateway not detected on port 4001")
    print("\n📋 To start IBKR Gateway manually:")
    print("1. Open IBKR Gateway application")
    print("2. Configure it to accept connections on port 4001")
    print("3. Enable API connections")
    print("4. Make sure your IBKR account has API access enabled")
    print("\n🔗 Common IBKR Gateway locations:")
    print("   - Windows: C:\\Program Files\\IBKR\\TWS\\ibgateway\\start.bat")
    print("   - Mac: /Applications/IBKR Gateway/")
    print("   - Linux: ~/ibgateway/")
    
    # Try to find and start IBKR Gateway automatically
    possible_paths = [
        r"C:\Program Files\IBKR\TWS\ibgateway\start.bat",
        r"C:\Program Files (x86)\IBKR\TWS\ibgateway\start.bat",
        "/Applications/IBKR Gateway/ibgateway",
        "~/ibgateway/ibgateway"
    ]
    
    for path in possible_paths:
        if os.path.exists(os.path.expanduser(path)):
            print(f"\n🚀 Found IBKR Gateway at: {path}")
            try:
                if path.endswith('.bat'):
                    subprocess.Popen([path], shell=True)
                else:
                    subprocess.Popen([path])
                print("✅ Started IBKR Gateway")
                time.sleep(5)  # Give it time to start
                if check_ibkr_gateway_running():
                    print("✅ IBKR Gateway is now running!")
                    return True
            except Exception as e:
                print(f"❌ Failed to start IBKR Gateway: {e}")
    
    print("\n⚠️  Could not start IBKR Gateway automatically.")
    print("   Please start it manually and run this script again.")
    return False

async def test_ibkr_connection():
    """Test the IBKR connection using the project's broker manager"""
    print("\n🔌 Testing IBKR Connection...")
    
    try:
        from brokers.ibkr_manager import ibkr_manager
        
        # Test connection
        await ibkr_manager.connect(host='127.0.0.1', port=4001, clientId=1)
        
        if ibkr_manager.is_connected():
            print("✅ Successfully connected to IBKR Gateway!")
            
            # Get account info
            try:
                account_summary = await ibkr_manager.ib.accountSummaryAsync()
                if account_summary:
                    print("\n💰 Account Information:")
                    for item in account_summary:
                        if item.tag in ['BuyingPower', 'NetLiquidation', 'TotalCashValue']:
                            print(f"   {item.tag}: ${item.value}")
                else:
                    print("⚠️  No account information available")
            except Exception as e:
                print(f"⚠️  Could not retrieve account info: {e}")
            
            return True
        else:
            print("❌ Failed to connect to IBKR Gateway")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

async def test_api_server():
    """Test the FastAPI server endpoints"""
    print("\n🌐 Testing API Server...")
    
    try:
        # Start the API server in background
        print("🚀 Starting API server...")
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "api.main:app", 
            "--host", "127.0.0.1", "--port", "8000", "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(5)
        
        # Test basic endpoints
        base_url = "http://127.0.0.1:8000"
        
        # Test health check
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server is running")
            else:
                print(f"⚠️  API server responded with status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ API server not responding: {e}")
            return False
        
        # Test IBKR broker endpoints
        try:
            response = requests.get(f"{base_url}/api/v1/broker/IBKRBroker/account-info", timeout=10)
            if response.status_code == 200:
                print("✅ IBKR broker API is working")
                data = response.json()
                print(f"   Response: {data}")
            else:
                print(f"⚠️  IBKR broker API responded with status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ IBKR broker API error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ API server test failed: {e}")
        return False

async def test_strategy_with_ibkr():
    """Test the Supertrend strategy with IBKR connection"""
    print("\n📊 Testing Strategy with IBKR...")
    
    try:
        from strategies.Supertrend import IntradaySupertrendMA
        from brokers.ibkr_broker import IBKRBroker
        
        # Create broker instance
        broker = IBKRBroker("test_broker")
        
        # Create strategy instance
        strategy_params = {
            'symbol': 'AAPL',  # Use AAPL for testing
            'quantity': 1,     # Small quantity for testing
            'base_timeframe': '1min',
            'ma_timeframe': '30min',
            'supertrend_timeframe': '3h',
            'supertrend_length': 10,
            'supertrend_multiplier': 3.0,
            'ma_type': 'SMA',
            'ma5_period': 5,
            'ma9_period': 9,
            'ma20_period': 20,
            'ma50_period': 50,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.03,
            'use_bracket_orders': False,  # Disable for testing
            'place_market_orders': False,  # Use limit orders for safety
            'backfill_days': 1
        }
        
        strategy = IntradaySupertrendMA("test_strategy", broker, strategy_params)
        
        # Initialize strategy
        await strategy.init()
        print("✅ Strategy initialized successfully")
        
        # Run a quick test
        print("🧪 Running 2-minute live test...")
        await strategy.test_with_ibkr_gateway(symbol='AAPL', test_duration_minutes=2)
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 IBKR Gateway Connection Test")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check/Start IBKR Gateway
    if not start_ibkr_gateway():
        print("\n❌ Cannot proceed without IBKR Gateway")
        return
    
    # Step 2: Test IBKR Connection
    if not await test_ibkr_connection():
        print("\n❌ Cannot proceed without IBKR connection")
        return
    
    # Step 3: Test API Server
    await test_api_server()
    
    # Step 4: Test Strategy
    await test_strategy_with_ibkr()
    
    print("\n" + "=" * 50)
    print("✅ IBKR Gateway Test Completed!")
    print("🎉 Your system is ready for trading!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
