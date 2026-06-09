@echo off
chcp 65001 >nul
title Legal Multi-Agent Demo

echo ============================================
echo   Legal Multi-Agent System - Web Demo
echo ============================================
echo.

:: Kiểm tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Python chua duoc cai dat hoac khong trong PATH
    pause
    exit /b 1
)

:: Kích hoạt virtual environment nếu có
if exist .venv\Scripts\activate.bat (
    echo [INFO] Dang kich hoat virtual environment...
    call .venv\Scripts\activate.bat
)

:: Kiểm tra uv
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] uv khong tim thay, dung pip thay the...
    pip install -e . >nul 2>&1
) else (
    echo [INFO] Dung uv de dong bo dependencies...
    uv sync >nul 2>&1
)

echo.
echo [INFO] Mo trinh duyet tai: http://localhost:8080
echo [INFO] Nhan Ctrl+C de dung server
echo.

python -m demo_web

if %errorlevel% neq 0 (
    echo.
    echo [LOI] Khong the khoi dong server. Kiem tra lai.
    pause
)
