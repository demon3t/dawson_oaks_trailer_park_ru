@echo off
chcp 65001 >nul
echo Установка русификатора Dawson Oaks Trailer Park
echo.
if "%~1"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -GameDir "%~1"
)
echo.
pause
