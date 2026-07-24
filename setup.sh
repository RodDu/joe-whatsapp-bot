#!/bin/bash
echo "Setting up joe-whatsapp-bot..."

if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found. Install from https://nodejs.org"
    exit 1
fi

if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python not found. Install from https://python.org"
    exit 1
fi

echo "Installing Node.js dependencies..."
npm install

echo "Creating Python virtual environment..."
python3 -m venv .venv || python -m venv .venv

echo "Installing Python dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
fi

if [ ! -f config.json ]; then
    cp config.example.json config.json
fi

echo ""
echo "Setup complete! Edit .env with your settings, then run: npm start"
