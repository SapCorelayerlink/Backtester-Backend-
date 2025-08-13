#!/usr/bin/env python3
"""
IBKR Gateway Diagnostic Script
==============================

This script helps diagnose common IBKR Gateway connection issues.
"""

import asyncio
import sys
import os
import socket
import subprocess
import time

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_system_info():
    """Check basic system information"""
    print("🔍 System Information")
    print("=" * 30)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check if required packages are installed
    try:
        import ib_insync
        print(f"✅ ib_insync version: {ib_insync.__version__}")
    except ImportError:
        print("❌ ib_insync not installed")
        return False
    
    try:
        import pandas
        print(f"✅ pandas version: {pandas.__version__}")
    except ImportError:
        print("❌ pandas not installed")
        return False
    
    return True

def check_network():
    """Check network connectivity"""
    print("\n🌐 Network Connectivity")
    print("=" * 30)
    
    # Check localhost connectivity
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 4001))
        sock.close()
        
        if result == 0:
            print("✅ Port 4001 is accessible")
        else:
            print(f"❌ Port 4001 is not accessible (error: {result})")
            return False
    except Exception as e:
        print(f"❌ Network check failed: {e}")
        return False
    
    # Check if anything is listening on port 4001
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
        if '4001' in result.stdout:
            print("✅ Port 4001 is being listened on")
        else:
            print("❌ Nothing listening on port 4001")
            return False
    except Exception as e:
        print(f"⚠️  Could not check netstat: {e}")
    
    return True

def check_ibkr_gateway_process():
    """Check if IBKR Gateway process is running"""
    print("\n🔍 IBKR Gateway Process")
    print("=" * 30)
    
    try:
        # Check for IBKR Gateway processes
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ibgateway.exe'], 
                              capture_output=True, text=True)
        
        if 'ibgateway.exe' in result.stdout:
            print("✅ IBKR Gateway process is running")
            return True
        else:
            print("❌ IBKR Gateway process not found")
            return False
    except Exception as e:
        print(f"⚠️  Could not check processes: {e}")
        return False

async def test_basic_connection():
    """Test basic connection without authentication"""
    print("\n🔌 Basic Connection Test")
    print("=" * 30)
    
    try:
        from ib_insync import IB
        
        # Create a new IB instance for testing
        ib = IB()
        
        print("   🔌 Attempting basic connection...")
        
        # Try to connect with a simple timeout
        await asyncio.wait_for(
            ib.connectAsync('127.0.0.1', 4001, clientId=1),
            timeout=10.0
        )
        
        if ib.isConnected():
            print("   ✅ Basic connection successful!")
            ib.disconnect()
            return True
        else:
            print("   ❌ Basic connection failed")
            return False
            
    except asyncio.TimeoutError:
        print("   ⏰ Connection timed out")
        return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def check_common_issues():
    """Check for common configuration issues"""
    print("\n🔧 Common Issues Check")
    print("=" * 30)
    
    issues_found = []
    
    # Check Windows Firewall
    print("1. Checking Windows Firewall...")
    try:
        result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'], 
                              capture_output=True, text=True)
        if 'Domain' in result.stdout or 'Private' in result.stdout or 'Public' in result.stdout:
            print("   ⚠️  Windows Firewall is active - may block connections")
            issues_found.append("Windows Firewall may be blocking connections")
        else:
            print("   ✅ Windows Firewall appears to be disabled")
    except Exception as e:
        print(f"   ⚠️  Could not check firewall: {e}")
    
    # Check for antivirus
    print("2. Checking for antivirus interference...")
    try:
        result = subprocess.run(['wmic', 'product', 'where', 'name like "%antivirus%"', 'get', 'name'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print("   ⚠️  Antivirus software detected - may interfere with connections")
            issues_found.append("Antivirus software may be blocking connections")
        else:
            print("   ✅ No obvious antivirus interference")
    except Exception as e:
        print(f"   ⚠️  Could not check for antivirus: {e}")
    
    return issues_found

def provide_recommendations(issues):
    """Provide recommendations based on findings"""
    print("\n💡 Recommendations")
    print("=" * 30)
    
    if not issues:
        print("✅ No obvious issues detected")
        print("💡 Try these steps:")
        print("   1. Restart IBKR Gateway")
        print("   2. Check IBKR Gateway API settings")
        print("   3. Verify your IBKR account has API access enabled")
        print("   4. Try connecting with a different client ID")
    else:
        print("⚠️  Potential issues detected:")
        for issue in issues:
            print(f"   - {issue}")
        
        print("\n🔧 Suggested fixes:")
        print("   1. Add IBKR Gateway to Windows Firewall exceptions")
        print("   2. Temporarily disable antivirus for testing")
        print("   3. Check IBKR Gateway API configuration:")
        print("      - Enable 'ActiveX and Socket Clients'")
        print("      - Set Socket port to 4001")
        print("      - Enable 'Allow connections from localhost'")
        print("   4. Restart IBKR Gateway after configuration changes")

async def main():
    """Main diagnostic function"""
    print("🚀 IBKR Gateway Diagnostic Tool")
    print("=" * 50)
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all checks
    checks_passed = 0
    total_checks = 4
    
    # Check 1: System info
    if check_system_info():
        checks_passed += 1
    
    # Check 2: Network
    if check_network():
        checks_passed += 1
    
    # Check 3: Process
    if check_ibkr_gateway_process():
        checks_passed += 1
    
    # Check 4: Basic connection
    if await test_basic_connection():
        checks_passed += 1
    
    # Check for common issues
    issues = check_common_issues()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Diagnostic Summary")
    print("=" * 50)
    print(f"✅ Checks passed: {checks_passed}/{total_checks}")
    
    if checks_passed == total_checks:
        print("🎉 All basic checks passed!")
        print("💡 The issue might be with authentication or API configuration")
    else:
        print("❌ Some checks failed")
        print("💡 Please address the issues above")
    
    # Provide recommendations
    provide_recommendations(issues)
    
    print("\n" + "=" * 50)
    print("🔗 Next Steps:")
    print("1. Fix any issues identified above")
    print("2. Restart IBKR Gateway")
    print("3. Run: python quick_ibkr_test.py")
    print("4. If still having issues, check IBKR Gateway logs")

if __name__ == "__main__":
    asyncio.run(main())
