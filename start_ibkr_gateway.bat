@echo off
echo Starting IBKR Gateway...
echo.

REM Try common IBKR Gateway installation paths
set "GATEWAY_PATHS=C:\Program Files\IBKR\TWS\ibgateway\start.bat;C:\Program Files (x86)\IBKR\TWS\ibgateway\start.bat"

for %%p in (%GATEWAY_PATHS%) do (
    if exist "%%p" (
        echo Found IBKR Gateway at: %%p
        echo Starting IBKR Gateway...
        start "" "%%p"
        echo.
        echo IBKR Gateway started successfully!
        echo Please wait a few moments for it to fully load.
        echo.
        echo You can now run: python quick_ibkr_test.py
        pause
        exit /b 0
    )
)

echo.
echo IBKR Gateway not found in common locations.
echo.
echo Please install IBKR Gateway from:
echo https://www.interactivebrokers.com/en/trading/ib-api.php
echo.
echo Or manually start IBKR Gateway and configure it to:
echo - Listen on port 4001
echo - Allow API connections
echo - Accept connections from localhost
echo.
pause
