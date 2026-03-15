@echo off
chcp 65001 >nul
title 手机竞品-后端 (8000)
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo 后端运行中: http://127.0.0.1:8000
echo 关闭本窗口将停止服务。
echo.
uvicorn app.main_phone:app --host 0.0.0.0 --port 8000
pause
