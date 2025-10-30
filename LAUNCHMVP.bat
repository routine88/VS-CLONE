@echo off
setlocal
echo Nightfall Survivors MVP Launcher
cd /d %~dp0 || goto :error

echo.
echo Updating repository to latest main branch...
git pull || goto :error

echo.
echo Launching MVP simulation...
python -m game.mvp --summary || goto :error

echo.
echo MVP simulation finished. Press any key to close this window.
pause >nul

goto :eof

:error
echo.
echo An error occurred. Exiting.
pause
exit /b 1
