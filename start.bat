@echo off
REM Windows batch script to launch Hippique Predictor
REM Colors simulation for Windows CMD

cls
echo.
echo ================================
echo  Hippique Predictor
echo ================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker daemon is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Build and start containers
echo [INFO] Building Docker image...
call docker-compose build --no-cache

if %errorlevel% neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo [OK] Build successful
echo.

echo [INFO] Starting application...
call docker-compose up -d

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start application
    pause
    exit /b 1
)

echo [OK] Application started
echo.

echo [INFO] Waiting for application to be ready (30-40 seconds for model training)...
timeout /t 5 /nobreak

REM Check health with retry
setlocal enabledelayedexpansion
set MAX_RETRIES=8
set RETRY_COUNT=0

:health_check
if %RETRY_COUNT% lss %MAX_RETRIES% (
    timeout /t 5 /nobreak >nul
    curl -s http://localhost:5000/api/health >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] Application is healthy
        echo.
        goto success
    )
    set /a RETRY_COUNT=!RETRY_COUNT!+1
    echo Attempt !RETRY_COUNT!/%MAX_RETRIES%...
    goto health_check
) else (
    echo [WARNING] Application is starting but not yet fully ready
    echo Check logs with: docker-compose logs -f app
    echo.
    goto success
)

:success
echo ================================
echo  Application Ready!
echo ================================
echo.
echo Frontend: http://localhost:5000
echo API Health: http://localhost:5000/api/health
echo.
echo ================================
echo.
echo Useful commands:
echo   docker-compose logs -f app    - View logs
echo   docker-compose down           - Stop application
echo   docker-compose ps             - Check status
echo.

REM Open browser if possible
timeout /t 2 /nobreak >nul
start http://localhost:5000

pause
