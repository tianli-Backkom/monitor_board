@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
echo Starting Pre-Commit Dashboard Server...
echo.
echo ============================================
echo   Visit: http://localhost:8000
echo ============================================
echo.
python start.py
pause
