@echo off
echo ======================================
echo   Email Priority API - Ngrok Deploy
echo ======================================
echo.

REM Check if ngrok is installed
where ngrok >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: ngrok is not installed!
    echo.
    echo Install ngrok:
    echo 1. Download from https://ngrok.com/download
    echo 2. Extract and add to PATH
    echo 3. Run: ngrok authtoken YOUR_TOKEN
    echo.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please run setup.bat first
    echo.
    pause
    exit /b 1
)

REM Read NG_KEY from .env
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="NG_KEY" set NG_KEY=%%b
)

REM Authenticate ngrok with token from .env
if defined NG_KEY (
    echo Authenticating ngrok with token from .env...
    ngrok config add-authtoken %NG_KEY%
    echo.
) else (
    echo WARNING: NG_KEY not found in .env file
    echo Ngrok may not work without authentication
    echo Add NG_KEY=your_token to .env file
    echo.
)

echo Starting API server on port 4999...
echo.

REM Start Flask in background
start /B python app.py

REM Wait for server to start
timeout /t 3 /nobreak >nul

echo Starting ngrok tunnel...
echo.
echo Your API will be available at: https://xxxxx.ngrok.io
echo Copy the HTTPS URL and paste it in Code_Hybrid.gs (line 12)
echo.
echo Press Ctrl+C to stop both server and ngrok
echo.

REM Start ngrok
ngrok http 4999
