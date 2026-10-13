@echo off
setlocal
set PORT=8999
if not "%1"=="" set PORT=%1

echo ========================================================
echo   Starting Syncplay Server
echo   Port: %PORT% (TCP)
echo ========================================================

if exist "%ProgramFiles(x86)%\Syncplay\syncplayServer.exe" (
    "%ProgramFiles(x86)%\Syncplay\syncplayServer.exe" --port %PORT%
) else if exist "%ProgramFiles%\Syncplay\syncplayServer.exe" (
    "%ProgramFiles%\Syncplay\syncplayServer.exe" --port %PORT%
) else (
    echo [ERROR] syncplayServer.exe was not found in Program Files.
    echo Please make sure Syncplay is installed from https://syncplay.pl
    pause
)
