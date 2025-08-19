#!/usr/bin/env python3
"""
Setup script for Polygon.io integration.
Helps users configure their API key and test the connection.
"""

import os
import sys
import asyncio
from pathlib import Path

def setup_api_key():
    """Interactive setup for Polygon.io API key."""
    print("="*60)
    print("POLYGON.IO API KEY SETUP")
    print("="*60)
    
    print("\nTo use the Polygon.io integration, you need an API key.")
    print("1. Sign up at https://polygon.io")
    print("2. Get your API key from the dashboard")
    print("3. Enter it below\n")
    
    # Check if API key already exists
    current_key = os.getenv("POLYGON_API_KEY", "")
    if current_key and current_key != "YOUR_API_KEY":
        print(f"Current API key: {current_key[:10]}...")
        change = input("Do you want to change it? (y/N): ").lower().strip()
        if change != 'y':
            return current_key
    
    # Get new API key
    while True:
        api_key = input("Enter your Polygon.io API key: ").strip()
        
        if not api_key:
            print("API key cannot be empty. Please try again.")
            continue
        
        if len(api_key) < 10:
            print("API key seems too short. Please check and try again.")
            continue
        
        # Confirm
        confirm = input(f"Confirm API key: {api_key[:10]}... (y/N): ").lower().strip()
        if confirm == 'y':
            break
    
    # Save to environment file
    save_to_env = input("\nSave API key to .env file? (Y/n): ").lower().strip()
    if save_to_env != 'n':
        env_file = Path(".env")
        env_content = f"POLYGON_API_KEY={api_key}\n"
        
        if env_file.exists():
            # Read existing content
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Replace existing key or add new one
            if "POLYGON_API_KEY=" in content:
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith("POLYGON_API_KEY="):
                        new_lines.append(f"POLYGON_API_KEY={api_key}")
                    else:
                        new_lines.append(line)
                env_content = '\n'.join(new_lines) + '\n'
            else:
                env_content = content + env_content
        else:
            env_content = f"# Polygon API Configuration\nPOLYGON_API_KEY={api_key}\n\n# Paper Trading Configuration\nPAPER_MODE=True\nPAPER_STARTING_CASH=100000\n\n# Database Configuration (Optional - uncomment and configure if using PostgreSQL)\n# PG_HOST=localhost\n# PG_PORT=5432\n# PG_DB=bactester\n# PG_USER=postgres\n# PG_PASSWORD=your_password\n# PG_SSLMODE=prefer\n\n# WebSocket Configuration\nWEBSOCKET_HOST=localhost\nWEBSOCKET_PORT=8765\n\n# Trading Configuration\nDEFAULT_COMMISSION=0.0\nDEFAULT_SLIPPAGE=0.0\n\n# Logging Configuration\nLOG_LEVEL=INFO\nLOG_FILE=paper_trader.log\n"
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✓ API key saved to {env_file}")
    
    # Set environment variable for current session
    os.environ["POLYGON_API_KEY"] = api_key
    
    print(f"\n✓ API key configured: {api_key[:10]}...")
    return api_key

async def test_connection(api_key):
    """Test the Polygon.io connection."""
    print("\n" + "="*60)
    print("TESTING CONNECTION")
    print("="*60)
    
    try:
        # Import after setting API key
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from data.polygon_data import polygon_data
        
        print("Testing API connection...")
        
        # Test real-time price
        price = await polygon_data.get_real_time_price('AAPL')
        if price:
            print(f"✓ Connection successful! AAPL price: ${price:.2f}")
        else:
            print("⚠ Connection successful but no price data available (may be outside market hours)")
        
        # Test historical data
        from datetime import datetime, timedelta
        df = await polygon_data.get_historical_bars(
            symbol='AAPL',
            from_date=datetime.now() - timedelta(days=7),
            to_date=datetime.now(),
            interval='1D'
        )
        
        if not df.empty:
            print(f"✓ Historical data working! Retrieved {len(df)} bars")
        else:
            print("⚠ Historical data test failed - check your plan permissions")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def show_next_steps():
    """Show next steps for the user."""
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    
    print("\n1. Test the integration:")
    print("   python examples/test_polygon_integration.py")
    
    print("\n2. Run paper trading:")
    print("   python paper_trader.py --symbols AAPL MSFT --strategy simple_paper_strategy")
    
    print("\n3. View documentation:")
    print("   docs/POLYGON_INTEGRATION.md")
    
    print("\n4. Check available strategies:")
    print("   ls strategies/")
    
    print("\n5. Monitor logs:")
    print("   tail -f paper_trader.log")

async def main():
    """Main setup function."""
    try:
        # Setup API key
        api_key = setup_api_key()
        
        # Test connection
        success = await test_connection(api_key)
        
        if success:
            show_next_steps()
            print("\n✓ Setup completed successfully!")
        else:
            print("\n✗ Setup failed. Please check your API key and try again.")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nError during setup: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
