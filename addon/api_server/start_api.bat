@echo off
echo ======================================
echo   Starting Email Priority API Server
echo ======================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure it
    echo.
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo Starting Flask API server on port 4999...
echo.
echo API Endpoints:
echo   - http://localhost:4999/health
echo   - http://localhost:4999/api/classify
echo   - http://localhost:4999/api/process-email
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start Flask
python app.py
