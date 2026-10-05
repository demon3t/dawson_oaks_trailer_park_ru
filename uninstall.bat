@echo off
chcp 65001 >nul
echo Удаление русификатора Dawson Oaks Trailer Park
echo.
if "%~1"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Uninstall
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Uninstall -GameDir "%~1"
)
echo.
pause
