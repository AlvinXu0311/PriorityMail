@echo off
echo === Email Priority API Server Setup ===
echo.

REM Check if .env exists
if exist .env (
    echo √ .env file already exists
) else (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo ‼ Please edit .env and add your API keys!
)

echo.
echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Checking if model exists...
if exist "..\..\data\models\priority_classifier.pkl" (
    echo √ Classification model found
) else (
    echo ‼ Model not found at ..\..\data\models\priority_classifier.pkl
    echo    Please train the model first:
    echo    cd ..\.. ^&^& python pipeline\run_full_pipeline.py --source data\enron_mail_20150507 --limit 1500
)

echo.
echo === Setup Complete! ===
echo.
echo Next steps:
echo 1. Edit .env file and add:
echo    - GEMINI_API_KEY (from https://makersuite.google.com)
echo    - API_KEY (generate with: python -c "import secrets; print(secrets.token_hex(16))")
echo    - NG_KEY (from https://dashboard.ngrok.com/get-started/your-authtoken)
echo.
echo 2. Run deployment script:
echo    deploy_ngrok.bat
echo.
pause
