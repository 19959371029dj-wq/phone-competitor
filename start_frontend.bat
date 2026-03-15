@echo off
chcp 65001 >nul
title 手机竞品-前端 (3000)
cd /d "%~dp0frontend"
echo 前端运行中: http://localhost:3000
echo 关闭本窗口将停止服务。
echo.
npm run dev
pause
