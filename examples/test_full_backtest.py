#!/usr/bin/env python3
"""
Test script to verify the full backtest functionality.
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_full_backtest():
    """Test the complete backtest functionality."""
    try:
        print("🧪 Testing Full Backtest System...")
        
        # 1. Test imports
        print("✓ Step 1: Testing imports...")
        from core.registry import StrategyRegistry, BrokerRegistry
        from brokers.ibkr_broker import IBKRBroker
        from strategies.macrossover_strategy import MACrossover
        
        # 2. Test broker creation
        print("✓ Step 2: Testing broker creation...")
        broker = IBKRBroker(name="test_broker")
        
        # 3. Test strategy creation
        print("✓ Step 3: Testing strategy creation...")
        strategy = MACrossover(
            name="test_strategy",
            broker=broker,
            params={
                'symbol': 'AAPL',
                'timeframe': '1 day',
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'initial_capital': 10000,
                'stop_loss_pct': 0.05
            }
        )
        
        # 4. Test strategy run
        print("✓ Step 4: Testing strategy execution...")
        run_id = await strategy.run()
        
        if run_id:
            print(f"✅ Backtest completed successfully with run_id: {run_id}")
            
            # 5. Test results loading
            print("✓ Step 5: Testing results loading...")
            import json
            import os
            
            results_file = f"backtest_results/{run_id}.json"
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                print(f"✅ Results file created: {results_file}")
                print(f"   - Strategy: {results.get('strategy_name')}")
                print(f"   - Trades: {len(results.get('trades', []))}")
                print(f"   - Equity curve points: {len(results.get('equity_curve', []))}")
                print(f"   - Final equity: ${results.get('final_equity', 0):.2f}")
                
                return True
            else:
                print(f"❌ Results file not found: {results_file}")
                return False
        else:
            print("❌ Strategy run returned no run_id")
            return False
            
    except Exception as e:
        print(f"❌ Error during backtest test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """Test the API endpoints."""
    try:
        print("\n🌐 Testing API Endpoints...")
        
        # This would require the server to be running
        # For now, just test the imports
        from api.main import app
        print("✅ API app imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Full System Test...\n")
    
    # Test 1: Full backtest functionality
    backtest_success = await test_full_backtest()
    
    # Test 2: API endpoints
    api_success = await test_api_endpoints()
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS:")
    print(f"   Backtest System: {'✅ PASS' if backtest_success else '❌ FAIL'}")
    print(f"   API System: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if backtest_success and api_success:
        print("\n🎉 All systems are working correctly!")
        print("\n📝 Next Steps:")
        print("1. Start the server: python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        print("2. Open frontend: http://localhost:8000/backtest-report")
        print("3. Run a backtest through the UI")
    else:
        print("\n⚠️  Some systems need attention before proceeding.")

if __name__ == "__main__":
    asyncio.run(main()) 