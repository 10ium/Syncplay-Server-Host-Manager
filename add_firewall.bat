@echo off
setlocal
set PORT=8999
if not "%1"=="" set PORT=%1

echo ========================================================
echo   Adding Windows Firewall Inbound Rule for Syncplay
echo   Port: %PORT% (TCP)
echo ========================================================

netsh advfirewall firewall add rule name="Syncplay Server %PORT%" dir=in action=allow protocol=TCP localport=%PORT%
echo.
echo Firewall rule "Syncplay Server %PORT%" added successfully!
pause
