#!/usr/bin/env python3
"""
Test script to check for import errors in the main application.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all the imports used in the main application."""
    try:
        print("Testing imports...")
        
        # Test core imports
        print("✓ Testing core imports...")
        from core.registry import StrategyRegistry, BrokerRegistry
        from core.base import BrokerBase
        
        # Test broker imports
        print("✓ Testing broker imports...")
        from brokers.ibkr_manager import ibkr_manager
        from brokers import ibkr_broker, mock_broker
        
        # Test strategy imports
        print("✓ Testing strategy imports...")
        from strategies import macrossover_strategy, sample_strategy
        
        # Test data manager
        print("✓ Testing data manager...")
        from data.data_manager import DataManager
        
        # Test FastAPI and other dependencies
        print("✓ Testing FastAPI imports...")
        from fastapi import FastAPI, APIRouter, HTTPException
        from pydantic import BaseModel
        import pandas as pd
        import numpy as np
        
        print("✓ All imports successful!")
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n🎉 All imports are working correctly!")
    else:
        print("\n❌ There are import errors that need to be fixed.") 