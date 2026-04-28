@echo off
title Metafore Works — Discovery Engine
color 0A
cls

echo.
echo  =======================================================
echo    Metafore Works ^| Discovery Engine
echo    Starting up, please wait...
echo  =======================================================
echo.

:: ── Step 1: Check Python ────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] Python is NOT installed on this computer.
    echo.
    echo      Please install Python first:
    echo      1. Go to  https://www.python.org/downloads/
    echo      2. Click the big yellow Download button
    echo      3. Run the installer
    echo      4. IMPORTANT: tick the box that says
    echo         "Add Python to PATH" before clicking Install
    echo      5. Once done, double-click START.bat again
    echo.
    echo  Opening the Python download page for you...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)
echo  [OK] Python is installed.
echo.

:: ── Step 2: Check config ────────────────────────────────────
if not exist "%~dp0discovery-engine\.env" (
    echo  [!] Missing configuration file.
    echo      Contact the person who sent you this project.
    pause
    exit /b 1
)
echo  [OK] Configuration found.
echo.

:: ── Step 3: Install packages ────────────────────────────────
echo  Installing required packages (1-2 min on first run)...
pip install -r "%~dp0discovery-engine\backend\requirements.txt" --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  [!] Installation failed. Try right-clicking START.bat
    echo      and choosing "Run as administrator".
    pause
    exit /b 1
)
echo  [OK] All packages ready.
echo.

:: ── Step 4: Stop any old instance ──────────────────────────
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8083 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: ── Step 5: Start server ────────────────────────────────────
echo  Starting server...
start "MetaforeWorks Discovery — Server" /min python -m uvicorn main:app --port 8083 --app-dir "%~dp0discovery-engine\backend"

:: ── Step 6: Open browser ────────────────────────────────────
echo  Waiting for server to start...
timeout /t 6 /nobreak >nul
echo  Opening browser...
start http://localhost:8083

echo.
echo  =======================================================
echo    Discovery Engine is RUNNING
echo.
echo    Your browser should open automatically.
echo    If not, go to:  http://localhost:8083
echo.
echo    To stop: run STOP.bat or close the small
echo    black window called "MetaforeWorks Discovery"
echo  =======================================================
echo.
pause
