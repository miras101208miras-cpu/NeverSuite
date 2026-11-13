@echo off
title Never Suite - Starting Never Hub...
echo.
echo  ███╗   ██╗███████╗██╗   ██╗███████╗██████╗
echo  ████╗  ██║██╔════╝██║   ██║██╔════╝██╔══██╗
echo  ██╔██╗ ██║█████╗  ██║   ██║█████╗  ██████╔╝
echo  ██║╚██╗██║██╔══╝  ╚██╗ ██╔╝██╔══╝  ██╔══██╗
echo  ██║ ╚████║███████╗ ╚████╔╝ ███████╗██║  ██║
echo  ╚═╝  ╚═══╝╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝
echo                     S U I T E  v1.0
echo.

:: Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org and re-run this script.
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER% detected.
echo.

:: Check pythonw (windowless launcher)
where pythonw >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Launching Never Hub (silent / no console window)...
    start "" pythonw "%~dp0Never_Hub\main.py"
) else (
    echo [INFO] pythonw not found, launching with python...
    start "" python "%~dp0Never_Hub\main.py"
)

echo Never Hub is starting up — check your taskbar!
timeout /t 2 /nobreak >nul
exit /b 0
