#!/bin/bash

echo "======================================"
echo "  Email Priority API - Ngrok Deploy"
echo "======================================"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "ERROR: ngrok is not installed!"
    echo ""
    echo "Install ngrok:"
    echo "1. Download from https://ngrok.com/download"
    echo "2. Extract and add to PATH"
    echo "3. Run: ngrok authtoken YOUR_TOKEN"
    echo ""
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please run ./setup.sh first"
    echo ""
    exit 1
fi

# Read NG_KEY from .env
if grep -q "NG_KEY=" .env; then
    NG_KEY=$(grep "NG_KEY=" .env | cut -d '=' -f2)
    if [ ! -z "$NG_KEY" ] && [ "$NG_KEY" != "your_ngrok_authtoken_here" ]; then
        echo "Authenticating ngrok with token from .env..."
        ngrok config add-authtoken "$NG_KEY"
        echo ""
    fi
else
    echo "WARNING: NG_KEY not found in .env file"
    echo "Ngrok may not work without authentication"
    echo "Add NG_KEY=your_token to .env file"
    echo ""
fi

echo "Starting API server on port 4999..."
echo ""

# Start Flask in background
python app.py &
FLASK_PID=$!

# Wait for server to start
sleep 3

echo "Starting ngrok tunnel..."
echo ""
echo "Your API will be available at: https://xxxxx.ngrok.io"
echo "Copy the HTTPS URL and paste it in Code_Hybrid.gs (line 12)"
echo ""
echo "Press Ctrl+C to stop both server and ngrok"
echo ""

# Trap Ctrl+C to kill both processes
trap "kill $FLASK_PID; exit" INT

# Start ngrok
ngrok http 4999
