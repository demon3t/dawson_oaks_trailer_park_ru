@echo off
chcp 65001 >nul
echo Удаление русификатора Dawson Oaks Trailer Park
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\installer.ps1" -Uninstall %1
echo.
pause
