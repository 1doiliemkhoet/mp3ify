@echo off
REM Optional: create a single mp3ify.exe on Windows (Python is required for build only).
pushd "%~dp0"
where py >nul 2>nul
if not errorlevel 1 goto py_build
where python >nul 2>nul
if not errorlevel 1 goto python_build
echo [ERROR] Python 3 not installed.
exit /b 2
:py_build
py -3 -m pip install pyinstaller
if errorlevel 1 exit /b 1
py -3 -m PyInstaller --onefile --console --name mp3ify "%~dp0mp3ify.py"
exit /b %errorlevel%
:python_build
python -m pip install pyinstaller
if errorlevel 1 exit /b 1
python -m PyInstaller --onefile --console --name mp3ify "%~dp0mp3ify.py"
exit /b %errorlevel%
