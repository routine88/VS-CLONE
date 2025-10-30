@echo off
setlocal
echo Nightfall Survivors MVP Launcher
cd /d %~dp0 || goto :error

echo.
echo Updating repository to latest main branch...
git pull || goto :error

echo.
echo Launching MVP simulation...
python -m game.mvp --summary

goto :eof

:error
echo.
echo An error occurred. Exiting.
exit /b 1
