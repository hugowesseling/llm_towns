@echo off
REM ============================================================================
REM
REM LLM Towns - Start Both Server and Client (Windows)
REM
REM Usage:
REM   start.bat              Starts both server and client with defaults
REM   start.bat --help       Show help message
REM   start.bat --server     Start only the server
REM   start.bat --client     Start only the client
REM
REM This script:
REM   1. Validates Python installation
REM   2. Checks dependencies (pygame, requests)
REM   3. Starts Flask server in separate window
REM   4. Waits for server to be ready
REM   5. Starts visualization client
REM
REM ============================================================================

setlocal enabledelayedexpansion

REM Configuration
set "PROJECT_DIR=%~dp0"
set "SERVER_SCRIPT=%PROJECT_DIR%app.py"
set "CLIENT_DIR=%PROJECT_DIR%client"
set "CLIENT_SCRIPT=%CLIENT_DIR%\viewer.py"
set "SERVER_PORT=5000"
set "SERVER_TIMEOUT=30"

REM Check for arguments
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help
if "%1"=="--server" goto :start_server_only
if "%1"=="--client" goto :start_client_only
if "%1"=="" goto :start_both

echo Error: Unknown argument '%1'
echo Run "start.bat --help" for usage information
exit /b 1

REM ============================================================================
:show_help
REM ============================================================================
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                 LLM TOWNS - START SERVER ^& CLIENT                       ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo Usage:
echo   start.bat              Start both server and client (default^)
echo   start.bat --help       Show this help message
echo   start.bat --server     Start only the server (new window^)
echo   start.bat --client     Start only the client
echo.
echo Environment Variables (optional^):
echo   PROJECT_DIR            Override project directory
echo   SERVER_PORT            Change server port (default: 5000^)
echo   SERVER_TIMEOUT         Wait time for server (default: 30 seconds^)
echo.
echo Examples:
echo   # Start both in one command
echo   start.bat
echo.
echo   # Start server in background window, client in current window
echo   start.bat --server
echo   start.bat --client
echo.
echo   # Change server port
echo   set SERVER_PORT=8000
echo   start.bat
echo.
echo What happens:
echo   1. Validates Python 3.8+
echo   2. Checks for required packages (pygame, requests^)
echo   3. Starts Flask server in separate window
echo   4. Waits for server to respond
echo   5. Starts visualization client
echo   6. Stops server when client closes
echo.
echo Keyboard shortcuts in client:
echo   Up/Down/Left/Right     Scroll map
echo   Left-click             Select entity
echo   Space                  Pause/resume
echo   ESC                    Exit
echo.
echo For more information, read:
echo   - QUICK_START.txt      (in project root^)
echo   - CLIENT_GUIDE.md      (comprehensive guide^)
echo   - CLIENT_SUMMARY.md    (technical details^)
echo.
goto :eof

REM ============================================================================
:check_python
REM ============================================================================
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found
exit /b 0

REM ============================================================================
:check_dependencies
REM ============================================================================
python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing pygame...
    python -m pip install --quiet pygame
)

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing requests...
    python -m pip install --quiet requests
)

echo [OK] All dependencies available
exit /b 0

REM ============================================================================
:start_both
REM ============================================================================
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║              LLM TOWNS - STARTING SERVER ^& CLIENT                       ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo [INFO] Project directory: %PROJECT_DIR%
echo [INFO] Server port: %SERVER_PORT%
echo.

call :check_python
if errorlevel 1 exit /b 1

call :check_dependencies
if errorlevel 1 exit /b 1

echo.
echo [INFO] Starting Flask server in new window...
echo.

start "LLM Towns Server" python "%SERVER_SCRIPT%"

echo [INFO] Waiting for server to respond...
setlocal enabledelayedexpansion
set /a elapsed=0

:wait_loop
timeout /t 1 /nobreak >nul 2>&1
curl -s "http://localhost:%SERVER_PORT%/health" >nul 2>&1
if errorlevel 0 (
    echo [OK] Server is ready!
    goto :server_ready
)

set /a elapsed=!elapsed!+1
if !elapsed! geq %SERVER_TIMEOUT% (
    echo [ERROR] Server failed to start within %SERVER_TIMEOUT% seconds
    exit /b 1
)

if !elapsed! equ 5 echo [INFO] Still waiting (this can take a moment^)...
goto :wait_loop

:server_ready
echo.
echo [INFO] Launching visualization client...
echo.

cd /d "%CLIENT_DIR%"
python "%CLIENT_SCRIPT%"

echo.
echo [INFO] Client closed.
goto :eof

REM ============================================================================
:start_server_only
REM ============================================================================
echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                   LLM TOWNS - SERVER ONLY                               ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

call :check_python
if errorlevel 1 exit /b 1

call :check_dependencies
if errorlevel 1 exit /b 1

echo.
echo [INFO] Starting Flask server on port %SERVER_PORT%...
echo.

cd /d "%PROJECT_DIR%"
python "%SERVER_SCRIPT%"
goto :eof

REM ============================================================================
:start_client_only
REM ============================================================================
echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                   LLM TOWNS - CLIENT ONLY                               ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

call :check_python
if errorlevel 1 exit /b 1

call :check_dependencies
if errorlevel 1 exit /b 1

echo.
echo [INFO] Starting visualization client...
echo [INFO] Make sure server is running on port %SERVER_PORT%
echo.

cd /d "%CLIENT_DIR%"
python "%CLIENT_SCRIPT%"
goto :eof
