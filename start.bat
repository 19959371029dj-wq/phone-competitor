@echo off
chcp 65001 >nul
title 手机竞品分析 - 一键启动
echo.
echo ========================================
echo   手机竞品分析 - 一键启动
echo ========================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [错误] 未找到 venv，请先执行: python -m venv venv
    pause
    exit /b 1
)

echo [1/3] 检查 Python 依赖…
call venv\Scripts\activate.bat
pip install -q -r requirements.txt 2>nul
echo.

echo [2/3] 启动后端 (新窗口)…
start "" "%~dp0start_backend.bat"

echo [3/3] 启动前端 (新窗口)…
timeout /t 2 /nobreak >nul
start "" "%~dp0start_frontend.bat"

echo.
echo 已打开两个新窗口：
echo   - 手机竞品-后端：API 端口 8000
echo   - 手机竞品-前端：页面端口 3000
echo.
echo 浏览器打开: http://localhost:3000
echo 请勿关闭后端、前端两个窗口。
echo.
pause
