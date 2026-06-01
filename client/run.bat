@echo off
cd /d "%~dp0"
echo Starting Pharmacy System Client...
echo Using Python environment: venv\Scripts\python.exe
venv\Scripts\python.exe main.py
if %errorlevel% neq 0 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)
