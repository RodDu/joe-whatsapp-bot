<🤖 Joe WhatsApp Bot>
> Your personal AI assistant on WhatsApp — voice & text, powered by Gemini and Ollama.

[English](#english) | [Português](#português)

---

## English

### Features
- 🎙️ **Voice messages:** Send a voice note, the bot transcribes it, queries the AI, and replies with TTS audio!
- 💬 **Text commands & AI Routing:** Smart routing to the best agent (e.g., local Ollama for privacy, cloud Gemini for coding).
- 🧠 **Multi-agent system:** Cloud AI via Gemini API and Local AI via Ollama.
- ⚙️ **/status:** Quickly check system services and their health directly in the chat.
- 📸 **/print:** Capture a screenshot of any local or remote web page.
- 🌐 **/link:** Create a temporary public URL via Cloudflare Tunnel.
- 🤝 **/join:** Automatically join WhatsApp groups by providing an invite link.
- 🔔 **Notification watcher:** External apps can send notifications through the bot to your WhatsApp.
- 🧰 **Extensible tool system:** Add capabilities like web search, file management, notes, tasks, and memory.
- 🖥️ **Cross-platform:** Works flawlessly on Windows, Linux, and macOS.

### Prerequisites
- Node.js 18+ (https://nodejs.org)
- Python 3.10+ (https://python.org)
- ffmpeg (required for audio/voice message conversion)
- At least ONE of:
  - Gemini API key (Free at [Google AI Studio](https://aistudio.google.com/apikey))
  - Ollama installed locally ([Ollama](https://ollama.ai))
- Optional: `cloudflared` (for the `/link` command to create tunnels)

### Quick Start
1. Clone the repository: `git clone https://github.com/RodDu/joe-whatsapp-bot.git`
2. Navigate into the directory: `cd joe-whatsapp-bot`
3. Run the setup script for your OS:
   - Windows: Run `setup.bat`
   - Linux/macOS: Run `bash setup.sh`
   *(Alternatively, run `npm install` and `pip install -r requirements.txt` manually)*
4. Copy `.env.example` to `.env` and fill in your values:
   - `OWNER_PHONE` is required (your WhatsApp number with country code, e.g., `5511999998888`).
   - Add your `GEMINI_API_KEY` or configure `OLLAMA_BASE_URL`.
5. Copy `config.example.json` to `config.json` and customize it to your liking.
6. Start the bot: `npm start`
7. Scan the QR code displayed in your terminal using the "Linked Devices" option in your WhatsApp app.
8. Send a message to yourself to test, or use the `/joe` prefix in groups!

### Configuration
The bot relies on two main configuration files:

#### `.env` - Environment Variables
- `OWNER_PHONE`: Your phone number with country code (no `+`, spaces, or dashes). Required.
- `GEMINI_API_KEY`: Your Google AI Studio API key.
- `OLLAMA_BASE_URL` & `OLLAMA_MODEL`: Settings for your local Ollama instance (default `http://localhost:11434` and `gemma2`).
- `BOT_NAME`, `USER_TITLE`, `BOT_SYSTEM_PROMPT`: Personalize how the bot identifies itself and you.
- `TTS_ENGINE`, `TTS_VOICE`, `VOICEBOX_URL`: Configure Text-to-Speech settings (using `edge-tts` or local `voicebox`).
- `TRANSCRIPTION_ENGINE`: Choose between `gemini`, `voicebox`, or `whisper`.
- `TUNNEL_PORT`: Port exposed when using the `/link` command.

#### `config.json` - Bot Logic
- `bot`: General info like bot name and language.
- `agents`: Define available AI models (`assistant` using Gemini, `local` using Ollama, `system` for bot commands).
- `agentAliases`: Shortcuts to call specific agents (e.g., calling `@gemini` routes to the `assistant` agent).
- `monitoring`: Services to check when you run the `/status` command.
- `autoRoute`: Keywords that dictate which agent handles a message automatically.
- `tts`: Character limits and voice selection.
- `notifications`: Manage external notification watching.

### Commands
| Command | Description |
|---|---|
| `@agent [msg]` | Direct a message to a specific agent (e.g., `@ollama hello`). |
| `/status` | Check the health of configured local services (e.g., Ollama). |
| `/print [url]` | Take a screenshot of the specified webpage and send it back. |
| `/link` | Start a Cloudflare Tunnel and return a public link. |
| `/join [link]` | Join a WhatsApp group using an invite link. |
| `/joe [msg]` | Explicitly talk to the bot in group chats (to avoid it responding to everything). |

### Architecture
The main Node.js process (`bot.js`) handles the WhatsApp connection using `whatsapp-web.js`. When a voice message arrives or AI processing is needed, the bot spawns a Python script (`voice_router.py` ou similar). Python handles the heavy lifting (transcription via Whisper/Gemini, AI inference routing, and TTS via Edge-TTS) and returns the result back to Node.js, which sends the final text or audio back to WhatsApp.

### Extending with Tools
The tool system is modular! You can add new capabilities (like checking weather, reading files, searching the web).
1. Create a new module inside the `tools/` directory.
2. Define the tool schema and execution logic.
3. Register the tool in the main agent configuration.
When the AI decides it needs to perform an action, it will execute your tool and use the returned data to reply.

### Troubleshooting
- **No QR Code appears:** Ensure `npm install` finished successfully and Puppeteer was installed. Check your internet connection.
- **Node/Python errors on startup:** Verify you are running Node.js 18+ and Python 3.10+.
- **FFmpeg not found:** You must install FFmpeg and add it to your system PATH for audio conversion to work.
- **Bot ignores me:** Check if the `OWNER_PHONE` in `.env` exactly matches your WhatsApp number.
- **Voice messages fail:** Ensure your `TRANSCRIPTION_ENGINE` is configured properly. If using `gemini`, ensure you have a valid API key.

---

## Português

### Funcionalidades
- 🎙️ **Mensagens de voz:** Envie um áudio, o bot transcreve, consulta a IA e responde com outro áudio TTS!
- 💬 **Comandos de texto e Roteamento:** Roteamento inteligente para o melhor agente (ex: Ollama local para privacidade, Gemini na nuvem para código).
- 🧠 **Sistema multi-agentes:** IA na nuvem via API do Gemini e IA local via Ollama.
- ⚙️ **/status:** Verifique rapidamente a integridade dos serviços do sistema diretamente no chat.
- 📸 **/print:** Capture a tela (screenshot) de qualquer página web local ou remota.
- 🌐 **/link:** Crie uma URL pública temporária via Cloudflare Tunnel.
- 🤝 **/join:** Entre automaticamente em grupos do WhatsApp enviando um link de convite.
- 🔔 **Observador de notificações:** Aplicativos externos podem enviar notificações através do bot para o seu WhatsApp.
- 🧰 **Sistema de ferramentas extensível:** Adicione capacidades como pesquisa na web, gerenciamento de arquivos, notas, tarefas e memória.
- 🖥️ **Multiplataforma:** Funciona perfeitamente no Windows, Linux e macOS.

### Pré-requisitos
- Node.js 18+ (https://nodejs.org)
- Python 3.10+ (https://python.org)
- ffmpeg (necessário para a conversão de áudio/voz)
- Pelo menos UM dos seguintes:
  - Chave de API do Gemini (Gratuita no [Google AI Studio](https://aistudio.google.com/apikey))
  - Ollama instalado localmente ([Ollama](https://ollama.ai))
- Opcional: `cloudflared` (para o comando `/link` criar túneis)

### Início Rápido
1. Clone o repositório: `git clone https://github.com/RodDu/joe-whatsapp-bot.git`
2. Entre no diretório: `cd joe-whatsapp-bot`
3. Execute o script de configuração para o seu SO:
   - Windows: Execute `setup.bat`
   - Linux/macOS: Execute `bash setup.sh`
   *(Ou execute `npm install` e `pip install -r requirements.txt` manualmente)*
4. Copie `.env.example` para `.env` e preencha seus valores:
   - `OWNER_PHONE` é obrigatório (seu número do WhatsApp com código do país, ex: `5511999998888`).
   - Adicione sua `GEMINI_API_KEY` ou configure `OLLAMA_BASE_URL`.
5. Copie `config.example.json` para `config.json` e personalize como quiser.
6. Inicie o bot: `npm start`
7. Escaneie o código QR exibido no terminal usando a opção "Aparelhos Conectados" no seu aplicativo do WhatsApp.
8. Envie uma mensagem para você mesmo para testar, ou use o prefixo `/joe` em grupos!

### Configuração
O bot depende de dois arquivos principais de configuração:

#### `.env` - Variáveis de Ambiente
- `OWNER_PHONE`: Seu número de telefone com o código do país (sem `+`, espaços ou traços). Obrigatório.
- `GEMINI_API_KEY`: Sua chave de API do Google AI Studio.
- `OLLAMA_BASE_URL` & `OLLAMA_MODEL`: Configurações do seu Ollama local (padrão `http://localhost:11434` e `gemma2`).
- `BOT_NAME`, `USER_TITLE`, `BOT_SYSTEM_PROMPT`: Personalize como o bot se identifica e como ele te chama.
- `TTS_ENGINE`, `TTS_VOICE`, `VOICEBOX_URL`: Configure o Text-to-Speech (usando `edge-tts` ou `voicebox` local).
- `TRANSCRIPTION_ENGINE`: Escolha entre `gemini`, `voicebox` ou `whisper`.
- `TUNNEL_PORT`: Porta exposta ao usar o comando `/link`.

#### `config.json` - Lógica do Bot
- `bot`: Informações gerais como nome e idioma do bot.
- `agents`: Define os modelos de IA disponíveis (`assistant` usando Gemini, `local` usando Ollama, `system` para comandos).
- `agentAliases`: Atalhos para chamar agentes específicos (ex: `@gemini` vai para o agente `assistant`).
- `monitoring`: Serviços a serem verificados quando você usa o comando `/status`.
- `autoRoute`: Palavras-chave que decidem qual agente processa a mensagem automaticamente.
- `tts`: Limite de caracteres e seleção de voz.
- `notifications`: Gerencia a verificação de notificações externas.

### Comandos
| Comando | Descrição |
|---|---|
| `@agente [msg]` | Direciona uma mensagem para um agente específico (ex: `@ollama oi`). |
| `/status` | Verifica a saúde dos serviços locais (ex: Ollama). |
| `/print [url]` | Tira um print (screenshot) de uma página web e envia a imagem. |
| `/link` | Inicia um Cloudflare Tunnel e retorna um link público. |
| `/join [link]` | Entra em um grupo do WhatsApp usando um link de convite. |
| `/joe [msg]` | Fala explicitamente com o bot em grupos (para que ele não responda a tudo). |

### Arquitetura
O processo principal em Node.js (`bot.js`) gerencia a conexão do WhatsApp usando `whatsapp-web.js`. Quando um áudio chega ou processamento de IA é necessário, o bot invoca um script Python (`voice_router.py` ou similar). O Python faz o trabalho pesado (transcrição via Whisper/Gemini, roteamento de IA e TTS via Edge-TTS) e retorna o resultado para o Node.js, que envia o texto ou áudio final de volta ao WhatsApp.

### Estendendo com Ferramentas
O sistema de ferramentas é modular! Você pode adicionar novas capacidades (como previsão do tempo, ler arquivos, buscar na web).
1. Crie um novo módulo dentro do diretório `tools/`.
2. Defina o esquema da ferramenta e a lógica de execução.
3. Registre a ferramenta na configuração do agente principal.
Quando a IA decidir que precisa agir, ela executará sua ferramenta e usará os dados para responder.

### Solução de Problemas
- **Nenhum QR Code aparece:** Confirme se o `npm install` terminou sem erros e se o Puppeteer foi instalado. Verifique sua internet.
- **Erros de Node/Python ao iniciar:** Certifique-se de que está rodando Node.js 18+ e Python 3.10+.
- **FFmpeg não encontrado:** Você deve instalar o FFmpeg e adicioná-lo ao PATH do sistema para a conversão de áudio funcionar.
- **Bot me ignora:** Verifique se o `OWNER_PHONE` no `.env` corresponde exatamente ao seu número do WhatsApp.
- **Mensagens de voz falham:** Verifique se seu `TRANSCRIPTION_ENGINE` está configurado corretamente. Se usar `gemini`, garanta que a chave da API é válida.

---

## Disclaimer
This bot uses whatsapp-web.js which is an unofficial WhatsApp API. Use at your own risk. This project is for personal use only. Do not use for spam or unauthorized messaging.

## License
MIT
