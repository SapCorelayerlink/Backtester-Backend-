#!/bin/bash

# Bactester Trading System - Quick Start Script
# For macOS and Linux users

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "======================================================================"
echo "🚀 BACTESTER TRADING SYSTEM - QUICK START"
echo "======================================================================"
echo "Advanced Trading Backtesting System with TimescaleDB"
echo "======================================================================"
echo -e "${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found. Please run this script from the project root directory.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python found${NC}"
echo -e "${GREEN}✅ Running from correct directory${NC}"
echo

# Make the script executable
chmod +x setup_guide/quick_start.py

# Run the quick start script
python3 setup_guide/quick_start.py

echo
echo -e "${BLUE}======================================================================"
echo "Setup completed!"
echo "======================================================================"
echo -e "${NC}"
