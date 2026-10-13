@echo off
echo Removing firewall rule for Syncplay Server port 24680...
netsh advfirewall firewall delete rule name="Syncplay Server 24680"
echo Done!
