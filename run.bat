@echo off
echo ============================================================
echo   Academic Performance Prediction System
echo   Starting server...
echo ============================================================
echo.

cd /d "%~dp0backend\python"

echo   Opening browser...
start "" http://127.0.0.1:5000

python app.py

pause
