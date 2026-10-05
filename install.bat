@echo off
chcp 65001 >nul
echo Установка русификатора Dawson Oaks Trailer Park
echo.
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
if "%~1"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([scriptblock]::Create([IO.File]::ReadAllText('%ROOT%\install.ps1'))) -LocalRoot '%ROOT%'"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([scriptblock]::Create([IO.File]::ReadAllText('%ROOT%\install.ps1'))) -LocalRoot '%ROOT%' -GameDir '%~1'"
)
echo.
pause
