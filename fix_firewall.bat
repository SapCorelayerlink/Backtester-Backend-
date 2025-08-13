@echo off
echo Configuring Windows Firewall for IBKR Gateway...
echo.

REM Run as administrator check
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Adding IBKR Gateway to Windows Firewall...
echo.

REM Add inbound rule for IBKR Gateway
echo Creating inbound rule for IBKR Gateway...
netsh advfirewall firewall add rule name="IBKR Gateway Inbound" dir=in action=allow program="C:\Program Files\IBKR\TWS\ibgateway\ibgateway.exe" enable=yes
if %errorLevel% equ 0 (
    echo ✅ Inbound rule created successfully
) else (
    echo ⚠️  Could not create inbound rule (Gateway might be in different location)
)

REM Add outbound rule for IBKR Gateway
echo Creating outbound rule for IBKR Gateway...
netsh advfirewall firewall add rule name="IBKR Gateway Outbound" dir=out action=allow program="C:\Program Files\IBKR\TWS\ibgateway\ibgateway.exe" enable=yes
if %errorLevel% equ 0 (
    echo ✅ Outbound rule created successfully
) else (
    echo ⚠️  Could not create outbound rule (Gateway might be in different location)
)

REM Add port rule for port 4001
echo Creating port rule for port 4001...
netsh advfirewall firewall add rule name="IBKR Gateway Port 4001" dir=in action=allow protocol=TCP localport=4001 enable=yes
if %errorLevel% equ 0 (
    echo ✅ Port 4001 rule created successfully
) else (
    echo ❌ Failed to create port rule
)

echo.
echo Firewall configuration completed!
echo.
echo Next steps:
echo 1. Restart IBKR Gateway
echo 2. Run: python quick_ibkr_test.py
echo.
pause
