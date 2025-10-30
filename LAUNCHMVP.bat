@echo off
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%logs"
set "LOG_FILE=%LOG_DIR%\mvp_last_run.log"

if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
    if errorlevel 1 (
        echo Failed to create log directory: "%LOG_DIR%"
        echo Cannot continue without a place to store the error log.
        pause
        exit /b 1
    )
)

echo Nightfall Survivors MVP Launcher
echo Log file: %LOG_FILE%
echo.

( 
    echo ==== Nightfall Survivors MVP Launcher ====
    echo Run started %DATE% %TIME%
    echo.
) > "%LOG_FILE%"

echo Changing directory to: %SCRIPT_DIR%
>> "%LOG_FILE%" echo Changing directory to: %SCRIPT_DIR%
cd /d "%SCRIPT_DIR%"
if errorlevel 1 goto :error

echo.
echo Updating repository to latest main branch...
>> "%LOG_FILE%" echo.
>> "%LOG_FILE%" echo Updating repository to latest main branch...
git pull >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :error

echo.
echo Launching MVP simulation...
>> "%LOG_FILE%" echo.
>> "%LOG_FILE%" echo Launching MVP simulation...
python -m game.mvp --summary >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :error

echo.
type "%LOG_FILE%"
echo.
echo MVP simulation finished. Full log saved to:
echo   %LOG_FILE%
echo Press any key to close this window.
pause >nul
exit /b 0

:error
set "STATUS=%errorlevel%"
echo.
echo MVP launcher encountered an error. Output log:
echo -----------------------------------------------
if exist "%LOG_FILE%" type "%LOG_FILE%"
echo -----------------------------------------------
echo.
if exist "%LOG_FILE%" (
    echo An error occurred. The full log has been saved to:
    echo   %LOG_FILE%
) else (
    echo An error occurred before the log file could be written.
)
echo Please review the log and press any key to close this window.
pause
exit /b %STATUS%
