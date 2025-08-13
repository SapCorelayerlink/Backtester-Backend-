@echo off
echo Re-enabling Windows Firewall...
echo.

REM Run as administrator check
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Enabling Windows Firewall...
netsh advfirewall set allprofiles state on
if %errorLevel% equ 0 (
    echo ✅ Windows Firewall enabled successfully
    echo.
    echo Your system is now protected again.
    echo.
) else (
    echo ❌ Failed to enable Windows Firewall
)

pause
