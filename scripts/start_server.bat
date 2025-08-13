@echo off
echo ========================================
echo TradeFlow AI: Starting FastAPI Server
echo ========================================
echo.

REM --- Kill process on port 8000 ---
echo --- Ensuring port 8000 is free ---
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo Found process %%a on port 8000. Attempting to kill...
    taskkill /F /PID %%a 2>nul
    if !errorlevel! equ 0 (
        echo Successfully killed process %%a
    ) else (
        echo Process %%a not found or already terminated
    )
)
echo Port 8000 should be free now.
echo.

REM --- Clear database locks ---
echo --- Step 1: Clearing database locks ---
if exist "scripts\clear_db_locks.bat" (
    call scripts\clear_db_locks.bat
) else (
    echo No clear_db_locks.bat found, skipping...
)
echo.

REM --- Start the server ---
echo --- Step 2: Starting the FastAPI server ---
echo Starting uvicorn with auto-reload...
echo Access the API at http://127.0.0.1:8000
echo Interactive docs at http://127.0.0.1:8000/docs
echo -------------------------------------------

REM Start the server
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

pause
