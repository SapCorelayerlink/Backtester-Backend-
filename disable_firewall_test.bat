@echo off
echo Temporarily Disabling Windows Firewall for IBKR Testing...
echo.
echo WARNING: This will disable Windows Firewall temporarily
echo This is for testing purposes only!
echo.

REM Run as administrator check
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Disabling Windows Firewall...
netsh advfirewall set allprofiles state off
if %errorLevel% equ 0 (
    echo ✅ Windows Firewall disabled successfully
    echo.
    echo Now test your IBKR connection:
    echo python quick_ibkr_test.py
    echo.
    echo IMPORTANT: Remember to re-enable firewall after testing!
    echo To re-enable: netsh advfirewall set allprofiles state on
    echo.
) else (
    echo ❌ Failed to disable Windows Firewall
)

pause
