@echo off
cd /d "%~dp0"
if exist "C:\Python314\pythonw.exe" (
    start "" "C:\Python314\pythonw.exe" "%~dp0server_manager.py"
) else (
    start "" pythonw "%~dp0server_manager.py"
)
