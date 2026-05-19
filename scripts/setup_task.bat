@echo off
chcp 65001 >nul
echo ========================================
echo    Pre-Commit 看板 - 定时任务配置
echo ========================================
echo.

set "PROJECT_DIR=%~dp0.."
set "PYTHON_EXE=python"
set "TASK_NAME=PreCommitDashboardUpdate"

echo 项目目录: %PROJECT_DIR%
echo.

REM 检测 Python 是否可用
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 先执行一次数据更新，确保可用
echo [1/3] 执行首次数据更新...
cd /d "%PROJECT_DIR%"
%PYTHON_EXE% scripts\daily_update.py
if errorlevel 1 (
    echo [警告] 首次更新失败，但继续创建任务
)

echo.
echo [2/3] 创建 Windows 定时任务（每日 9:00 执行）...

REM 删除已存在的任务
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM 创建新任务（每天 9:00 执行）
schtasks /create /tn "%TASK_NAME%" ^
    /tr "\"%PROJECT_DIR%\scripts\run_update.bat\"" ^
    /sc daily /st 09:00 ^
    /f

if errorlevel 1 (
    echo [错误] 定时任务创建失败，请以管理员身份运行此脚本
    pause
    exit /b 1
)

echo [成功] 定时任务已创建
echo.
echo [3/3] 创建 Web 服务器启动脚本...

REM 创建启动脚本
echo @echo off > "%PROJECT_DIR%\start_server.bat"
echo chcp 65001 ^>nul >> "%PROJECT_DIR%\start_server.bat"
echo cd /d "%PROJECT_DIR%" >> "%PROJECT_DIR%\start_server.bat"
echo %PYTHON_EXE% scripts\web_server.py 8000 >> "%PROJECT_DIR%\start_server.bat"
echo pause >> "%PROJECT_DIR%\start_server.bat"

echo ========================================
echo    配置完成！
echo ========================================
echo.
echo 📅 定时任务: 每日 9:00 自动更新数据
echo 🌐 Web 服务: 运行 start_server.bat 启动服务器
echo.
echo 下一步操作:
echo   1. 双击运行 start_server.bat 启动 Web 服务器
echo   2. 浏览器访问 http://localhost:8000 查看看板
echo   3. 分享你的局域网 IP 给团队其他成员
echo.
echo 查看任务: 控制面板 - 管理工具 - 任务计划程序 - 任务计划程序库
echo 删除任务: schtasks /delete /tn "%TASK_NAME%" /f
echo.
pause
