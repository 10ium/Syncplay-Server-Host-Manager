@echo off
setlocal
set PORT=8999
if not "%1"=="" set PORT=%1

echo ========================================================
echo   Removing Windows Firewall Inbound Rule for Syncplay
echo   Port: %PORT% (TCP)
echo ========================================================

netsh advfirewall firewall delete rule name="Syncplay Server %PORT%"
echo.
echo Firewall rule "Syncplay Server %PORT%" removed.
pause
