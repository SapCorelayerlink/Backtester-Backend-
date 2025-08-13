@echo off
echo ========================================
echo Stock Screener Project Setup
echo ========================================
echo.

echo This script will set up both frontend and backend components.
echo Make sure you have Python, Node.js, and Ollama installed.
echo.
pause

cd /d "%~dp0"

echo Step 1: Setting up Python Backend...
echo ========================================
cd backend
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo Installing Python requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python requirements
    pause
    exit /b 1
)

cd ..

echo.
echo Step 2: Setting up Node.js Frontend...
echo ========================================
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js
    pause
    exit /b 1
)

echo Installing Node.js dependencies...
npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies
    pause
    exit /b 1
)

echo.
echo Step 3: Checking Ollama Setup...
echo ========================================
echo Make sure Ollama is installed and running:
echo   1. Install Ollama from https://ollama.ai
echo   2. Run: ollama serve
echo   3. Run: ollama pull qwen
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application:
echo   1. Backend: cd backend ^&^& python start_server.py
echo   2. Frontend: npm run dev
echo.
echo The backend will run on: http://localhost:5000
echo The frontend will run on: http://localhost:5173
echo.
pause
