@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo.
echo 正在创建桌面快捷方式…
echo 项目目录: %INSTALL_DIR%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1" "%INSTALL_DIR%"
if errorlevel 1 (
    echo.
    echo 创建失败。若提示无法执行脚本，请以管理员运行 PowerShell 执行:
    echo   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    echo 然后重新运行本 bat。
    echo.
    pause
    exit /b 1
)

echo.
echo 请到桌面查看「手机竞品分析」图标。若无，请查看上面显示的路径。
echo.
pause
