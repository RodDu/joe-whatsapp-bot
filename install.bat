@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title Joe WhatsApp Bot - Installer
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║                                                          ║
echo  ║     🤖  JOE WHATSAPP BOT  -  INSTALLER                  ║
echo  ║                                                          ║
echo  ║     Your personal AI assistant on WhatsApp               ║
echo  ║                                                          ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo  This installer will guide you through the entire setup.
echo  No technical knowledge required!
echo.
echo  ─────────────────────────────────────────────────────────
echo.

:: ============================================================
:: STEP 1: Check Node.js
:: ============================================================
echo  [Step 1/7] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ❌ Node.js is NOT installed.
    echo.
    echo  Node.js is required to run the WhatsApp bot.
    echo  I'll try to install it for you now.
    echo.
    where winget >nul 2>&1
    if !errorlevel! equ 0 (
        echo  Installing Node.js via winget...
        winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
        if !errorlevel! neq 0 (
            echo.
            echo  ⚠️  Automatic install failed.
            echo  Please install Node.js manually from: https://nodejs.org
            echo  Download the LTS version, install it, then run this script again.
            echo.
            pause
            exit /b 1
        )
        echo  ✅ Node.js installed! You may need to restart this terminal.
        echo     Close this window and run install.bat again.
        pause
        exit /b 0
    ) else (
        echo  ⚠️  Cannot install automatically (winget not found).
        echo  Please install Node.js manually from: https://nodejs.org
        echo  Download the LTS version, install it, then run this script again.
        echo.
        pause
        exit /b 1
    )
) else (
    for /f "tokens=*" %%v in ('node --version') do set NODE_VER=%%v
    echo  ✅ Node.js found: !NODE_VER!
)
echo.

:: ============================================================
:: STEP 2: Check Python
:: ============================================================
echo  [Step 2/7] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ❌ Python is NOT installed.
    echo.
    echo  Python is required for AI voice processing.
    echo  I'll try to install it for you now.
    echo.
    where winget >nul 2>&1
    if !errorlevel! equ 0 (
        echo  Installing Python via winget...
        winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        if !errorlevel! neq 0 (
            echo.
            echo  ⚠️  Automatic install failed.
            echo  Please install Python manually from: https://python.org
            echo  IMPORTANT: Check "Add Python to PATH" during installation!
            echo  Then run this script again.
            echo.
            pause
            exit /b 1
        )
        echo  ✅ Python installed! You may need to restart this terminal.
        echo     Close this window and run install.bat again.
        pause
        exit /b 0
    ) else (
        echo  ⚠️  Cannot install automatically.
        echo  Please install Python from: https://python.org
        echo  IMPORTANT: Check "Add Python to PATH" during installation!
        echo  Then run this script again.
        echo.
        pause
        exit /b 1
    )
) else (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
    echo  ✅ Python found: !PY_VER!
)
echo.

:: ============================================================
:: STEP 3: Check ffmpeg
:: ============================================================
echo  [Step 3/7] Checking ffmpeg (for voice messages)...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ⚠️  ffmpeg is NOT installed.
    echo  ffmpeg is needed to process voice messages.
    echo.
    where winget >nul 2>&1
    if !errorlevel! equ 0 (
        echo  Installing ffmpeg via winget...
        winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
        if !errorlevel! neq 0 (
            echo  ⚠️  Could not install ffmpeg automatically.
            echo  Voice messages won't work until ffmpeg is installed.
            echo  You can install it later from: https://ffmpeg.org/download.html
        ) else (
            echo  ✅ ffmpeg installed!
        )
    ) else (
        echo  ⚠️  Cannot install ffmpeg automatically.
        echo  Voice messages won't work until you install it.
        echo  Download from: https://ffmpeg.org/download.html
    )
) else (
    echo  ✅ ffmpeg found!
)
echo.

:: ============================================================
:: STEP 4: Install project dependencies
:: ============================================================
echo  [Step 4/7] Installing bot dependencies...
echo.
echo  Installing Node.js packages (this may take a minute)...
call npm install --no-fund --no-audit 2>nul
if %errorlevel% neq 0 (
    echo  ❌ npm install failed. Check errors above.
    pause
    exit /b 1
)
echo  ✅ Node.js packages installed!
echo.

echo  Creating Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
)
echo  Installing Python packages...
.venv\Scripts\pip install -q -r requirements.txt 2>nul
if %errorlevel% neq 0 (
    echo  ⚠️  Some Python packages may have failed.
    echo  Voice features might not work fully, but the bot will still run.
)
echo  ✅ Python packages installed!
echo.

:: ============================================================
:: STEP 5: Configuration - Ask questions
:: ============================================================
echo  ─────────────────────────────────────────────────────────
echo.
echo  [Step 5/7] Let's configure your bot!
echo.
echo  I need to ask you a few questions.
echo  ─────────────────────────────────────────────────────────
echo.

:: --- Phone Number ---
:ask_phone
echo  📱 What is your WhatsApp phone number?
echo     Include country code, no + or spaces.
echo     Example: 5511999998888 (Brazil) or 14155551234 (USA)
echo.
set /p PHONE="     Your number: "
if "!PHONE!"=="" (
    echo     ❌ Phone number is required! Try again.
    echo.
    goto ask_phone
)
echo.
echo  ✅ Phone: !PHONE!
echo.

:: --- AI Provider ---
echo  🧠 Which AI provider do you want to use?
echo.
echo     [1] Gemini API (cloud - recommended, free tier available)
echo     [2] Ollama (local - runs on your PC, fully private)
echo     [3] Both (best experience - cloud + local fallback)
echo.
set /p AI_CHOICE="     Your choice (1/2/3): "
if "!AI_CHOICE!"=="" set AI_CHOICE=1
echo.

set GEMINI_KEY=
set OLLAMA_URL=http://localhost:11434
set OLLAMA_MODEL=gemma2

if "!AI_CHOICE!"=="1" (
    goto ask_gemini
) else if "!AI_CHOICE!"=="3" (
    goto ask_gemini
) else (
    goto ask_ollama_model
)

:ask_gemini
echo  🔑 Enter your Gemini API key.
echo     Get a FREE key at: https://aistudio.google.com/apikey
echo     (I'll open the page for you in 3 seconds...)
timeout /t 3 >nul
start "" "https://aistudio.google.com/apikey"
echo.
set /p GEMINI_KEY="     API Key: "
if "!GEMINI_KEY!"=="" (
    echo     ⚠️  No key entered. Bot will try Ollama as fallback.
)
echo.

if "!AI_CHOICE!"=="3" goto ask_ollama_model
goto ask_language

:ask_ollama_model
echo  🏠 Which Ollama model do you want to use?
echo.
echo     [1] gemma2 (recommended, good balance)
echo     [2] llama3.2 (Meta's model, great for chat)
echo     [3] qwen2.5 (good for coding)
echo     [4] Other (type the name)
echo.
set /p MODEL_CHOICE="     Your choice (1/2/3/4): "
if "!MODEL_CHOICE!"=="" set MODEL_CHOICE=1

if "!MODEL_CHOICE!"=="1" set OLLAMA_MODEL=gemma2
if "!MODEL_CHOICE!"=="2" set OLLAMA_MODEL=llama3.2
if "!MODEL_CHOICE!"=="3" set OLLAMA_MODEL=qwen2.5
if "!MODEL_CHOICE!"=="4" (
    set /p OLLAMA_MODEL="     Model name: "
)
echo  ✅ Model: !OLLAMA_MODEL!
echo.

:: Check if Ollama is installed
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo  ⚠️  Ollama is not installed yet.
    echo  Install from: https://ollama.ai
    echo  After installing, run: ollama pull !OLLAMA_MODEL!
) else (
    echo  Downloading model !OLLAMA_MODEL! (this may take a few minutes)...
    ollama pull !OLLAMA_MODEL! 2>nul
)
echo.

:ask_language
:: --- Language ---
echo  🌍 What language should the bot speak?
echo.
echo     [1] English
echo     [2] Português (Brasil)
echo     [3] Español
echo     [4] Other
echo.
set /p LANG_CHOICE="     Your choice (1/2/3/4): "
if "!LANG_CHOICE!"=="" set LANG_CHOICE=1

set TTS_VOICE=en-US-GuyNeural
set BOT_LANG=en

if "!LANG_CHOICE!"=="1" (
    set TTS_VOICE=en-US-GuyNeural
    set BOT_LANG=en
)
if "!LANG_CHOICE!"=="2" (
    set TTS_VOICE=pt-BR-AntonioNeural
    set BOT_LANG=pt
)
if "!LANG_CHOICE!"=="3" (
    set TTS_VOICE=es-ES-AlvaroNeural
    set BOT_LANG=es
)
if "!LANG_CHOICE!"=="4" (
    set /p TTS_VOICE="     edge-tts voice name: "
    set BOT_LANG=en
)
echo  ✅ Voice: !TTS_VOICE!
echo.

:: --- Bot Name ---
echo  🤖 What should the bot be called? (default: Joe)
set /p BOT_NAME="     Bot name: "
if "!BOT_NAME!"=="" set BOT_NAME=Joe
echo  ✅ Name: !BOT_NAME!
echo.

:: ============================================================
:: STEP 6: Write configuration files
:: ============================================================
echo  [Step 6/7] Saving your configuration...
echo.

:: Write .env
(
    echo # joe-whatsapp-bot configuration
    echo # Generated by installer on %date% %time%
    echo.
    echo OWNER_PHONE=!PHONE!
    echo GEMINI_API_KEY=!GEMINI_KEY!
    echo OLLAMA_BASE_URL=!OLLAMA_URL!
    echo OLLAMA_MODEL=!OLLAMA_MODEL!
    echo BOT_NAME=!BOT_NAME!
    echo USER_TITLE=
    echo BOT_SYSTEM_PROMPT=
    echo TTS_ENGINE=edge-tts
    echo TTS_VOICE=!TTS_VOICE!
    echo VOICEBOX_URL=http://127.0.0.1:17493
    echo TRANSCRIPTION_ENGINE=gemini
    echo TUNNEL_PORT=8080
) > .env

echo  ✅ .env created!

:: Write config.json with language
(
    echo {
    echo   "bot": {
    echo     "name": "!BOT_NAME!",
    echo     "language": "!BOT_LANG!",
    echo     "userTitle": "",
    echo     "systemPrompt": ""
    echo   },
    echo   "agents": {
    echo     "assistant": {
    echo       "type": "api",
    echo       "model": "gemini-2.5-flash",
    echo       "description": "Cloud AI assistant"
    echo     },
    echo     "local": {
    echo       "type": "local",
    echo       "model": "!OLLAMA_MODEL!",
    echo       "description": "Local AI for private use"
    echo     },
    echo     "system": {
    echo       "type": "system",
    echo       "description": "System commands"
    echo     }
    echo   },
    echo   "agentAliases": {
    echo     "ai": "assistant",
    echo     "gemini": "assistant",
    echo     "ollama": "local",
    echo     "gemma": "local"
    echo   },
    echo   "monitoring": {
    echo     "services": [
    echo       {
    echo         "name": "Ollama",
    echo         "check": "http",
    echo         "url": "http://localhost:11434",
    echo         "description": "Local LLM server"
    echo       }
    echo     ]
    echo   },
    echo   "autoRoute": {
    echo     "systemKeywords": ["restart", "status", "logs", "process", "service"],
    echo     "codeKeywords": ["code", "program", "python", "javascript", "bug", "error", "script"],
    echo     "creativeKeywords": ["analyze", "creative", "imagine", "write", "story", "poem"]
    echo   },
    echo   "tts": {
    echo     "maxChars": 2000,
    echo     "voice": "!TTS_VOICE!"
    echo   },
    echo   "notifications": {
    echo     "enabled": true,
    echo     "checkIntervalMs": 10000
    echo   }
    echo }
) > config.json

echo  ✅ config.json created!
echo.

:: ============================================================
:: STEP 7: Launch!
:: ============================================================
echo  ─────────────────────────────────────────────────────────
echo.
echo  [Step 7/7] Everything is ready! 🎉
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║                                                          ║
echo  ║   ✅  INSTALLATION COMPLETE!                             ║
echo  ║                                                          ║
echo  ║   Your bot "!BOT_NAME!" is configured and ready.        ║
echo  ║                                                          ║
echo  ║   WHAT HAPPENS NEXT:                                     ║
echo  ║   1. A QR code will appear in this window                ║
echo  ║   2. Open WhatsApp on your phone                         ║
echo  ║   3. Go to Settings → Linked Devices                    ║
echo  ║   4. Scan the QR code                                    ║
echo  ║   5. Send yourself a message to test!                    ║
echo  ║                                                          ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo  Press any key to start the bot...
pause >nul

echo.
echo  Starting !BOT_NAME!...
echo.
node bot.js
echo.
echo  ─────────────────────────────────────────────────────────
echo  Bot stopped. Press any key to restart, or close the window.
echo  ─────────────────────────────────────────────────────────
pause >nul
node bot.js
