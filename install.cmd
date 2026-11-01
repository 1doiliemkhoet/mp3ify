@echo off
setlocal
set "DEST=%LOCALAPPDATA%\Programs\mp3ify"
if not exist "%DEST%" mkdir "%DEST%"
if errorlevel 1 goto error
copy /y "%~dp0mp3ify.py" "%DEST%\mp3ify.py" >nul
if errorlevel 1 goto error
copy /y "%~dp0mp3ify.cmd" "%DEST%\mp3ify.cmd" >nul
if errorlevel 1 goto error
powershell -NoProfile -Command "$dest=Join-Path $env:LOCALAPPDATA 'Programs\mp3ify'; $p=[Environment]::GetEnvironmentVariable('Path','User'); if (-not $p) {$p=''}; if (($p -split ';') -notcontains $dest) { [Environment]::SetEnvironmentVariable('Path', (($p.TrimEnd(';')+';'+$dest).TrimStart(';')), 'User') }"
if errorlevel 1 goto error
echo.
echo [OK] mp3ify installed to "%DEST%"
echo Open a NEW CMD / PowerShell window and run: mp3ify --help
echo.
echo Prerequisites: Python 3, FFmpeg and FFprobe in PATH.
exit /b 0
:error
echo [ERROR] Installation failed. You can also run mp3ify.cmd directly from this folder.
exit /b 1
