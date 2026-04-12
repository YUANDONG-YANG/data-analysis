@echo off
chcp 65001 >nul
cls
echo ========================================
echo   Documentation Server Launcher
echo ========================================
echo.

REM Check if markdown is installed
python -c "import markdown" 2>nul
if errorlevel 1 (
    echo [WARNING] markdown library not installed, installing...
    pip install markdown>=3.4.0
    echo.
)

echo [INFO] Starting server...
echo [INFO] After server starts, open: http://localhost:8081/ (pipeline tour + architecture index)
echo [TIP] Press Ctrl+C to stop server
echo.
echo ========================================
echo.

python docs_server.py

echo.
echo ========================================
echo Server stopped
pause
