# 🗺️ Installation Map / Mapa de Instalação

> Visual guide to installing and understanding **joe-whatsapp-bot**.

---

## 1. Installation Flow / Fluxo de Instalação

```mermaid
flowchart TD
    START["🚀 Start Installation"] --> CLONE["📥 Clone or Download<br/>git clone ...joe-whatsapp-bot.git"]
    CLONE --> CHECK{"Prerequisites<br/>Installed?"}
    
    CHECK -->|"❌ No"| INSTALL_PREREQ["Install Prerequisites"]
    CHECK -->|"✅ Yes"| SETUP
    
    INSTALL_PREREQ --> NODE["📦 Install Node.js 18+<br/>nodejs.org"]
    INSTALL_PREREQ --> PYTHON["🐍 Install Python 3.10+<br/>python.org"]
    INSTALL_PREREQ --> FFMPEG["🎵 Install ffmpeg<br/>winget / apt / brew"]
    
    NODE & PYTHON & FFMPEG --> SETUP["⚙️ Run Setup Script"]
    
    SETUP --> SETUP_WIN["Windows:<br/>setup.bat"]
    SETUP --> SETUP_NIX["Linux/Mac:<br/>bash setup.sh"]
    
    SETUP_WIN & SETUP_NIX --> CONFIG["📝 Configure"]
    
    CONFIG --> ENV["Edit .env<br/>• OWNER_PHONE ✱<br/>• GEMINI_API_KEY<br/>• TTS_VOICE"]
    CONFIG --> JSON["Edit config.json<br/>• agents<br/>• monitoring<br/>• autoRoute"]
    
    ENV & JSON --> AI_CHOICE{"Choose AI Provider"}
    
    AI_CHOICE -->|"☁️ Cloud"| GEMINI["Get Gemini API Key<br/>aistudio.google.com/apikey"]
    AI_CHOICE -->|"🏠 Local"| OLLAMA["Install Ollama<br/>ollama pull gemma2"]
    AI_CHOICE -->|"Both"| BOTH["Configure both<br/>in .env"]
    
    GEMINI & OLLAMA & BOTH --> RUN["▶️ npm start"]
    
    RUN --> QR["📱 Scan QR Code<br/>WhatsApp → Linked Devices"]
    
    QR --> DONE["✅ Bot is Running!<br/>Send a message to test"]
    
    style START fill:#4CAF50,color:#fff
    style DONE fill:#4CAF50,color:#fff
    style ENV fill:#FF9800,color:#fff
    style GEMINI fill:#4285F4,color:#fff
    style OLLAMA fill:#333,color:#fff
```

---

## 2. Architecture Map / Mapa da Arquitetura

```mermaid
flowchart LR
    subgraph PHONE["📱 Your Phone"]
        WA["WhatsApp App"]
    end
    
    subgraph SERVER["💻 Your Computer"]
        subgraph NODE["Node.js Process"]
            BOT["bot.js<br/>WhatsApp Client"]
            CMD["Command Handler<br/>/status /print /link /join"]
            NOTIF["🔔 Notification<br/>Watcher"]
        end
        
        subgraph PYTHON["Python Process"]
            VR["voice_router.py<br/>AI Pipeline"]
            TRANS["🎤 Transcription"]
            ROUTE["🔀 Router"]
            EXEC["⚡ Agent Executor"]
            TTS["🔊 TTS Engine"]
        end
        
        subgraph TOOLS["🧰 Tool System"]
            WEB["🌐 Web Search"]
            FILES["📁 File Manager"]
            NOTES["📝 Notes"]
            TASKS["✅ Tasks"]
            MEM["🧠 Memory"]
        end
        
        subgraph LOCAL_AI["🏠 Local AI (Optional)"]
            OLL["Ollama Server<br/>localhost:11434"]
        end
    end
    
    subgraph CLOUD["☁️ Cloud Services"]
        GEM["Gemini API"]
        EDGE["Edge TTS"]
        CF["Cloudflare<br/>Tunnel"]
        DDG["DuckDuckGo<br/>Fallback"]
    end
    
    WA <-->|"WebSocket<br/>via Puppeteer"| BOT
    BOT -->|"Voice/Text"| VR
    VR --> TRANS --> ROUTE --> EXEC --> TTS
    VR -->|"JSON result"| BOT
    BOT --> CMD
    EXEC --> TOOLS
    
    TRANS -.->|"Primary"| GEM
    TRANS -.->|"Fallback"| OLL
    EXEC -.->|"Cloud Agent"| GEM
    EXEC -.->|"Local Agent"| OLL
    TTS -.->|"edge-tts"| EDGE
    WEB -.-> GEM
    WEB -.-> DDG
    CMD -.->|"/link"| CF
    
    style PHONE fill:#25D366,color:#fff
    style GEM fill:#4285F4,color:#fff
    style OLL fill:#333,color:#fff
    style CF fill:#F48120,color:#fff
```

---

## 3. Message Flow / Fluxo de Mensagem

```mermaid
sequenceDiagram
    actor User as 📱 User (WhatsApp)
    participant Bot as 🤖 bot.js (Node)
    participant VR as 🧠 voice_router.py
    participant AI as ☁️/🏠 AI Provider
    participant TTS as 🔊 TTS Engine
    
    User->>Bot: Send voice message 🎤
    Bot->>Bot: Download audio (base64)
    Bot->>Bot: Convert OGG → WAV (ffmpeg)
    Bot->>VR: Spawn: python voice_router.py -ja audio.wav
    
    VR->>AI: Transcribe audio
    AI-->>VR: "What's the weather today?"
    
    VR->>VR: Detect agent (auto-route)
    VR->>AI: Route to best agent
    AI-->>VR: "I don't have real-time weather data..."
    
    VR->>TTS: Synthesize speech
    TTS-->>VR: audio_response.mp3
    
    VR-->>Bot: JSON {text, response, audio_path, agent}
    
    Bot->>User: 💬 Text reply
    Bot->>User: 🔊 Audio reply (TTS)
```

```mermaid
sequenceDiagram
    actor User as 📱 User (WhatsApp)
    participant Bot as 🤖 bot.js (Node)
    participant VR as 🧠 voice_router.py
    participant Tool as 🧰 Tool System
    participant AI as ☁️ Gemini API
    
    User->>Bot: /joe search latest news about AI
    Bot->>Bot: Strip /joe prefix
    Bot->>VR: Spawn: python voice_router.py -jt "search latest..."
    
    VR->>AI: Route + Function Calling
    AI-->>VR: Call tool: web_search("latest AI news")
    VR->>Tool: Execute web_search
    Tool-->>VR: Search results
    VR->>AI: Here are the results, summarize
    AI-->>VR: "Here are the latest AI developments..."
    
    VR-->>Bot: JSON {response, agent: "assistant"}
    Bot->>User: 💬 Summary with sources
```

---

## 4. File Map / Mapa de Arquivos

```mermaid
graph TD
    ROOT["📁 joe-whatsapp-bot/"]
    
    ROOT --> ENV[".env — 🔐 Your secrets<br/>(phone, API keys)"]
    ROOT --> CONFIG["config.json — ⚙️ Bot behavior<br/>(agents, routing, monitoring)"]
    ROOT --> BOTJS["bot.js — 📱 WhatsApp client<br/>(Node.js, 678 lines)"]
    ROOT --> VRPY["voice_router.py — 🧠 AI pipeline<br/>(Python, 1124 lines)"]
    ROOT --> TOOLS_DIR["📁 tools/"]
    ROOT --> DOCS["📄 README.md, INSTALL.md<br/>LICENSE, setup scripts"]
    
    TOOLS_DIR --> AGENT["agent.py<br/>🤖 Function calling loop"]
    TOOLS_DIR --> EXECUTOR["executor.py<br/>🔀 Tool dispatcher"]
    TOOLS_DIR --> WEBSEARCH["web_search.py<br/>🌐 Internet search"]
    TOOLS_DIR --> NOTES_F["notes.py<br/>📝 Document search"]
    TOOLS_DIR --> TASKS_F["tasks.py<br/>✅ Task manager"]
    TOOLS_DIR --> MEMORY_F["memory.py<br/>🧠 Persistent memory"]
    TOOLS_DIR --> FILES_F["files.py<br/>📁 File browser"]
    TOOLS_DIR --> STATUS["status_collector.py<br/>📊 Service monitor"]
    TOOLS_DIR --> REGISTRY["registry.py<br/>📋 Tool schemas"]
    
    style ROOT fill:#333,color:#fff
    style ENV fill:#FF9800,color:#fff
    style CONFIG fill:#2196F3,color:#fff
    style BOTJS fill:#4CAF50,color:#fff
    style VRPY fill:#9C27B0,color:#fff
    style TOOLS_DIR fill:#607D8B,color:#fff
```

---

## 5. Configuration Decision Tree / Árvore de Decisão de Configuração

```mermaid
flowchart TD
    Q1{"Do you have<br/>internet access?"}
    Q1 -->|"Yes"| Q2{"Want cloud AI?<br/>(faster, smarter)"}
    Q1 -->|"No"| LOCAL_ONLY["Use Ollama only<br/>GEMINI_API_KEY=(empty)<br/>Install: ollama pull gemma2"]
    
    Q2 -->|"Yes"| Q3{"Also want<br/>local fallback?"}
    Q2 -->|"No"| LOCAL_ONLY
    
    Q3 -->|"Yes"| BOTH_AI["Use both!<br/>GEMINI_API_KEY=your-key<br/>OLLAMA_MODEL=gemma2<br/>✨ Best experience"]
    Q3 -->|"No"| CLOUD_ONLY["Gemini only<br/>GEMINI_API_KEY=your-key<br/>OLLAMA_BASE_URL=(empty)"]
    
    Q4{"Want voice<br/>responses?"}
    BOTH_AI & CLOUD_ONLY & LOCAL_ONLY --> Q4
    
    Q4 -->|"Yes"| Q5{"Have Voicebox<br/>installed?"}
    Q4 -->|"No"| NO_TTS["TTS_ENGINE=(empty)<br/>Text replies only"]
    
    Q5 -->|"Yes"| VOICEBOX["TTS_ENGINE=voicebox<br/>VOICEBOX_URL=http://..."]
    Q5 -->|"No"| EDGE["TTS_ENGINE=edge-tts<br/>TTS_VOICE=en-US-GuyNeural<br/>or pt-BR-AntonioNeural"]
    
    Q6{"Language?"}
    VOICEBOX & EDGE & NO_TTS --> Q6
    
    Q6 -->|"English"| EN["TTS_VOICE=en-US-GuyNeural<br/>config.json: language=en"]
    Q6 -->|"Português"| PT["TTS_VOICE=pt-BR-AntonioNeural<br/>config.json: language=pt"]
    Q6 -->|"Other"| OTHER["Pick a voice from<br/>edge-tts voice list"]
    
    EN & PT & OTHER --> READY["✅ You're ready!<br/>npm start"]
    
    style BOTH_AI fill:#4CAF50,color:#fff
    style READY fill:#4CAF50,color:#fff
    style LOCAL_ONLY fill:#333,color:#fff
    style CLOUD_ONLY fill:#4285F4,color:#fff
```

---

## 6. Port & Service Map / Mapa de Portas e Serviços

| Port | Service | Required | Configured In |
|------|---------|----------|--------------|
| — | WhatsApp (WebSocket via Puppeteer) | ✅ Always | Automatic |
| 11434 | Ollama (local LLM) | If using local AI | `.env` → `OLLAMA_BASE_URL` |
| 17493 | Voicebox (TTS/STT) | If using Voicebox | `.env` → `VOICEBOX_URL` |
| 8080 | Tunnel target (your app) | If using `/link` | `.env` → `TUNNEL_PORT` |
| 9222 | Chrome DevTools (Puppeteer debug) | Never (internal) | Automatic |

---

## 7. Quick Reference Card / Cartão de Referência Rápida

```
┌─────────────────────────────────────────────────────┐
│                 joe-whatsapp-bot                     │
│              Quick Reference Card                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  INSTALL:                                           │
│    git clone → cd → setup.bat → edit .env → npm start │
│                                                     │
│  REQUIRED ENV:                                      │
│    OWNER_PHONE=5511999998888                        │
│                                                     │
│  COMMANDS:                                          │
│    /status     Check services                       │
│    /print      Screenshot a page                    │
│    /link       Create public tunnel                 │
│    /join URL   Join WhatsApp group                  │
│    /joe MSG    Talk to bot in groups                │
│    @agent MSG  Direct to specific agent             │
│                                                     │
│  FILES:                                             │
│    .env           → Secrets & keys                  │
│    config.json    → Bot behavior                    │
│    bot.js         → WhatsApp client                 │
│    voice_router.py→ AI pipeline                     │
│    tools/         → Extensible tools                │
│                                                     │
│  AI PROVIDERS:                                      │
│    Cloud: GEMINI_API_KEY=AIza...                    │
│    Local: ollama pull gemma2                        │
│                                                     │
│  VOICE (PT-BR): TTS_VOICE=pt-BR-AntonioNeural      │
│  VOICE (EN-US): TTS_VOICE=en-US-GuyNeural          │
│                                                     │
└─────────────────────────────────────────────────────┘
```
