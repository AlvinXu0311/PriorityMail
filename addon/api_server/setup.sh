#!/bin/bash

echo "=== Email Priority API Server Setup ==="
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "✓ .env file already exists"
else
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
fi

echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "Checking if model exists..."
if [ -f ../../data/models/priority_classifier.pkl ]; then
    echo "✓ Classification model found"
else
    echo "⚠️  Model not found at ../../data/models/priority_classifier.pkl"
    echo "   Please train the model first:"
    echo "   cd ../.. && python pipeline/run_full_pipeline.py --source data/enron_mail_20150507 --limit 1500"
fi

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Start server: python app.py"
echo "3. Expose with ngrok: ngrok http 5001"
echo ""
