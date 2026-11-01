@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish-github.ps1" %*
exit /b %ERRORLEVEL%
