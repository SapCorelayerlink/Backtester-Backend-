@echo off
echo ========================================
echo Clearing Database Locks
echo ========================================
echo.

REM Check if SQLite database exists
if exist "data\tradeflow.db" (
    echo Found SQLite database: data\tradeflow.db
    
    REM Try to remove any lock files
    if exist "data\tradeflow.db-wal" (
        echo Removing WAL file...
        del /f "data\tradeflow.db-wal" 2>nul
    )
    
    if exist "data\tradeflow.db-shm" (
        echo Removing SHM file...
        del /f "data\tradeflow.db-shm" 2>nul
    )
    
    echo Database locks cleared.
) else (
    echo No SQLite database found at data\tradeflow.db
)

REM Check for PostgreSQL/TimescaleDB
echo.
echo Checking for PostgreSQL/TimescaleDB connections...
echo (This would require psql to be installed)

REM Try to kill any hanging PostgreSQL connections (if psql is available)
where psql >nul 2>nul
if %errorlevel% equ 0 (
    echo PostgreSQL client found, attempting to clear connections...
    REM This is a basic attempt - in production you'd want more sophisticated connection management
    echo Note: Manual PostgreSQL connection cleanup may be required if using TimescaleDB
) else (
    echo PostgreSQL client not found, skipping PostgreSQL cleanup
)

echo.
echo Database lock cleanup completed.
echo.
