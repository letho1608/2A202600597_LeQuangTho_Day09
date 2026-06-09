@echo off
chcp 65001 >nul
title Legal Multi-Agent Demo

echo ============================================
echo   Legal Multi-Agent System - Single Process
echo ============================================
echo.

:: Ki?m tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Python chua duoc cai dat hoac khong trong PATH
    pause
    exit /b 1
)

:: Kích ho?t virtual environment n?u có
if exist .venv\Scripts\activate.bat (
    echo [INFO] Dang kich hoat virtual environment...
    call .venv\Scripts\activate.bat
)

:: Cài d?t dependencies
echo [INFO] Dang cai dat dependencies...
pip install -e .
if %errorlevel% neq 0 (
    echo [LOI] Cai dat dependencies that bai.
    pause
    exit /b 1
)

echo.
echo [INFO] Khoi dong tat ca services trong 1 terminal...
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo [LOI] Khong the khoi dong he thong.
    pause
)
