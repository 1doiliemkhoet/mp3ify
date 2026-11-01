@echo off
REM mp3ify launcher: Python 3 + FFmpeg, both work offline.
where py >nul 2>nul
if not errorlevel 1 goto launch_py
where python >nul 2>nul
if not errorlevel 1 goto launch_python
echo [ERROR] Python 3 not found. Install Python 3, then open a new CMD window.
exit /b 2
:launch_py
py -3 "%~dp0mp3ify.py" %*
exit /b %errorlevel%
:launch_python
python "%~dp0mp3ify.py" %*
exit /b %errorlevel%
