#!/usr/bin/env python3
"""
Quick Start Script for Bactester Trading System
Automates the setup and provides easy access to common operations
"""

import os
import sys
import subprocess
import time
import platform
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    print("=" * 70)
    print("🚀 BACTESTER TRADING SYSTEM - QUICK START")
    print("=" * 70)
    print("Advanced Trading Backtesting System with TimescaleDB")
    print("=" * 70)

def check_prerequisites():
    """Check if required software is installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if Docker is available
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is available")
        else:
            print("❌ Docker not found. Please install Docker Desktop")
            return False
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker Desktop")
        return False
    
    # Check if docker-compose is available
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker Compose is available")
        else:
            print("❌ Docker Compose not found")
            return False
    except FileNotFoundError:
        print("❌ Docker Compose not found")
        return False
    
    return True

def install_python_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        return False

def start_database():
    """Start TimescaleDB using Docker"""
    print("\n🗄️  Starting TimescaleDB database...")
    
    try:
        # Navigate to config directory
        config_dir = Path("config")
        if not config_dir.exists():
            print("❌ Config directory not found")
            return False
        
        # Start TimescaleDB
        result = subprocess.run([
            'docker-compose', '-f', 'docker-compose.timescaledb.yml', 'up', '-d'
        ], cwd=config_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ TimescaleDB started successfully")
            
            # Wait a moment for database to be ready
            print("⏳ Waiting for database to be ready...")
            time.sleep(5)
            
            return True
        else:
            print(f"❌ Failed to start TimescaleDB: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting database: {e}")
        return False

def reset_database():
    """Reset database with correct schema"""
    print("\n🔄 Resetting database schema...")
    
    try:
        result = subprocess.run([sys.executable, 'reset_database.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database reset successfully")
            return True
        else:
            print(f"❌ Database reset failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

def test_system():
    """Run basic system tests"""
    print("\n🧪 Running system tests...")
    
    tests = [
        ("Database Connection", "from data.backtest_database import BacktestDatabase; db = BacktestDatabase(); print('Database OK')"),
        ("RSI Strategy", "from strategies.rsi_vwap_strategy import RSI_VWAPStrategy; print('RSI Strategy OK')"),
        ("Turtle Strategy", "from strategies.Turtle import TurtleStrategy; print('Turtle Strategy OK')"),
        ("Paper Broker", "from brokers.paper_broker import PaperBroker; print('Paper Broker OK')")
    ]
    
    all_passed = True
    for test_name, test_code in tests:
        try:
            result = subprocess.run([sys.executable, '-c', test_code], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {test_name}: OK")
            else:
                print(f"❌ {test_name}: Failed - {result.stderr}")
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name}: Error - {e}")
            all_passed = False
    
    return all_passed

def show_menu():
    """Show interactive menu"""
    while True:
        print("\n" + "=" * 50)
        print("🎯 BACTESTER QUICK START MENU")
        print("=" * 50)
        print("1. 🚀 Complete Setup (Install + Database + Test)")
        print("2. 📦 Install Python Dependencies Only")
        print("3. 🗄️  Start Database Only")
        print("4. 🔄 Reset Database Schema")
        print("5. 🧪 Run System Tests")
        print("6. 🎮 Test RSI + VWAP Strategy")
        print("7. 🐢 Test Turtle Strategy")
        print("8. 📊 View Database Data")
        print("9. 🌐 Start API Server")
        print("10. 📱 Start Frontend (if Node.js installed)")
        print("0. ❌ Exit")
        
        choice = input("\nEnter your choice (0-10): ").strip()
        
        if choice == '0':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            run_complete_setup()
        elif choice == '2':
            install_python_dependencies()
        elif choice == '3':
            start_database()
        elif choice == '4':
            reset_database()
        elif choice == '5':
            test_system()
        elif choice == '6':
            run_strategy_test('test_scripts\\test_rsi_vwap_simple.py')
        elif choice == '7':
            run_strategy_test('test_scripts\\test_turtle_strategy.py')
        elif choice == '8':
            run_database_viewer()
        elif choice == '9':
            start_api_server()
        elif choice == '10':
            start_frontend()
        else:
            print("❌ Invalid choice. Please try again.")

def run_complete_setup():
    """Run complete setup process"""
    print("\n🚀 Starting complete setup...")
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites check failed. Please install required software.")
        return
    
    # Install dependencies
    if not install_python_dependencies():
        print("❌ Failed to install dependencies.")
        return
    
    # Start database
    if not start_database():
        print("❌ Failed to start database.")
        return
    
    # Reset database
    if not reset_database():
        print("❌ Failed to reset database.")
        return
    
    # Test system
    if not test_system():
        print("❌ System tests failed.")
        return
    
    print("\n🎉 Complete setup finished successfully!")
    print("You can now:")
    print("  - Run strategies: python test_scripts\\test_rsi_vwap_simple.py")
    print("  - Start API server: python -m api.main")
    print("  - View database: python utility_scripts\\view_database_data.py")

def run_strategy_test(script_name):
    """Run a strategy test script"""
    print(f"\n🎮 Running {script_name}...")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {script_name} completed successfully")
            print("Output:")
            print(result.stdout)
        else:
            print(f"❌ {script_name} failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")

def run_database_viewer():
    """Run database viewer"""
    print("\n📊 Starting database viewer...")
    
    try:
        subprocess.run([sys.executable, 'utility_scripts\\view_database_data.py'])
    except Exception as e:
        print(f"❌ Error running database viewer: {e}")

def start_api_server():
    """Start the FastAPI server"""
    print("\n🌐 Starting API server...")
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([sys.executable, '-m', 'api.main'])
    except KeyboardInterrupt:
        print("\n👋 API server stopped")
    except Exception as e:
        print(f"❌ Error starting API server: {e}")

def start_frontend():
    """Start the frontend development server"""
    print("\n📱 Starting frontend development server...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return
    
    try:
        # Check if Node.js is installed
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Node.js not found. Please install Node.js 18+")
            return
        
        print("✅ Node.js found")
        
        # Install dependencies if needed
        if not (frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
        
        print("🚀 Starting frontend development server...")
        print("Frontend will be available at: http://localhost:5173")
        print("Press Ctrl+C to stop the server")
        
        subprocess.run(['npm', 'run', 'dev'], cwd=frontend_dir)
        
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")

def main():
    """Main function"""
    print_banner()
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found. Please run this script from the project root directory.")
        return
    
    # Show menu
    show_menu()

if __name__ == "__main__":
    main()
