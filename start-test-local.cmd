@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-test-local.ps1"
exit /b %ERRORLEVEL%