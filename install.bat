@echo off
chcp 65001 >nul
echo Установка русификатора Dawson Oaks Trailer Park
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\installer.ps1" %1
echo.
pause
