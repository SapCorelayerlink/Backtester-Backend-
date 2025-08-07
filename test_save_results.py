#!/usr/bin/env python3
"""
Test script to verify backtest results saving.
"""

import sys
import os
import asyncio

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_save_results():
    """Test the backtest results saving process."""
    try:
        print("🧪 Testing Backtest Results Saving...")
        
        # Import required modules
        from brokers.mock_broker import MockBroker
        from strategies.macrossover_strategy import MACrossover
        
        # Create broker and strategy
        broker = MockBroker(name="test_broker")
        strategy = MACrossover(
            name="test_strategy",
            broker=broker,
            params={
                'symbol': 'GOOG',
                'timeframe': '1 day',
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'initial_capital': 10000,
                'stop_loss_pct': 0.05
            }
        )
        
        print("✓ Step 1: Created strategy instance")
        
        # Run the strategy
        print("✓ Step 2: Running strategy...")
        run_id = await strategy.run()
        
        if run_id:
            print(f"✅ Strategy completed with run_id: {run_id}")
            
            # Check if file was created
            results_file = f"backtest_results/{run_id}.json"
            if os.path.exists(results_file):
                print(f"✅ Results file created: {results_file}")
                
                # Read and display file info
                import json
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
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
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoint():
    """Test the API endpoint for listing results."""
    try:
        print("\n🌐 Testing API Results Endpoint...")
        
        # Import the API app
        from api.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/api/v1/strategies/results")
        
        print(f"✅ API response status: {response.status_code}")
        data = response.json()
        print(f"✅ Available run IDs: {data.get('run_ids', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Results Saving Test...\n")
    
    # Test 1: Save results
    save_success = await test_save_results()
    
    # Test 2: API endpoint
    api_success = await test_api_endpoint()
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS:")
    print(f"   Save Results: {'✅ PASS' if save_success else '❌ FAIL'}")
    print(f"   API Endpoint: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if save_success and api_success:
        print("\n🎉 Results saving is working correctly!")
    else:
        print("\n⚠️  There are issues with results saving.")

if __name__ == "__main__":
    asyncio.run(main()) 