#!/bin/bash
# joe-whatsapp-bot Interactive Installer for Linux / macOS
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear
echo ""
echo -e "${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════╗"
echo "  ║                                                          ║"
echo "  ║     🤖  JOE WHATSAPP BOT  -  INSTALLER                  ║"
echo "  ║                                                          ║"
echo "  ║     Your personal AI assistant on WhatsApp               ║"
echo "  ║                                                          ║"
echo "  ╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "  This installer will guide you through the entire setup."
echo "  No technical knowledge required!"
echo ""
echo "  ─────────────────────────────────────────────────────────"
echo ""

# Detect OS
OS="unknown"
PKG_MGR=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    if command -v brew &>/dev/null; then PKG_MGR="brew"; fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    if command -v apt &>/dev/null; then PKG_MGR="apt"
    elif command -v dnf &>/dev/null; then PKG_MGR="dnf"
    elif command -v pacman &>/dev/null; then PKG_MGR="pacman"
    fi
fi

install_pkg() {
    local pkg=$1
    local name=$2
    echo -e "  Installing ${name}..."
    if [[ "$OS" == "macos" ]]; then
        if [[ "$PKG_MGR" == "brew" ]]; then
            brew install "$pkg" 2>/dev/null || true
        else
            echo -e "  ${YELLOW}⚠️  Homebrew not found. Install Homebrew first: https://brew.sh${NC}"
            echo "  Then run: brew install $pkg"
            return 1
        fi
    elif [[ "$PKG_MGR" == "apt" ]]; then
        sudo apt update -qq && sudo apt install -y "$pkg" 2>/dev/null || true
    elif [[ "$PKG_MGR" == "dnf" ]]; then
        sudo dnf install -y "$pkg" 2>/dev/null || true
    elif [[ "$PKG_MGR" == "pacman" ]]; then
        sudo pacman -S --noconfirm "$pkg" 2>/dev/null || true
    else
        echo -e "  ${YELLOW}⚠️  Cannot install automatically. Please install $name manually.${NC}"
        return 1
    fi
}

# ============================================================
# STEP 1: Check Node.js
# ============================================================
echo -e "  ${CYAN}[Step 1/7]${NC} Checking Node.js..."
if ! command -v node &>/dev/null; then
    echo ""
    echo -e "  ${RED}❌ Node.js is NOT installed.${NC}"
    echo ""
    if [[ "$OS" == "macos" ]]; then
        install_pkg "node" "Node.js"
    elif [[ "$OS" == "linux" ]]; then
        # Try NodeSource for latest LTS
        echo "  Attempting to install Node.js 20 LTS..."
        if [[ "$PKG_MGR" == "apt" ]]; then
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>/dev/null
            sudo apt install -y nodejs 2>/dev/null
        else
            install_pkg "nodejs" "Node.js"
        fi
    fi
    if ! command -v node &>/dev/null; then
        echo -e "  ${RED}❌ Could not install Node.js.${NC}"
        echo "  Please install from: https://nodejs.org"
        exit 1
    fi
fi
NODE_VER=$(node --version)
echo -e "  ${GREEN}✅ Node.js found: ${NODE_VER}${NC}"
echo ""

# ============================================================
# STEP 2: Check Python
# ============================================================
echo -e "  ${CYAN}[Step 2/7]${NC} Checking Python..."
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
fi

if [[ -z "$PYTHON_CMD" ]]; then
    echo -e "  ${RED}❌ Python is NOT installed.${NC}"
    if [[ "$OS" == "macos" ]]; then
        install_pkg "python@3.12" "Python"
    elif [[ "$OS" == "linux" ]]; then
        install_pkg "python3" "Python"
        install_pkg "python3-venv" "Python venv"
        install_pkg "python3-pip" "pip"
    fi
    if command -v python3 &>/dev/null; then PYTHON_CMD="python3"
    elif command -v python &>/dev/null; then PYTHON_CMD="python"
    else
        echo -e "  ${RED}❌ Could not install Python.${NC}"
        echo "  Please install from: https://python.org"
        exit 1
    fi
fi
PY_VER=$($PYTHON_CMD --version 2>&1)
echo -e "  ${GREEN}✅ Python found: ${PY_VER}${NC}"
echo ""

# ============================================================
# STEP 3: Check ffmpeg
# ============================================================
echo -e "  ${CYAN}[Step 3/7]${NC} Checking ffmpeg (for voice messages)..."
if ! command -v ffmpeg &>/dev/null; then
    echo -e "  ${YELLOW}⚠️  ffmpeg is NOT installed.${NC}"
    install_pkg "ffmpeg" "ffmpeg"
    if command -v ffmpeg &>/dev/null; then
        echo -e "  ${GREEN}✅ ffmpeg installed!${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Voice messages won't work until ffmpeg is installed.${NC}"
    fi
else
    echo -e "  ${GREEN}✅ ffmpeg found!${NC}"
fi
echo ""

# ============================================================
# STEP 4: Install dependencies
# ============================================================
echo -e "  ${CYAN}[Step 4/7]${NC} Installing bot dependencies..."
echo ""
echo "  Installing Node.js packages..."
npm install --no-fund --no-audit 2>/dev/null
echo -e "  ${GREEN}✅ Node.js packages installed!${NC}"
echo ""

echo "  Creating Python virtual environment..."
if [[ ! -d ".venv" ]]; then
    $PYTHON_CMD -m venv .venv
fi
echo "  Installing Python packages..."
.venv/bin/pip install -q -r requirements.txt 2>/dev/null || true
echo -e "  ${GREEN}✅ Python packages installed!${NC}"
echo ""

# ============================================================
# STEP 5: Configuration
# ============================================================
echo "  ─────────────────────────────────────────────────────────"
echo ""
echo -e "  ${CYAN}[Step 5/7]${NC} Let's configure your bot!"
echo ""
echo "  ─────────────────────────────────────────────────────────"
echo ""

# Phone number
while true; do
    echo -e "  ${BOLD}📱 What is your WhatsApp phone number?${NC}"
    echo "     Include country code, no + or spaces."
    echo "     Example: 5511999998888 (Brazil) or 14155551234 (USA)"
    echo ""
    read -p "     Your number: " PHONE
    if [[ -n "$PHONE" ]]; then break; fi
    echo -e "     ${RED}❌ Phone number is required!${NC}"
    echo ""
done
echo -e "  ${GREEN}✅ Phone: ${PHONE}${NC}"
echo ""

# AI provider
echo -e "  ${BOLD}🧠 Which AI provider do you want to use?${NC}"
echo ""
echo "     [1] Gemini API (cloud - recommended, free tier)"
echo "     [2] Ollama (local - runs on your PC, private)"
echo "     [3] Both (best experience)"
echo ""
read -p "     Your choice (1/2/3) [1]: " AI_CHOICE
AI_CHOICE=${AI_CHOICE:-1}
echo ""

GEMINI_KEY=""
OLLAMA_URL="http://localhost:11434"
OLLAMA_MODEL="gemma2"

if [[ "$AI_CHOICE" == "1" || "$AI_CHOICE" == "3" ]]; then
    echo -e "  ${BOLD}🔑 Enter your Gemini API key.${NC}"
    echo "     Get a FREE key at: https://aistudio.google.com/apikey"
    if [[ "$OS" == "macos" ]]; then
        open "https://aistudio.google.com/apikey" 2>/dev/null || true
    elif [[ "$OS" == "linux" ]]; then
        xdg-open "https://aistudio.google.com/apikey" 2>/dev/null || true
    fi
    echo ""
    read -p "     API Key: " GEMINI_KEY
    echo ""
fi

if [[ "$AI_CHOICE" == "2" || "$AI_CHOICE" == "3" ]]; then
    echo -e "  ${BOLD}🏠 Which Ollama model?${NC}"
    echo "     [1] gemma2 (recommended)"
    echo "     [2] llama3.2"
    echo "     [3] qwen2.5"
    echo ""
    read -p "     Your choice (1/2/3) [1]: " MODEL_CHOICE
    MODEL_CHOICE=${MODEL_CHOICE:-1}
    case "$MODEL_CHOICE" in
        1) OLLAMA_MODEL="gemma2" ;;
        2) OLLAMA_MODEL="llama3.2" ;;
        3) OLLAMA_MODEL="qwen2.5" ;;
    esac
    echo -e "  ${GREEN}✅ Model: ${OLLAMA_MODEL}${NC}"
    if command -v ollama &>/dev/null; then
        echo "  Downloading model (may take a few minutes)..."
        ollama pull "$OLLAMA_MODEL" 2>/dev/null || true
    else
        echo -e "  ${YELLOW}⚠️  Ollama not installed. Get it at: https://ollama.ai${NC}"
        echo "     After installing, run: ollama pull $OLLAMA_MODEL"
    fi
    echo ""
fi

# Language
echo -e "  ${BOLD}🌍 What language should the bot speak?${NC}"
echo ""
echo "     [1] English"
echo "     [2] Português (Brasil)"
echo "     [3] Español"
echo ""
read -p "     Your choice (1/2/3) [1]: " LANG_CHOICE
LANG_CHOICE=${LANG_CHOICE:-1}

TTS_VOICE="en-US-GuyNeural"
BOT_LANG="en"
case "$LANG_CHOICE" in
    1) TTS_VOICE="en-US-GuyNeural"; BOT_LANG="en" ;;
    2) TTS_VOICE="pt-BR-AntonioNeural"; BOT_LANG="pt" ;;
    3) TTS_VOICE="es-ES-AlvaroNeural"; BOT_LANG="es" ;;
esac
echo -e "  ${GREEN}✅ Voice: ${TTS_VOICE}${NC}"
echo ""

# Bot name
echo -e "  ${BOLD}🤖 What should the bot be called?${NC} (default: Joe)"
read -p "     Bot name: " BOT_NAME
BOT_NAME=${BOT_NAME:-Joe}
echo -e "  ${GREEN}✅ Name: ${BOT_NAME}${NC}"
echo ""

# ============================================================
# STEP 6: Write config
# ============================================================
echo -e "  ${CYAN}[Step 6/7]${NC} Saving your configuration..."
echo ""

cat > .env <<EOF
# joe-whatsapp-bot configuration
# Generated by installer on $(date)

OWNER_PHONE=${PHONE}
GEMINI_API_KEY=${GEMINI_KEY}
OLLAMA_BASE_URL=${OLLAMA_URL}
OLLAMA_MODEL=${OLLAMA_MODEL}
BOT_NAME=${BOT_NAME}
USER_TITLE=
BOT_SYSTEM_PROMPT=
TTS_ENGINE=edge-tts
TTS_VOICE=${TTS_VOICE}
VOICEBOX_URL=http://127.0.0.1:17493
TRANSCRIPTION_ENGINE=gemini
TUNNEL_PORT=8080
EOF

echo -e "  ${GREEN}✅ .env created!${NC}"

cat > config.json <<EOF
{
  "bot": {
    "name": "${BOT_NAME}",
    "language": "${BOT_LANG}",
    "userTitle": "",
    "systemPrompt": ""
  },
  "agents": {
    "assistant": {
      "type": "api",
      "model": "gemini-2.5-flash",
      "description": "Cloud AI assistant"
    },
    "local": {
      "type": "local",
      "model": "${OLLAMA_MODEL}",
      "description": "Local AI for private use"
    },
    "system": {
      "type": "system",
      "description": "System commands"
    }
  },
  "agentAliases": {
    "ai": "assistant",
    "gemini": "assistant",
    "ollama": "local",
    "gemma": "local"
  },
  "monitoring": {
    "services": [
      {
        "name": "Ollama",
        "check": "http",
        "url": "http://localhost:11434",
        "description": "Local LLM server"
      }
    ]
  },
  "autoRoute": {
    "systemKeywords": ["restart", "status", "logs", "process", "service"],
    "codeKeywords": ["code", "program", "python", "javascript", "bug", "error", "script"],
    "creativeKeywords": ["analyze", "creative", "imagine", "write", "story", "poem"]
  },
  "tts": {
    "maxChars": 2000,
    "voice": "${TTS_VOICE}"
  },
  "notifications": {
    "enabled": true,
    "checkIntervalMs": 10000
  }
}
EOF

echo -e "  ${GREEN}✅ config.json created!${NC}"
echo ""

# ============================================================
# STEP 7: Launch!
# ============================================================
echo "  ─────────────────────────────────────────────────────────"
echo ""
echo -e "  ${CYAN}[Step 7/7]${NC} Everything is ready! 🎉"
echo ""
echo -e "${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════╗"
echo "  ║                                                          ║"
echo "  ║   ✅  INSTALLATION COMPLETE!                             ║"
echo "  ║                                                          ║"
echo "  ║   Your bot \"${BOT_NAME}\" is configured and ready.        "
echo "  ║                                                          ║"
echo "  ║   WHAT HAPPENS NEXT:                                     ║"
echo "  ║   1. A QR code will appear below                         ║"
echo "  ║   2. Open WhatsApp on your phone                         ║"
echo "  ║   3. Go to Settings → Linked Devices                    ║"
echo "  ║   4. Scan the QR code                                    ║"
echo "  ║   5. Send yourself a message to test!                    ║"
echo "  ║                                                          ║"
echo "  ╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
read -p "  Press Enter to start the bot..." _
echo ""
echo "  Starting ${BOT_NAME}..."
echo ""
node bot.js
