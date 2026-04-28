@echo off
title Metafore One — Stopping Discovery Engine
echo.
echo  Stopping the Discovery Engine server...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8083 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo  [OK] Server stopped.
echo.
timeout /t 2 /nobreak >nul
