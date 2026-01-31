@echo off
chcp 65001 >nul
title Home Inn Cafe - Server

echo ╔════════════════════════════════════════════════════════════════╗
echo ║                     Home Inn Cafe Server                       ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [1/4] Running Django checks...
python manage.py check
if %errorlevel% neq 0 (
    echo.
    echo ❌ Django check failed! Please fix the errors above.
    pause
    exit /b 1
)
echo ✓ Checks passed!
echo.

echo [2/4] Running database migrations...
python manage.py migrate --run-syncdb
if %errorlevel% neq 0 (
    echo.
    echo ❌ Migration failed! Please fix the errors above.
    pause
    exit /b 1
)
echo ✓ Database ready!
echo.

echo [3/4] Getting your IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found_ip
)
:found_ip
set IP=%IP: =%

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║  Server URLs:                                                  ║
echo ║                                                                ║
echo ║  Local:    http://127.0.0.1:8000                               ║
echo ║  Network:  http://%IP%:8000                             ║
echo ║                                                                ║
echo ║  Press Ctrl+C to stop the server                               ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

echo [4/4] Opening browser and starting server...
start http://127.0.0.1:8000

python manage.py runserver 0.0.0.0:8000

pause
