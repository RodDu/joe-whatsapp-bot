@echo off
echo Setting up joe-whatsapp-bot...
where node >nul 2>&1 || (echo ERROR: Node.js not found. Install from https://nodejs.org && pause && exit /b 1)
where python >nul 2>&1 || (echo ERROR: Python not found. Install from https://python.org && pause && exit /b 1)
echo Installing Node.js dependencies...
npm install
echo Creating Python virtual environment...
python -m venv .venv
echo Installing Python dependencies...
.venv\Scripts\pip install -r requirements.txt
if not exist .env copy .env.example .env
if not exist config.json copy config.example.json config.json
echo.
echo Setup complete!
echo Edit .env with your settings, then run: npm start
pause
