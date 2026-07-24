require('dotenv').config();
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const puppeteer = require('puppeteer');
const { exec, spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Initialize log to file with size limit
const logPath = path.join(__dirname, 'bot.log');
function logText(type, text) {
    const timestamp = new Date().toLocaleString('pt-BR');
    const logLine = `[${timestamp}] [${type}] ${text}\n`;
    try {
        if (fs.existsSync(logPath)) {
            const stats = fs.statSync(logPath);
            if (stats.size > 10 * 1024 * 1024) {
                try {
                    fs.renameSync(logPath, logPath + '.old');
                } catch (renameErr) {
                    fs.writeFileSync(logPath, ''); // Fallback
                }
            }
        }
        fs.appendFileSync(logPath, logLine);
    } catch (err) {
        try {
            console.error('Falha ao escrever no arquivo de log:', err);
        } catch (consoleErr) {}
    }
    try {
        console.log(`[${type}] ${text}`);
    } catch (consoleErr) {}
}

const OWN_PHONE = process.env.OWNER_PHONE;
if (!OWN_PHONE) {
    logText('CRASH', 'ERRO: OWNER_PHONE não definido no .env');
    process.exit(1);
}

// Variables & Control
let activeTunnelProcess = null;
let activeTunnelUrl = null;
const sentByBot = new Set();
let botReady = false;

// Dynamic JIDs
const ownJids = new Set([
    `${OWN_PHONE}@c.us`
]);

function loadConfig() {
    let config = {};
    const configPath = path.join(__dirname, 'config.json');
    const examplePath = path.join(__dirname, 'config.example.json');
    try {
        if (fs.existsSync(configPath)) {
            config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
        } else if (fs.existsSync(examplePath)) {
            config = JSON.parse(fs.readFileSync(examplePath, 'utf-8'));
        }
    } catch (e) {
        logText('CONFIG_WARN', `Erro ao ler configurações: ${e.message}`);
    }
    return config;
}

// Check Python Path
function getPythonPath() {
    const winVenv = path.join(__dirname, '.venv', 'Scripts', 'python.exe');
    const unixVenv = path.join(__dirname, '.venv', 'bin', 'python');
    if (fs.existsSync(winVenv)) return winVenv;
    if (fs.existsSync(unixVenv)) return unixVenv;
    try {
        execSync('python3 --version');
        return 'python3';
    } catch {
        return 'python';
    }
}

// Wrapper for responding to messages
async function botReply(msg, text, options = {}) {
    try {
        const response = await msg.reply(text, options);
        if (response && response.id) {
            sentByBot.add(response.id._serialized);
        }
        return response;
    } catch (err) {
        logText('REPLY_WARN', `Falha ao usar msg.reply, usando client.sendMessage como fallback.`);
        try {
            const isGroup = msg.from && msg.from.endsWith('@g.us');
            const chatId = isGroup ? msg.from : `${OWN_PHONE}@c.us`;
            const response = await client.sendMessage(chatId, text, options);
            if (response && response.id) {
                sentByBot.add(response.id._serialized);
            }
            return response;
        } catch (err2) {
            logText('REPLY_ERROR', `Erro critico ao enviar resposta por fallback: ${err2.message}`);
        }
    }
}

// Wrapper for sending general messages
async function botSendMessage(chatId, content, options = {}) {
    try {
        const response = await client.sendMessage(chatId, content, options);
        if (response && response.id) {
            sentByBot.add(response.id._serialized);
        }
        return response;
    } catch (err) {
        logText('SEND_ERROR', `Erro ao enviar mensagem: ${err.message}`);
    }
}

// Helper to run synchronous commands
function runCommand(cmd) {
    return new Promise((resolve, reject) => {
        exec(cmd, (error, stdout, stderr) => {
            if (error) {
                logText('ERROR_CMD', `Erro ao rodar comando: ${cmd} | ${error.message}`);
                reject(error);
            } else {
                resolve(stdout);
            }
        });
    });
}

// Helper for cross-platform process check
function checkProcess(commandLineKeyword) {
    return new Promise((resolve) => {
        if (os.platform() === 'win32') {
            const cmd = `powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-CimInstance -ClassName Win32_Process -Filter \\"Name = 'python.exe' and CommandLine like '%${commandLineKeyword}%'\\") { exit 0 } else { exit 1 }"`;
            exec(cmd, (error) => resolve(!error));
        } else {
            const cmd = `ps aux | grep -v grep | grep "${commandLineKeyword}"`;
            exec(cmd, (error, stdout) => {
                if (error || !stdout.trim()) {
                    resolve(false);
                } else {
                    resolve(true);
                }
            });
        }
    });
}

// Initialize WhatsApp Client
const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: path.join(__dirname, '.wwebjs_auth')
    }),
    webVersionCache: {
        type: 'remote',
        remotePath: 'https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2412.54.html'
    },
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1280,800',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            '--remote-debugging-port=9222'
        ],
        defaultViewport: { width: 1280, height: 800 }
    }
});

client.on('qr', (qr) => {
    logText('QR_CODE', 'Novo QR Code gerado.');
    console.log('\n============================================================');
    console.log('ESCANEIE O QR CODE ABAIXO COM O SEU CELULAR NO WHATSAPP:');
    console.log('============================================================\n');
    qrcode.generate(qr, { small: true });
    console.log('\n============================================================\n');
});

client.on('loading_screen', (percent, message) => {
    logText('LOADING', `Tela de carregamento: ${percent}% - ${message}`);
});

client.on('authenticated', () => {
    logText('AUTH', 'Autenticação realizada com sucesso!');
});

client.on('ready', async () => {
    const userJid = client.info && client.info.wid ? client.info.wid._serialized : 'Desconhecido';
    const userName = client.info ? client.info.pushname : 'Desconhecido';
    
    // Add user's own JID @lid dynamically if available
    if (client.info && client.info.wid && client.info.wid._serialized) {
        ownJids.add(client.info.wid._serialized);
    }
    
    botReady = true;
    logText('SYSTEM', `WhatsApp Bot está pronto e conectado! Logado como: ${userName} (${userJid})`);
    logText('SYSTEM', `JIDs próprios registrados: ${[...ownJids].join(', ')}`);
});

// Event triggered for any message created
client.on('message_create', async (msg) => {
    logText('MSG_RAW', `De: ${msg.from} | Para: ${msg.to} | fromMe: ${msg.fromMe} | Tipo: ${msg.type}`);

    // 1. Skip self-generated messages
    if (sentByBot.has(msg.id._serialized)) {
        sentByBot.delete(msg.id._serialized);
        return;
    }

    // 2. Dynamic learning of self LIDs
    if (msg.fromMe && msg.to && msg.to.endsWith('@lid') && msg.from && msg.from.includes(OWN_PHONE)) {
        if (!ownJids.has(msg.to)) {
            ownJids.add(msg.to);
            logText('SYSTEM', `Novo LID próprio detectado e registrado: ${msg.to}`);
        }
    }

    const config = loadConfig();
    const groupJid = config.groupJid || null;
    const panelJid = config.panelJid || null;
    const prefix = config.bot?.prefix || '/joe';

    const isSelfChat = ownJids.has(msg.from) && ownJids.has(msg.to);
    const isMainGroup = groupJid && (msg.to === groupJid || msg.from === groupJid);
    const isPanelGroup = panelJid && (msg.to === panelJid || msg.from === panelJid);

    const hasPrefix = msg.body && msg.body.trim().toLowerCase().startsWith(prefix);
    const isStatusQuery = msg.body && (
        msg.body.trim().toLowerCase().startsWith('/status') || 
        msg.body.trim().toLowerCase() === 'status' || 
        msg.body.trim().toLowerCase() === 'status do sistema' || 
        msg.body.trim().toLowerCase() === 'como esta o sistema' || 
        msg.body.trim().toLowerCase() === 'como está o sistema'
    );
    const isVoiceMessage = msg.hasMedia && (msg.type === 'audio' || msg.type === 'ptt');

    const shouldProcess = isSelfChat || isPanelGroup || (isMainGroup && (hasPrefix || isStatusQuery || isVoiceMessage));

    if (!shouldProcess) {
        return;
    }

    if ((isMainGroup || isSelfChat) && hasPrefix) {
        let commandText = msg.body.trim().substring(prefix.length).trim();
        
        if (!commandText) {
            await botReply(msg, 'olá, estou aqui. em que posso ajudar?');
            return;
        }
        
        const cleanText = commandText.toLowerCase();
        
        const isCommand = cleanText.startsWith('/status') || cleanText === 'status' || cleanText === 'status do sistema' ||
                          cleanText.startsWith('/print') || cleanText.startsWith('/dashboard') || cleanText === 'print' ||
                          cleanText.startsWith('/link') || cleanText === 'link' ||
                          cleanText.startsWith('/join ') || cleanText.startsWith('grupo ') || cleanText.startsWith('entrar no grupo ');
                          
        if (isCommand) {
            msg.body = commandText;
        } else {
            await botReply(msg, '⏳ Processando sua solicitação...');
            try {
                const textResult = await handleTextMessage(commandText);
                logText('TEXT_ROUTER', `Resultado: agente="${textResult.agent}" | auto_routed=${textResult.auto_routed} | texto="${textResult.text}"`);

                let agentLabel = textResult.agent || 'desconhecido';
                let responseMsg = `🤖 *Agente: ${agentLabel}*\n\n${textResult.response || 'Sem resposta.'}`;
                await botReply(msg, responseMsg);

                if (textResult.audio_path && fs.existsSync(textResult.audio_path)) {
                    try {
                        const ttsMedia = MessageMedia.fromFilePath(textResult.audio_path);
                        const ttsTarget = msg.from;
                        await botSendMessage(ttsTarget, ttsMedia, { sendAudioAsVoice: true });
                        logText('TTS_SENT', `Áudio TTS enviado para ${ttsTarget}: ${textResult.audio_path}`);
                    } catch (audioErr) {
                        logText('TTS_WARN', `Falha ao enviar áudio TTS: ${audioErr.message}`);
                    }
                }

                const responsePath = path.join(__dirname, 'user_response.json');
                const responseData = {
                    message: commandText,
                    sender: msg.author || msg.from,
                    agent: agentLabel,
                    response: textResult.response,
                    timestamp: new Date().toISOString()
                };
                fs.writeFileSync(responsePath, JSON.stringify(responseData, null, 2), 'utf-8');
            } catch (err) {
                logText('TEXT_ROUTER_ERR', `Erro ao processar texto: ${err.message}`);
                await botReply(msg, '❌ Desculpe, não consegui processar a sua solicitação. O backend Python pode não estar disponível.');
            }
            return;
        }
    }

    logText('MSG_IN', `Mensagem no chat próprio | fromMe: ${msg.fromMe} | Tipo: ${msg.type} | Corpo: "${msg.body}"`);

    // Handle voice messages via voice_router
    if (msg.hasMedia && (msg.type === 'audio' || msg.type === 'ptt')) {
        logText('AUDIO', `Baixando áudio de ${msg.from}...`);
        try {
            const media = await msg.downloadMedia();
            if (!media || !media.data) {
                await botReply(msg, '❌ Não foi possível baixar o áudio da mensagem.');
                return;
            }

            const voiceResult = await handleVoiceMessage(media.data);
            logText('VOICE_ROUTER', `Resultado: agente="${voiceResult.agent}" | auto_routed=${voiceResult.auto_routed} | texto="${voiceResult.text}"`);

            let agentLabel = voiceResult.agent || 'desconhecido';
            let autoLabel = voiceResult.auto_routed ? '\n_(🔄 Agente auto-selecionado)_' : '';
            let responseMsg = `🤖 *Agente: ${agentLabel}*\n\n${voiceResult.response || 'Sem resposta.'}${autoLabel}`;

            await botReply(msg, responseMsg);

            if (voiceResult.audio_path && fs.existsSync(voiceResult.audio_path)) {
                try {
                    const ttsMedia = MessageMedia.fromFilePath(voiceResult.audio_path);
                    const ttsTarget = msg.from;
                    await botSendMessage(ttsTarget, ttsMedia, { sendAudioAsVoice: true });
                    logText('TTS_SENT', `Áudio TTS enviado para ${ttsTarget}: ${voiceResult.audio_path}`);
                } catch (audioErr) {
                    logText('TTS_WARN', `Falha ao enviar áudio TTS: ${audioErr.message}`);
                }
            }
        } catch (err) {
            logText('AUDIO_ERROR', `Erro no processamento de voz: ${err.message}`);
            await botReply(msg, '❌ Desculpe, não consegui processar a sua mensagem de áudio. O backend Python/FFMPEG pode não estar disponível.');
        }
        return;
    }

    if (msg.type !== 'chat') return;
    let commandText = msg.body;
    if (!commandText) return;
    let cleanCommand = commandText.trim().toLowerCase();

    if (cleanCommand.startsWith('/status') || cleanCommand === 'status' || cleanCommand === 'status do sistema' || cleanCommand === 'como esta o sistema' || cleanCommand === 'como está o sistema') {
        logText('COMMAND', `Processando pedido de STATUS de ${msg.from}`);
        await handleStatus(msg);
    }
    else if (cleanCommand.startsWith('/print') || cleanCommand.startsWith('/dashboard') || cleanCommand === 'tira print' || cleanCommand === 'print' || cleanCommand === 'painel' || cleanCommand === 'dashboard' || cleanCommand === 'print do painel') {
        logText('COMMAND', `Processando pedido de PRINT de ${msg.from}`);
        await handlePrint(msg);
    }
    else if (cleanCommand.startsWith('/link') || cleanCommand === 'link' || cleanCommand === 'me manda o link' || cleanCommand === 'gerar link' || cleanCommand === 'acesso remoto') {
        logText('COMMAND', `Processando pedido de LINK de ${msg.from}`);
        await handleLink(msg);
    }
    else if (cleanCommand.startsWith('/join ') || cleanCommand.startsWith('entrar no grupo ') || cleanCommand.startsWith('grupo ')) {
        logText('COMMAND', `Processando pedido de JOIN de ${msg.from}`);
        await handleJoin(msg);
    }
});

async function handleVoiceMessage(base64Data) {
    const oggPath = path.join(__dirname, 'temp_voice.ogg');
    const wavPath = path.join(__dirname, 'temp_voice.wav');
    
    fs.writeFileSync(oggPath, Buffer.from(base64Data, 'base64'));
    
    const pythonPath = getPythonPath();
    const voiceRouterScript = path.join(__dirname, 'voice_router.py');
    
    try {
        const ffmpegCmd = `ffmpeg -y -i "${oggPath}" -ac 1 -ar 16000 "${wavPath}"`;
        await runCommand(ffmpegCmd);
        
        const routerCmd = `"${pythonPath}" "${voiceRouterScript}" -ja "${wavPath}"`;
        const routerOutput = await runCommand(routerCmd);
        
        logText('DEBUG_JSON', `RAW ROUTER OUTPUT: [${routerOutput}]`);
        const result = JSON.parse(routerOutput.trim());
        return result;
    } catch (err) {
        logText('VOICE_ROUTER_ERROR', `Falha no voice_router: ${err.message}`);
        throw err;
    } finally {
        if (fs.existsSync(oggPath)) fs.unlinkSync(oggPath);
        if (fs.existsSync(wavPath)) fs.unlinkSync(wavPath);
    }
}

async function handleTextMessage(text) {
    const pythonPath = getPythonPath();
    const voiceRouterScript = path.join(__dirname, 'voice_router.py');
    
    const escapedText = text.replace(/"/g, '\\"');
    const routerCmd = `"${pythonPath}" "${voiceRouterScript}" -jt "${escapedText}"`;
    
    try {
        const routerOutput = await runCommand(routerCmd);
        const result = JSON.parse(routerOutput.trim());
        return result;
    } catch (err) {
        logText('TEXT_ROUTER_ERROR', `Falha no processamento de texto: ${err.message}`);
        throw err;
    }
}

async function handleStatus(msg) {
    await botReply(msg, '⏳ Verificando status dos serviços... Por favor, aguarde.');
    
    const config = loadConfig();
    let statusText = '=====================\n📋 *STATUS DO SISTEMA*\n=====================\n\n';
    
    if (config.monitoring && config.monitoring.services && config.monitoring.services.length > 0) {
        for (const service of config.monitoring.services) {
            let srvStatus = '🔴 Inativo';
            if (service.check === 'http' && service.url) {
                try {
                    const response = await fetch(service.url, { method: 'HEAD', signal: AbortSignal.timeout(2000) });
                    if (response.ok || response.status === 200 || response.status === 404) {
                        srvStatus = '🟢 Online';
                    }
                } catch(e) {
                    logText('STATUS_CHECK', `Falha ao conectar em ${service.name}: ${e.message}`);
                }
            } else if (service.check === 'process' && service.processName) {
                const running = await checkProcess(service.processName);
                if (running) {
                    srvStatus = '🟢 Ativo';
                }
            }
            statusText += `*${service.name}:* ${srvStatus}\n`;
        }
    } else {
        statusText += "⚠️ _Nenhum serviço monitorado configurado em config.json._\n";
    }

    const now = new Date();
    const formattedDate = now.toLocaleDateString('pt-BR');
    const formattedTime = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    const timestampStr = `${formattedDate}, ${formattedTime}`;

    statusText += `\n-------------------------------------\n🕒 _Em: ${timestampStr}_`;
                        
    await botReply(msg, statusText);
    logText('STATUS_RESP', 'Resposta de status enviada com sucesso.');
}

async function handlePrint(msg) {
    await botReply(msg, '📸 Capturando tela do Dashboard... Um momento.');
    
    const screenshotPath = path.join(__dirname, 'temp_dashboard.png');
    let browser = null;
    
    try {
        logText('PRINT_CHECK', 'Iniciando navegador headless...');
        browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        const page = await browser.newPage();
        await page.setViewport({ width: 1280, height: 800 });
        
        const port = process.env.TUNNEL_PORT || 8080;
        logText('PRINT_CHECK', `Carregando http://localhost:${port}...`);
        await page.goto(`http://localhost:${port}`, {
            waitUntil: 'networkidle2',
            timeout: 15000
        });
        
        await new Promise(r => setTimeout(r, 1000));
        
        logText('PRINT_CHECK', 'Tirando captura de tela...');
        await page.screenshot({ path: screenshotPath });
        
        if (fs.existsSync(screenshotPath)) {
            logText('PRINT_CHECK', 'Enviando imagem capturada...');
            const media = MessageMedia.fromFilePath(screenshotPath);
            await botSendMessage(`${OWN_PHONE}@c.us`, media, { caption: `📊 Captura de tela do Dashboard (http://localhost:${port})` });
            logText('PRINT_RESP', 'Captura de tela enviada com sucesso.');
        } else {
            throw new Error('Arquivo de print não gerado após captura');
        }
    } catch (err) {
        logText('PRINT_ERROR', `Falha ao tirar print do dashboard: ${err.message}`);
        await botReply(msg, `❌ Falha ao tirar captura do dashboard. Certifique-se de que está ativo.`);
    } finally {
        if (browser) {
            await browser.close();
        }
        if (fs.existsSync(screenshotPath)) {
            fs.unlinkSync(screenshotPath);
        }
    }
}

async function handleLink(msg) {
    if (activeTunnelUrl && activeTunnelProcess) {
        try {
            const testRes = await fetch(activeTunnelUrl, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
            if (testRes.ok || testRes.status === 200 || testRes.status === 302 || testRes.status === 404) {
                await botReply(msg, `🔗 *Túnel Ativo!* Você pode acessar remotamente o dashboard através do link:\n\n${activeTunnelUrl}\n\n_(Este túnel já estava ativo e está sendo reutilizado)._`);
                return;
            }
        } catch (e) {
            logText('TUNNEL', `Túnel anterior não responde (${e.message}). Criando novo...`);
            if (activeTunnelProcess) activeTunnelProcess.kill();
            activeTunnelUrl = null;
            activeTunnelProcess = null;
        }
    }

    await botReply(msg, '⚡ Criando túnel público seguro com Cloudflare... Um momento.');

    try {
        const url = await startTunnel();
        await botReply(msg, `🔗 *Túnel Criado com Sucesso!* Acesso liberado no link abaixo:\n\n${url}\n\n⚠️ _Nota: Mantenha esta URL em segredo, ela expõe o seu painel à internet de forma temporária._`);
    } catch (err) {
        logText('LINK_ERROR', `Erro ao criar túnel Cloudflare: ${err.message}`);
        await botReply(msg, '❌ Não foi possível criar o túnel de acesso remoto. Verifique se o cloudflared está instalado e no PATH.');
    }
}

async function handleJoin(msg) {
    const parts = msg.body.trim().split(/\s+/);
    if (parts.length < 2) {
        await botReply(msg, '❌ Please send the group invite link. Example: `/join https://chat.whatsapp.com/AbCdEfGhIjK...`');
        return;
    }
    const inviteLink = parts[1];
    const inviteCode = inviteLink.substring(inviteLink.lastIndexOf('/') + 1);
    
    try {
        logText('GROUP_JOIN', `Tentando entrar no grupo com código: ${inviteCode}`);
        const result = await client.acceptInvite(inviteCode);
        logText('GROUP_JOIN', `Sucesso ao entrar no grupo! JID do Grupo: ${result}`);
        
        const configPath = path.join(__dirname, 'config.json');
        let config = {};
        if (fs.existsSync(configPath)) {
            try {
                config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
            } catch (e) {
                config = {};
            }
        }
        config.groupJid = result;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8');
        
        await botReply(msg, `🟢 *Sucesso!* O bot entrou no grupo.\nJID do Grupo salvo: \`${result}\`\nAs notificações de progresso serão enviadas lá!`);
    } catch (err) {
        logText('GROUP_JOIN_ERROR', `Falha ao entrar no grupo: ${err.message}`);
        await botReply(msg, `❌ Erro ao tentar entrar no grupo: ${err.message}`);
    }
}

function startTunnel() {
    return new Promise((resolve, reject) => {
        const port = process.env.TUNNEL_PORT || 8080;
        logText('TUNNEL', 'Iniciando processo do cloudflared...');
        const child = spawn('cloudflared', ['tunnel', '--url', `http://localhost:${port}`]);
        activeTunnelProcess = child;
        
        let resolved = false;
        
        const timeout = setTimeout(() => {
            if (!resolved) {
                resolved = true;
                child.kill();
                reject(new Error('Timeout de 15 segundos excedido ao conectar ao túnel'));
            }
        }, 15000);
        
        child.stderr.on('data', (data) => {
            const output = data.toString();
            const match = output.match(/https:\/\/[a-z0-9-]+\.trycloudflare\.com/);
            if (match) {
                activeTunnelUrl = match[0];
                logText('TUNNEL', `Link gerado: ${activeTunnelUrl}`);
                if (!resolved) {
                    resolved = true;
                    clearTimeout(timeout);
                    resolve(activeTunnelUrl);
                }
            }
        });
        
        child.on('close', (code) => {
            logText('TUNNEL', `Processo cloudflared encerrado (código: ${code})`);
            activeTunnelProcess = null;
            activeTunnelUrl = null;
        });
        
        child.on('error', (err) => {
            if (!resolved) {
                resolved = true;
                clearTimeout(timeout);
                reject(err);
            }
        });
    });
}

client.on('disconnected', (reason) => {
    logText('WARN', `Bot desconectado do WhatsApp: ${reason}. Reinicializando...`);
    setTimeout(() => {
        client.initialize().catch(e => logText('ERROR', `Falha ao reinicializar: ${e.message}`));
    }, 5000);
});

client.on('auth_failure', (msg) => {
    logText('ERROR', `Falha de autenticação: ${msg}`);
});

process.on('uncaughtException', (err) => {
    logText('CRASH', `Erro não tratado: ${err.message}\n${err.stack}`);
});

process.on('unhandledRejection', (reason) => {
    logText('CRASH', `Promise rejeitada não tratada: ${reason}`);
});

process.on('SIGINT', () => {
    logText('SYSTEM', 'Encerrando serviço do bot...');
    if (activeTunnelProcess) {
        activeTunnelProcess.kill();
    }
    clearInterval(keepAlive);
    process.exit();
});

const keepAlive = setInterval(() => {
    // Keeps event loop active
}, 30000);

// EXTERNAL NOTIFICATION WATCHER
const NOTIF_FILE = path.join(__dirname, 'pending_notification.json');
const SENT_DIR = path.join(__dirname, 'sent_notifications');
if (!fs.existsSync(SENT_DIR)) { fs.mkdirSync(SENT_DIR, { recursive: true }); }

const notifWatcher = setInterval(async () => {
    if (!botReady) return;
    try {
        if (!fs.existsSync(NOTIF_FILE)) return;
        const raw = fs.readFileSync(NOTIF_FILE, 'utf-8');
        if (!raw.trim()) return;
        const notif = JSON.parse(raw);
        if (!notif.message) return;

        let targetChat = `${OWN_PHONE}@c.us`;
        const config = loadConfig();
        if (config.groupJid) {
            targetChat = config.groupJid;
        }
        if (notif.chatId && notif.chatId !== `${OWN_PHONE}@c.us`) {
            targetChat = notif.chatId;
        }

        logText('NOTIF', `Enviando notificação externa para ${targetChat}: "${notif.message.substring(0, 80)}..."`);
        await botSendMessage(targetChat, notif.message);
        logText('NOTIF', `✅ Notificação enviada com sucesso!`);

        const sentFile = path.join(SENT_DIR, `notif_${Date.now()}.json`);
        fs.renameSync(NOTIF_FILE, sentFile);
    } catch (err) {
        logText('NOTIF_ERR', `Erro ao processar notificação: ${err.message}`);
    }
}, 10000);

client.initialize();
logText('SYSTEM', 'Cliente do bot de WhatsApp inicializado.');
logText('SYSTEM', 'Watcher de notificações externas ativado (a cada 10s).');
