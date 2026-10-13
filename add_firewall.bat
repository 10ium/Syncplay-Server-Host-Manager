@echo off
echo Adding firewall rule for Syncplay Server port 24680...
netsh advfirewall firewall add rule name="Syncplay Server 24680" dir=in action=allow protocol=TCP localport=24680
echo Done!
