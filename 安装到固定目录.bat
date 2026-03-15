@echo off
chcp 65001 >nul
setlocal
set "SOURCE=%~dp0"
set "SOURCE=%SOURCE:~0,-1%"
set "TARGET=C:\PhoneCompetitor"

echo.
echo ========================================
echo   手机竞品分析 - 安装到固定目录
echo ========================================
echo.
echo 安装目录: %TARGET%
echo 源目录:   %SOURCE%
echo.
echo 将复制项目并创建桌面快捷方式，是否继续？
pause

if not exist "%TARGET%" mkdir "%TARGET%"

echo.
echo [1/4] 复制文件（排除 venv、node_modules、.next）…
robocopy "%SOURCE%" "%TARGET%" /E /XD venv node_modules .next .git .cursor /XF *.pyc /NFL /NDL /NJH /NJS /NC /NS
if errorlevel 8 (
    echo 复制失败。
    pause
    exit /b 1
)
echo 复制完成。

echo.
echo [2/4] 创建 Python 虚拟环境…
cd /d "%TARGET%"
if not exist "venv" (
    python -m venv venv
    if errorlevel 1 (
        echo 请先安装 Python 3.10+ 并加入 PATH。
        pause
        exit /b 1
    )
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
echo 后端依赖已安装。

echo.
echo [3/4] 安装前端依赖…
cd /d "%TARGET%\frontend"
if not exist "node_modules" (
    call npm install
) else (
    echo node_modules 已存在，跳过。
)
cd /d "%TARGET%"
echo.

echo [4/4] 创建桌面快捷方式…
powershell -NoProfile -ExecutionPolicy Bypass -File "%TARGET%\create_shortcut.ps1" "%TARGET%"

echo.
echo ========================================
echo   安装完成
echo ========================================
echo   安装目录: %TARGET%
echo   桌面快捷方式: 手机竞品分析
echo.
echo 双击桌面「手机竞品分析」即可启动。
echo 首次启动若提示缺少依赖，可在安装目录运行 start.bat。
echo.
pause
