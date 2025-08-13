@echo off
title Bactester Trading System - Quick Start
color 0A

echo.
echo ======================================================================
echo 🚀 BACTESTER TRADING SYSTEM - QUICK START
echo ======================================================================
echo Advanced Trading Backtesting System with TimescaleDB
echo ======================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo ❌ requirements.txt not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

echo ✅ Python found
echo ✅ Running from correct directory
echo.

REM Run the quick start script
python quick_start.py

echo.
echo ======================================================================
echo Setup completed! Press any key to exit...
echo ======================================================================
pause >nul
