@echo off
title Never Suite - Installer
echo.
echo  ███╗   ██╗███████╗██╗   ██╗███████╗██████╗
echo  ████╗  ██║██╔════╝██║   ██║██╔════╝██╔══██╗
echo  ██╔██╗ ██║█████╗  ██║   ██║█████╗  ██████╔╝
echo  ██║╚██╗██║██╔══╝  ╚██╗ ██╔╝██╔══╝  ██╔══██╗
echo  ██║ ╚████║███████╗ ╚████╔╝ ███████╗██║  ██║
echo  ╚═╝  ╚═══╝╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝
echo                 I N S T A L L E R  v1.0
echo.

:: Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org, then re-run.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER% detected.
echo.
echo [*] Installing Python dependencies from requirements.txt...
pip install -r "%~dp0requirements.txt" --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Some packages may have failed to install. Check output above.
) else (
    echo [OK] All dependencies installed successfully.
)
echo.
echo [*] Running Never Suite Installer UI...
python "%~dp0Never_Installer\main.py"
pause
