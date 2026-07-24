# 📖 Installation Manual / Manual de Instalação

> **joe-whatsapp-bot** — Complete step-by-step guide for every operating system.

[English](#-installation-guide-english) | [Português](#-guia-de-instalação-português)

---

# 🇺🇸 Installation Guide (English)

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Getting the Project](#2-getting-the-project)
3. [Installing Dependencies](#3-installing-dependencies)
4. [Configuration](#4-configuration)
5. [First Run](#5-first-run)
6. [Connecting WhatsApp](#6-connecting-whatsapp)
7. [Testing the Bot](#7-testing-the-bot)
8. [Optional Setup](#8-optional-setup)
9. [Running as a Service](#9-running-as-a-service)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prerequisites

You need these installed before proceeding:

### Required

| Software | Minimum Version | How to Install | How to Verify |
|----------|----------------|----------------|---------------|
| **Node.js** | 18.0+ | [nodejs.org](https://nodejs.org) → Download LTS | `node --version` |
| **Python** | 3.10+ | [python.org](https://python.org) → Download | `python --version` |
| **ffmpeg** | Any | See below | `ffmpeg -version` |

### Installing ffmpeg

**Windows:**
```powershell
# Option A: Using winget (recommended)
winget install Gyan.FFmpeg

# Option B: Using choco
choco install ffmpeg

# Option C: Manual — download from https://ffmpeg.org/download.html, extract, add bin/ to PATH
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### At Least ONE AI Provider

| Provider | Type | Cost | How to Get |
|----------|------|------|------------|
| **Gemini API** | Cloud | Free tier available | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| **Ollama** | Local | Free (runs on your PC) | [ollama.ai](https://ollama.ai) → Install, then `ollama pull gemma2` |

> **Tip:** You can use both! Gemini handles cloud requests, Ollama handles offline/private requests. The bot falls back automatically.

### Optional

| Software | Purpose | How to Install |
|----------|---------|----------------|
| **cloudflared** | `/link` command (public tunnels) | `winget install Cloudflare.cloudflared` or [download](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) |
| **Ollama models** | More local AI options | `ollama pull llama3.2` or `ollama pull qwen2.5` |

---

## 2. Getting the Project

### Option A: Clone from GitHub
```bash
git clone https://github.com/RodDu/joe-whatsapp-bot.git
cd joe-whatsapp-bot
```

### Option B: Download ZIP
1. Go to the GitHub repository page
2. Click **Code** → **Download ZIP**
3. Extract to any folder on your machine
4. Open a terminal in that folder

---

## 3. Installing Dependencies

### Automatic (Recommended)

**Windows:**
```
setup.bat
```

**Linux / macOS:**
```bash
chmod +x setup.sh
bash setup.sh
```

The setup script will:
- ✅ Verify Node.js and Python are installed
- ✅ Run `npm install` (Node.js dependencies)
- ✅ Create a Python virtual environment (`.venv/`)
- ✅ Install Python packages (`requirements.txt`)
- ✅ Copy config templates if they don't exist

### Manual Installation

If you prefer to do it yourself:

```bash
# 1. Install Node.js dependencies
npm install

# 2. Create Python virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Copy config templates
cp .env.example .env
cp config.example.json config.json
```

---

## 4. Configuration

### Step 4.1: Edit `.env` (Required)

Open `.env` in any text editor and fill in the values:

```ini
# REQUIRED — Your WhatsApp phone number (country code + number, no +/spaces/dashes)
# Examples: 5511999998888 (Brazil), 14155551234 (USA), 447911123456 (UK)
OWNER_PHONE=5511999998888

# RECOMMENDED — Get a free key at https://aistudio.google.com/apikey
GEMINI_API_KEY=AIzaSy...your-key-here
```

> ⚠️ **OWNER_PHONE is mandatory.** The bot will refuse to start without it.

#### All `.env` Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OWNER_PHONE` | **Yes** | — | Your WhatsApp number with country code |
| `GEMINI_API_KEY` | No* | — | Gemini API key (free at Google AI Studio) |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | No | `gemma2` | Default Ollama model |
| `BOT_NAME` | No | `Joe` | How the bot refers to itself |
| `USER_TITLE` | No | *(empty)* | How the bot addresses you (e.g., "Sir", "Boss") |
| `BOT_SYSTEM_PROMPT` | No | *(default)* | Custom personality prompt |
| `TTS_ENGINE` | No | `edge-tts` | TTS engine: `edge-tts` or `voicebox` |
| `TTS_VOICE` | No | `en-US-GuyNeural` | Voice for edge-tts |
| `VOICEBOX_URL` | No | `http://127.0.0.1:17493` | Voicebox server URL |
| `TRANSCRIPTION_ENGINE` | No | `gemini` | Engine: `gemini`, `voicebox`, or `whisper` |
| `TUNNEL_PORT` | No | `8080` | Port for `/link` tunnel |

*\* Either `GEMINI_API_KEY` or a running Ollama instance is required for AI features.*

### Step 4.2: Edit `config.json` (Optional)

The default `config.json` works out of the box. Customize if you want to:

#### Add services to monitor (`/status` command)
```json
"monitoring": {
  "services": [
    {
      "name": "Ollama",
      "check": "http",
      "url": "http://localhost:11434",
      "description": "Local LLM server"
    },
    {
      "name": "My Web App",
      "check": "http",
      "url": "http://localhost:3000",
      "description": "My development server"
    }
  ]
}
```

#### Add custom agents
```json
"agents": {
  "assistant": {
    "type": "api",
    "model": "gemini-2.5-flash",
    "description": "Cloud AI for general use"
  },
  "coder": {
    "type": "local",
    "model": "qwen2.5-coder",
    "description": "Local code assistant"
  },
  "writer": {
    "type": "local",
    "model": "llama3.2",
    "description": "Creative writing assistant"
  }
}
```

#### Add agent aliases (voice shortcuts)
```json
"agentAliases": {
  "ai": "assistant",
  "gemini": "assistant",
  "coder": "coder",
  "code": "coder",
  "writer": "writer"
}
```

---

## 5. First Run

```bash
npm start
```

You should see output like:
```
[SYSTEM] WhatsApp Bot client initialized.
[SYSTEM] Notification watcher active (every 10s).
[QR_CODE] New QR Code generated.

============================================================
SCAN THE QR CODE BELOW WITH YOUR PHONE IN WHATSAPP:
============================================================

▄▄▄▄▄▄▄ ▄▄▄ ▄▄  ▄▄▄▄▄▄▄
█ ▄▄▄ █ ▀█▀██▀█  █ ▄▄▄ █
...

============================================================
```

---

## 6. Connecting WhatsApp

1. Open **WhatsApp** on your phone
2. Go to **Settings** → **Linked Devices**
3. Tap **Link a Device**
4. Point your phone camera at the QR code in the terminal
5. Wait for the bot to authenticate — you'll see:
   ```
   [AUTH] Authentication successful!
   [SYSTEM] WhatsApp Bot is ready and connected!
   ```

> 📱 **First time only.** After the initial scan, the session is saved locally in `.wwebjs_auth/`. You won't need to scan again unless you log out or delete that folder.

---

## 7. Testing the Bot

### Test 1: Self-chat
Send a text message **to yourself** on WhatsApp. The bot monitors your self-chat.

### Test 2: Commands
Try these in your self-chat:

| Send this | Expected response |
|-----------|-------------------|
| `/status` | List of service statuses with 🟢/🔴 indicators |
| `Hello, how are you?` | AI-generated response from configured agent |
| `/joe What's the weather?` | AI response (works in groups too) |

### Test 3: Voice message
Send a voice message to yourself. The bot should:
1. Transcribe it
2. Route to the best AI agent
3. Reply with text + TTS audio

---

## 8. Optional Setup

### 8.1 Using Ollama (Local AI)

```bash
# Install Ollama
# Windows: winget install Ollama.Ollama
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull gemma2

# Verify it's running
curl http://localhost:11434
```

Then in `.env`:
```ini
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2
```

### 8.2 Using Cloudflare Tunnel (`/link`)

```bash
# Windows
winget install Cloudflare.cloudflared

# macOS
brew install cloudflared

# Linux
# See: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
```

The `/link` command will create a temporary public URL that tunnels to `localhost:TUNNEL_PORT`.

### 8.3 Brazilian Portuguese Voices (edge-tts)

For PT-BR voice responses, set in `.env`:
```ini
TTS_VOICE=pt-BR-AntonioNeural
```

Other popular voices:
- `pt-BR-FranciscaNeural` (female, Brazilian)
- `en-US-JennyNeural` (female, American English)
- `en-GB-SoniaNeural` (female, British English)
- `es-ES-ElviraNeural` (female, Spanish)

---

## 9. Running as a Service

### Windows (Task Scheduler)
1. Open **Task Scheduler**
2. Create a new task → **Run at startup**
3. Action: `node` with arguments `bot.js`
4. Working directory: your project folder

### Linux (systemd)
```ini
# /etc/systemd/system/joe-bot.service
[Unit]
Description=Joe WhatsApp Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/joe-whatsapp-bot
ExecStart=/usr/bin/node bot.js
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable joe-bot
sudo systemctl start joe-bot
```

### macOS (launchd)
```xml
<!-- ~/Library/LaunchAgents/com.joe.whatsapp-bot.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.joe.whatsapp-bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/node</string>
        <string>bot.js</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/joe-whatsapp-bot</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

---

## 10. Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `OWNER_PHONE not defined` | Missing `.env` | Copy `.env.example` to `.env`, fill `OWNER_PHONE` |
| No QR Code appears | Puppeteer issue | Run `npm install` again; check Node.js version ≥18 |
| QR scanned but bot disconnects | Session conflict | Delete `.wwebjs_auth/` folder, restart, scan again |
| Voice messages not working | ffmpeg missing | Install ffmpeg and ensure it's in PATH |
| `ModuleNotFoundError: edge_tts` | Python deps missing | Activate `.venv` and run `pip install -r requirements.txt` |
| Bot ignores messages | Wrong phone number | Check `OWNER_PHONE` matches your WhatsApp number exactly |
| Gemini API errors | Invalid API key | Verify key at [aistudio.google.com](https://aistudio.google.com) |
| Ollama not responding | Service not running | Start with `ollama serve` or check URL in `.env` |
| `/link` fails | cloudflared missing | Install cloudflared (see Optional Setup) |
| `/print` returns error | No web server | The `/print` command needs a running web page to screenshot |
| Python not found by bot | PATH issue | Ensure Python is in PATH, or create `.venv` in the project folder |

---

---

# 🇧🇷 Guia de Instalação (Português)

## Índice
1. [Pré-requisitos](#1-pré-requisitos)
2. [Obtendo o Projeto](#2-obtendo-o-projeto)
3. [Instalando Dependências](#3-instalando-dependências)
4. [Configuração](#4-configuração-1)
5. [Primeira Execução](#5-primeira-execução)
6. [Conectando o WhatsApp](#6-conectando-o-whatsapp)
7. [Testando o Bot](#7-testando-o-bot)
8. [Configurações Opcionais](#8-configurações-opcionais)
9. [Rodando como Serviço](#9-rodando-como-serviço)
10. [Solução de Problemas](#10-solução-de-problemas)

---

## 1. Pré-requisitos

### Obrigatórios

| Software | Versão Mínima | Como Instalar | Como Verificar |
|----------|--------------|---------------|----------------|
| **Node.js** | 18.0+ | [nodejs.org](https://nodejs.org) → Baixe LTS | `node --version` |
| **Python** | 3.10+ | [python.org](https://python.org) → Baixe | `python --version` |
| **ffmpeg** | Qualquer | Veja abaixo | `ffmpeg -version` |

### Instalando ffmpeg

**Windows:**
```powershell
# Opção A: Via winget (recomendado)
winget install Gyan.FFmpeg

# Opção B: Via chocolatey
choco install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### Pelo menos UM provedor de IA

| Provedor | Tipo | Custo | Como Obter |
|----------|------|-------|------------|
| **Gemini API** | Nuvem | Grátis (tier gratuito) | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| **Ollama** | Local | Grátis (roda no seu PC) | [ollama.ai](https://ollama.ai) → Instale, depois `ollama pull gemma2` |

> **Dica:** Você pode usar os dois! O Gemini responde requisições na nuvem, o Ollama lida com consultas offline/privadas. O bot faz fallback automaticamente.

---

## 2. Obtendo o Projeto

```bash
git clone https://github.com/RodDu/joe-whatsapp-bot.git
cd joe-whatsapp-bot
```

Ou baixe o ZIP pela página do GitHub → **Code** → **Download ZIP**.

---

## 3. Instalando Dependências

**Windows:** Execute `setup.bat`

**Linux / macOS:** Execute `bash setup.sh`

**Ou manualmente:**
```bash
npm install
python -m venv .venv

# Windows:
.venv\Scripts\pip install -r requirements.txt

# Linux/macOS:
.venv/bin/pip install -r requirements.txt

cp .env.example .env
cp config.example.json config.json
```

---

## 4. Configuração

### Passo 4.1: Editar `.env` (Obrigatório)

```ini
# OBRIGATÓRIO — Seu número do WhatsApp (código do país + número, sem +/espaços/traços)
OWNER_PHONE=5567841XXXXX

# RECOMENDADO — Chave gratuita em https://aistudio.google.com/apikey
GEMINI_API_KEY=AIzaSy...sua-chave-aqui
```

#### Tabela Completa de Variáveis

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `OWNER_PHONE` | **Sim** | — | Seu número WhatsApp com código do país |
| `GEMINI_API_KEY` | Não* | — | Chave da API Gemini |
| `OLLAMA_BASE_URL` | Não | `http://localhost:11434` | URL do servidor Ollama |
| `OLLAMA_MODEL` | Não | `gemma2` | Modelo padrão do Ollama |
| `BOT_NAME` | Não | `Joe` | Como o bot se chama |
| `USER_TITLE` | Não | *(vazio)* | Como o bot te chama (ex: "Senhor", "Chefe") |
| `TTS_ENGINE` | Não | `edge-tts` | Motor TTS: `edge-tts` ou `voicebox` |
| `TTS_VOICE` | Não | `en-US-GuyNeural` | Voz (use `pt-BR-AntonioNeural` para PT-BR) |
| `TRANSCRIPTION_ENGINE` | Não | `gemini` | Motor: `gemini`, `voicebox` ou `whisper` |
| `TUNNEL_PORT` | Não | `8080` | Porta para o túnel do `/link` |

*\* `GEMINI_API_KEY` ou uma instância Ollama rodando é necessária para as funções de IA.*

### Passo 4.2: Voz em Português

Para respostas em áudio PT-BR, altere no `.env`:
```ini
TTS_VOICE=pt-BR-AntonioNeural
```

---

## 5. Primeira Execução

```bash
npm start
```

Você verá um QR Code no terminal.

---

## 6. Conectando o WhatsApp

1. Abra o **WhatsApp** no celular
2. Vá em **Configurações** → **Aparelhos Conectados**
3. Toque em **Conectar um Aparelho**
4. Aponte a câmera para o QR Code no terminal
5. Aguarde a autenticação — você verá:
   ```
   [AUTH] Authentication successful!
   [SYSTEM] WhatsApp Bot is ready and connected!
   ```

> 📱 **Apenas na primeira vez.** Depois do scan inicial, a sessão fica salva em `.wwebjs_auth/`. Não será necessário escanear de novo, a menos que você desconecte ou delete essa pasta.

---

## 7. Testando o Bot

| Envie isso | Resposta esperada |
|-----------|-------------------|
| `/status` | Lista de status dos serviços com 🟢/🔴 |
| `Olá, tudo bem?` | Resposta gerada por IA |
| Mensagem de voz | Transcrição + resposta em texto + áudio TTS |

---

## 8. Configurações Opcionais

### 8.1 Usando Ollama (IA Local)

```bash
# Instalar Ollama (Windows)
winget install Ollama.Ollama

# Baixar um modelo
ollama pull gemma2

# Verificar se está rodando
curl http://localhost:11434
```

### 8.2 Cloudflare Tunnel (comando `/link`)

```bash
winget install Cloudflare.cloudflared
```

---

## 9. Rodando como Serviço

### Windows (Agendador de Tarefas)
1. Abra o **Agendador de Tarefas**
2. Crie uma nova tarefa → **Executar na inicialização**
3. Ação: `node` com argumentos `bot.js`
4. Diretório de trabalho: pasta do projeto

### Linux (systemd)
```bash
# Crie /etc/systemd/system/joe-bot.service (veja exemplo na seção em inglês)
sudo systemctl enable joe-bot
sudo systemctl start joe-bot
```

---

## 10. Solução de Problemas

| Problema | Causa | Solução |
|----------|-------|---------|
| `OWNER_PHONE not defined` | `.env` ausente | Copie `.env.example` para `.env` e preencha |
| QR Code não aparece | Problema no Puppeteer | Execute `npm install` novamente |
| Mensagens de voz falham | ffmpeg ausente | Instale o ffmpeg e garanta que está no PATH |
| Bot ignora mensagens | Número errado | Confira se `OWNER_PHONE` confere com seu WhatsApp |
| Erros do Gemini | Chave inválida | Verifique em [aistudio.google.com](https://aistudio.google.com) |
| Ollama não responde | Serviço parado | Inicie com `ollama serve` |
