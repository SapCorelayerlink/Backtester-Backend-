#!/usr/bin/env python3
"""
Test script to test all available strategies one by one.
"""

import asyncio
import sys
import os
import traceback
from datetime import datetime, timedelta

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_strategy(strategy_name: str, strategy_class):
    """Test a single strategy."""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING STRATEGY: {strategy_name}")
    print(f"{'='*60}")
    
    try:
        # Import necessary modules
        from core.registry import StrategyRegistry, BrokerRegistry
        from brokers.paper_broker import PaperBroker
        from data.polygon_data import PolygonDataProvider
        
        # Test 1: Strategy Registration
        print(f"✓ Step 1: Checking strategy registration...")
        if strategy_name in StrategyRegistry.list():
            print(f"  ✓ Strategy '{strategy_name}' is registered")
        else:
            print(f"  ✗ Strategy '{strategy_name}' is NOT registered")
            return False
        
        # Test 2: Strategy Class Creation
        print(f"✓ Step 2: Testing strategy class creation...")
        try:
            # Create a paper broker for testing
            broker = PaperBroker("test_paper_broker", {'starting_cash': 10000})
            await broker.connect()
            
            # Create strategy instance
            strategy = strategy_class(
                name=f"test_{strategy_name}",
                broker=broker,
                params={
                    'symbol': 'AAPL',
                    'timeframe': '1d',
                    'quantity': 100,
                    'initial_capital': 10000
                }
            )
            print(f"  ✓ Strategy instance created successfully")
        except Exception as e:
            print(f"  ✗ Failed to create strategy instance: {e}")
            return False
        
        # Test 3: Strategy Initialization
        print(f"✓ Step 3: Testing strategy initialization...")
        try:
            await strategy.init()
            print(f"  ✓ Strategy initialized successfully")
        except Exception as e:
            print(f"  ✗ Strategy initialization failed: {e}")
            return False
        
        # Test 4: Strategy on_bar method
        print(f"✓ Step 4: Testing strategy on_bar method...")
        try:
            import pandas as pd
            
            # Create sample bar data
            sample_bar = pd.Series({
                'open': 150.0,
                'high': 152.0,
                'low': 149.0,
                'close': 151.0,
                'volume': 1000000,
                'timestamp': datetime.now()
            })
            
            await strategy.on_bar(sample_bar)
            print(f"  ✓ Strategy on_bar method executed successfully")
        except Exception as e:
            print(f"  ✗ Strategy on_bar method failed: {e}")
            return False
        
        # Test 5: Strategy Parameters
        print(f"✓ Step 5: Checking strategy parameters...")
        try:
            params = strategy.params
            print(f"  ✓ Strategy parameters: {params}")
        except Exception as e:
            print(f"  ✗ Failed to access strategy parameters: {e}")
            return False
        
        print(f"✅ STRATEGY '{strategy_name}' PASSED ALL TESTS!")
        return True
        
    except Exception as e:
        print(f"❌ STRATEGY '{strategy_name}' FAILED: {e}")
        traceback.print_exc()
        return False

async def test_all_strategies():
    """Test all available strategies."""
    print("🚀 STARTING COMPREHENSIVE STRATEGY TESTING")
    print(f"Timestamp: {datetime.now()}")
    
    # List of strategies to test (with their import paths)
    strategies_to_test = [
        ("SampleStrategy", "strategies.sample_strategy"),
        ("MACrossover", "strategies.macrossover_strategy"),
        ("SimplePaperStrategy", "strategies.simple_paper_strategy"),
        ("RSIVWAPStrategy", "strategies.RSI+VWAP"),
        ("TurtleStrategy", "strategies.Turtle"),
        ("SwingFailureStrategy", "strategies.SwingFailure"),
        ("BB5EMAStrategy", "strategies.Bollinger + 5EMA"),
        ("IntradaySupertrendMA", "strategies.Supertrend"),
        ("SRTrend4H", "strategies.Support Resiatance "),
        ("IntradaySupertrendMA", "strategies.intraday_supertrend_ma_strategy"),
    ]
    
    results = {}
    passed = 0
    failed = 0
    
    for strategy_name, import_path in strategies_to_test:
        try:
            # Import the strategy module
            module = __import__(import_path, fromlist=[strategy_name])
            strategy_class = getattr(module, strategy_name)
            
            # Test the strategy
            success = await test_strategy(strategy_name, strategy_class)
            results[strategy_name] = success
            
            if success:
                passed += 1
            else:
                failed += 1
                
        except ImportError as e:
            print(f"\n❌ FAILED TO IMPORT {strategy_name}: {e}")
            results[strategy_name] = False
            failed += 1
        except AttributeError as e:
            print(f"\n❌ FAILED TO GET STRATEGY CLASS {strategy_name}: {e}")
            results[strategy_name] = False
            failed += 1
        except Exception as e:
            print(f"\n❌ UNEXPECTED ERROR WITH {strategy_name}: {e}")
            results[strategy_name] = False
            failed += 1
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"📊 TESTING SUMMARY")
    print(f"{'='*80}")
    print(f"Total strategies tested: {len(strategies_to_test)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed/len(strategies_to_test)*100):.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for strategy_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {strategy_name}: {status}")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    if failed > 0:
        print(f"  - {failed} strategies need attention")
        print(f"  - Check import statements and dependencies")
        print(f"  - Verify strategy class names match registration")
    else:
        print(f"  - All strategies are working correctly!")
        print(f"  - Ready for production use")
    
    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(test_all_strategies())
        sys.exit(0 if all(results.values()) else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        traceback.print_exc()
        sys.exit(1)
