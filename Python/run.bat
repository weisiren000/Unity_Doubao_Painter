@echo off
chcp 65001 >nul
title Unity截图 + 豆包AI生图系统
echo ====================================================
echo       Unity截图 + 豆包AI生图系统 启动脚本
echo ====================================================
echo.

:: 设置颜色
setlocal EnableDelayedExpansion
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set "DEL=%%a"
)

:: 检查PowerShell是否可用
powershell -Command "exit" 2>nul
if %ERRORLEVEL% neq 0 (
    call :colorEcho 0C "错误: 未检测到PowerShell，无法启动程序"
    echo 请确保您的Windows系统已安装PowerShell
    pause
    exit /b 1
)

:: 启动PowerShell脚本
call :colorEcho 0B "正在启动系统，请稍候..."
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1"
exit /b 0

:colorEcho
echo %DEL% > "%~2"
findstr /v /a:%1 /R "^$" "%~2" nul
del "%~2" > nul
exit /b