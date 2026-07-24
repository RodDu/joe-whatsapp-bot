# -*- coding: utf-8 -*-
"""
voice_router.py — Core Voice Processing Pipeline
================================================

Pipeline:
  Audio -> Transcription -> Agent Detection -> Routing -> Execution -> TTS Synthesis

Transcription engines (configurable via .env TRANSCRIPTION_ENGINE):
  - Primary (default): Gemini 2.0 Flash REST API (cloud)
  - Fallback 1: Voicebox API (local)
  - Fallback 2: faster-whisper (local)

TTS engines (configurable via .env TTS_ENGINE):
  - Primary (default): edge-tts (cloud)
  - Fallback/Alternative: Voicebox (local)
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import re
import subprocess
import sys

# Redirect sys.stdout to sys.stderr to avoid imported modules 
# corrupting JSON output with unwanted logs.
_original_stdout = sys.stdout
sys.stdout = sys.stderr

import tempfile
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ─── Project Paths ─── #
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
TEMP_VOICE_DIR = SCRIPT_DIR / "temp_voice"
TEMP_VOICE_DIR.mkdir(exist_ok=True)

# ─── Logging Setup ─── #
# StreamHandler with UTF-8 to avoid UnicodeEncodeError on Windows console (cp1252)
_console_handler = logging.StreamHandler(
    io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        _console_handler,
        logging.FileHandler(
            SCRIPT_DIR / "voice_router.log", encoding="utf-8", mode="a"
        ),
    ],
)
logger = logging.getLogger("voice_router")


def _log(tag: str, msg: str) -> None:
    """Standardized log with a visual prefix."""
    logger.info("[%s] %s", tag, msg)


# ─── Configuration Loading ─── #
def _load_config() -> dict:
    """Load config.json from the same directory."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
            _log("CONFIG", f"Configuration loaded from {CONFIG_PATH}")
            return cfg
    except FileNotFoundError:
        _log("CONFIG", f"Configuration file not found: {CONFIG_PATH}")
        return {}
    except json.JSONDecodeError as exc:
        _log("ERRO", f"Error decoding config.json: {exc}")
        return {}

CONFIG = _load_config()

# ─── Tools System Import (graceful degradation) ─── #
_TOOLS_AVAILABLE = False
try:
    from tools.agent import run_agent as _run_tool_agent
    from tools.agent import init as _init_tool_agent
    from tools.executor import execute_tool as _tool_executor
    from tools.web_search import init as _init_web_search
    _TOOLS_AVAILABLE = True
    _log("INIT", "Tools system (tools/) loaded successfully.")
except ImportError as _tools_err:
    _log("INIT", f"Tools system unavailable: {_tools_err}. Using legacy mode.")


# ─── API Keys & Config ─── #
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

# Ollama Config
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2")

# TTS Config
TTS_ENGINE = os.environ.get("TTS_ENGINE", "edge-tts")
TTS_VOICE = os.environ.get("TTS_VOICE", "en-US-GuyNeural")
VOICEBOX_URL = os.environ.get("VOICEBOX_URL", "http://127.0.0.1:17493")

TRANSCRIPTION_ENGINE = os.environ.get("TRANSCRIPTION_ENGINE", "gemini")

# Agent Definitions
AGENTS = CONFIG.get("agents", {})
_AGENT_ALIASES = CONFIG.get("agentAliases", {})

# Auto Routing Keywords
AUTO_ROUTE_CFG = CONFIG.get("autoRoute", {})
SYSTEM_KEYWORDS = AUTO_ROUTE_CFG.get("systemKeywords", ["restart", "status", "logs", "process", "service"])
CODE_KEYWORDS = AUTO_ROUTE_CFG.get("codeKeywords", ["code", "program", "python", "javascript", "bug", "error", "script"])
CREATIVE_KEYWORDS = AUTO_ROUTE_CFG.get("creativeKeywords", ["analyze", "creative", "imagine", "write", "story"])

BOT_LANG = CONFIG.get("bot", {}).get("language", "en")

# ─── AUDIO TRANSCRIPTION ─── #

def _call_gemini_rest(prompt: str, system_prompt: Optional[str] = None, model: str = "gemini-2.5-flash") -> str:
    """Make a direct REST call to the official Gemini API."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured.")
        
    import ssl
    import json
    import urllib.request
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    parts = [{"text": prompt}]
    payload = {
        "contents": [{"parts": parts}]
    }
    
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        
    data = json.dumps(payload).encode("utf-8")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()


async def _transcribe_gemini(audio_bytes: bytes, audio_format: str) -> str:
    """Primary transcription via Gemini 2.0 Flash REST API."""
    _log("VOICE", "Starting transcription via Gemini 2.0 Flash REST API...")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")

    import base64
    import ssl
    import json
    import urllib.request
    
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    
    mime_map = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
        "opus": "audio/ogg",
        "m4a": "audio/mp4",
        "webm": "audio/webm",
        "flac": "audio/flac",
    }
    mime_type = mime_map.get(audio_format.lower().strip("."), "audio/wav")
    
    prompt_text = "Transcribe this audio. Return ONLY the transcribed text, with no formatting, no markers, no headers, and no explanations."
    if BOT_LANG == "pt":
        prompt_text = "Transcreva este áudio em português brasileiro. Retorne APENAS o texto transcrito, sem formatações, sem marcadores, sem cabeçalhos e sem explicações."

    payload = {
        "contents": [{
            "parts": [
                {
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": audio_b64
                    }
                },
                {
                    "text": prompt_text
                }
            ]
        }]
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    data = json.dumps(payload).encode("utf-8")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    def perform_request():
        with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
    text = await asyncio.to_thread(perform_request)
    _log("VOICE", f"Gemini transcription complete: '{text[:120]}...'" if len(text) > 120 else f"Gemini transcription complete: '{text}'")
    return text

# Global cache for faster-whisper model
_whisper_model = None
_whisper_model_lock = threading.Lock()

def _get_whisper_model():
    """Returns the faster-whisper model, loading it only on the first call."""
    global _whisper_model
    if _whisper_model is None:
        with _whisper_model_lock:
            if _whisper_model is None:
                from faster_whisper import WhisperModel
                _log("VOICE", "Loading faster-whisper 'small' model (first time, may take a while)...")
                _whisper_model = WhisperModel(
                    "small",
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=4,
                )
                _log("VOICE", "faster-whisper 'small' model loaded and cached.")
    return _whisper_model


async def _transcribe_faster_whisper(audio_bytes: bytes, audio_format: str) -> str:
    """Local transcription via faster-whisper."""
    try:
        model = _get_whisper_model()
        _log("VOICE", "Starting transcription via faster-whisper...")

        suffix = f".{audio_format.strip('.')}"
        tmp_path = TEMP_VOICE_DIR / f"whisper_input_{int(time.time())}{suffix}"
        tmp_path.write_bytes(audio_bytes)

        try:
            segments, info = await asyncio.to_thread(
                model.transcribe,
                str(tmp_path),
                language=BOT_LANG,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200,
                ),
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            _log("VOICE", f"faster-whisper transcription complete ({info.language}, conf={info.language_probability:.2f}): '{text[:120]}'")
            return text
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

    except ImportError:
        _log("ERROR", "faster-whisper not installed.")
        raise RuntimeError("No transcription backend available")
    except Exception as exc:
        _log("ERROR", f"faster-whisper transcription failed: {exc}")
        raise


async def _transcribe_voicebox(audio_bytes: bytes, audio_format: str = "wav") -> str:
    """Transcribe audio using local Voicebox API."""
    import requests
    _log("VOICE", "Starting transcription via Voicebox API...")
    
    url = f"{VOICEBOX_URL}/transcribe"
    files = {
        'file': (f'audio.{audio_format}', audio_bytes, f'audio/{audio_format}')
    }
    data = {
        'model': 'turbo'
    }
    try:
        def _do_req():
            resp = requests.post(url, files=files, data=data, timeout=30)
            resp.raise_for_status()
            return resp.json()
            
        result = await asyncio.to_thread(_do_req)
        text = result.get("text", "").strip()
        _log("VOICE", f"Voicebox transcription complete: '{text}'")
        return text
    except Exception as exc:
        _log("ERROR", f"Voicebox transcription failed: {exc}")
        raise RuntimeError(f"Transcription failed: {exc}")


async def transcribe_audio(audio_bytes: bytes, audio_format: str = "wav") -> str:
    """Architecture for transcription."""
    engine = TRANSCRIPTION_ENGINE.lower()
    
    if engine == "gemini" and GEMINI_API_KEY:
        try: 
            return await _transcribe_gemini(audio_bytes, audio_format)
        except Exception as e:
            _log("WARN", f"Gemini transcription failed: {e}. Falling back to Voicebox...")
            
    if engine in ("voicebox", "gemini"):
        try:
            return await _transcribe_voicebox(audio_bytes, audio_format)
        except Exception as e:
            _log("WARN", f"Voicebox transcription failed: {e}. Falling back to faster-whisper...")
            
    return await _transcribe_faster_whisper(audio_bytes, audio_format)

# ─── AGENT DETECTION AND ROUTING ─── #

def _detect_agent_in_text(text: str) -> tuple[Optional[str], str]:
    """Detects agent trigger words anywhere in the text."""
    text_lower = text.lower().strip()

    # Check aliases first
    for alias, agent_name in sorted(
        _AGENT_ALIASES.items(), key=lambda x: len(x[0]), reverse=True
    ):
        pattern = re.compile(re.escape(alias), re.IGNORECASE)
        if pattern.search(text_lower):
            cleaned = pattern.sub("", text, count=1).strip()
            cleaned = re.sub(r"^[,.\s!?;:]+", "", cleaned).strip()
            _log("ROUTER", f"Agent detected by alias '{alias}' -> '{agent_name}'")
            return agent_name, cleaned

    # Check direct agent names
    for agent_name in AGENTS:
        pattern = re.compile(r"\b" + re.escape(agent_name) + r"\b", re.IGNORECASE)
        if pattern.search(text_lower):
            cleaned = pattern.sub("", text, count=1).strip()
            cleaned = re.sub(r"^[,.\s!?;:]+", "", cleaned).strip()
            _log("ROUTER", f"Agent detected directly: '{agent_name}'")
            return agent_name, cleaned

    _log("ROUTER", "No agent detected in text - auto-routing needed")
    return None, text


def _detect_sequential_routing(text: str) -> list[dict]:
    """
    Detects sequential routing: when the user asks an agent to call another agent.
    Returns a list of routing steps.
    """
    # Portuguese patterns
    delegation_patterns = [
        r"(?:ligue|chame|acione|peça\s+(?:ao|para\s+o?))\s+(?:o\s+)?(\w+)\s+(?:e\s+)?(?:peça|mande|diga|solicite)\s+(?:para\s+)?(?:ele\s+)?(.+)",
        r"(?:fale\s+com|contate)\s+(?:o\s+)?(\w+)\s+(?:e\s+)?(?:peça|mande|diga)\s+(?:para\s+)?(?:ele\s+)?(.+)",
        r"(?:encaminhe|repasse)\s+(?:para|ao)\s+(?:o\s+)?(\w+)\s*[:\-]?\s*(.+)",
        r"(?:ask|tell|call)\s+(\w+)\s+to\s+(.+)",
        r"(?:forward|delegate)\s+(?:to)\s+(\w+)\s*[:\-]?\s*(.+)",
    ]

    for pattern in delegation_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            second_agent_name = match.group(1).lower().strip()
            second_task = match.group(2).strip()

            resolved = _AGENT_ALIASES.get(second_agent_name, second_agent_name)
            if resolved in AGENTS:
                _log(
                    "ROUTER",
                    f"Sequential routing detected -> second agent: '{resolved}', task: '{second_task}'",
                )
                return [
                    {"agent": None, "task": text},  # Will be filled by main detect
                    {"agent": resolved, "task": second_task},
                ]

    return []


_AUTO_ROUTE_PROMPT = """You are an intent classifier for an automation system.
Analyze the user command below and classify it into ONE of the following agent categories:
{categories}

Respond ONLY with the category name, no explanations.

User command: "{text}"

Category:"""

async def _auto_route(text: str) -> str:
    """Smart auto-routing based on command context."""
    _log("ROUTER", "Executing smart auto-routing...")
    
    categories = "\n".join([f"- '{k}' - {v.get('description', '')}" for k,v in AGENTS.items()])
    prompt = _AUTO_ROUTE_PROMPT.format(categories=categories, text=text)

    if GEMINI_API_KEY:
        try:
            response = await asyncio.to_thread(
                _call_gemini_rest,
                prompt=prompt,
                model="gemini-2.5-flash"
            )
            category = response.strip().lower().strip('"\'').strip()
            if category in AGENTS:
                _log("ROUTER", f"Gemini smart routing -> '{category}'")
                return category
            _log("ROUTER", f"Gemini returned invalid category: '{category}', trying local fallback...")
        except Exception as exc:
            _log("ROUTER", f"Gemini smart routing failed: {exc}")

    try:
        category = await _ollama_generate(
            prompt, model=OLLAMA_MODEL, max_tokens=20
        )
        category = category.strip().lower().strip('"\'').strip()
        if category in AGENTS:
            _log("ROUTER", f"Ollama routing -> '{category}'")
            return category
        _log("ROUTER", f"Ollama returned invalid category: '{category}'")
    except Exception as exc:
        _log("ROUTER", f"Ollama auto-routing failed: {exc}")

    return _heuristic_route(text)


def _heuristic_route(text: str) -> str:
    """Heuristic routing by keywords (last resort)."""
    text_lower = text.lower()

    if any(kw in text_lower for kw in SYSTEM_KEYWORDS):
        agent = next((k for k,v in AGENTS.items() if v.get("type") == "system"), None)
        if agent:
            _log("ROUTER", f"Heuristic -> '{agent}'")
            return agent

    api_agents = [k for k,v in AGENTS.items() if v.get("type") == "api"]
    if api_agents and any(kw in text_lower for kw in CODE_KEYWORDS):
        _log("ROUTER", f"Heuristic -> '{api_agents[0]}'")
        return api_agents[0]

    local_agents = [k for k,v in AGENTS.items() if v.get("type") == "local"]
    
    if any(kw in text_lower for kw in CREATIVE_KEYWORDS):
        if local_agents:
            _log("ROUTER", f"Heuristic -> '{local_agents[0]}'")
            return local_agents[0]
            
    default = local_agents[0] if local_agents else (api_agents[0] if api_agents else list(AGENTS.keys())[0])
    _log("ROUTER", f"Heuristic (general fallback) -> '{default}'")
    return default


async def route_command(text: str) -> dict:
    """Complete routing: detect agent, check sequential routing, return execution plan."""
    agent, cleaned_text = _detect_agent_in_text(text)
    auto_routed = agent is None

    if auto_routed:
        agent = await _auto_route(text)
        cleaned_text = text

    sequential_steps = _detect_sequential_routing(cleaned_text)
    if sequential_steps and not auto_routed:
        sequential_steps[0]["agent"] = agent
        return {
            "agent": agent,
            "task": cleaned_text,
            "auto_routed": False,
            "sequential": sequential_steps,
        }

    return {
        "agent": agent,
        "task": cleaned_text,
        "auto_routed": auto_routed,
        "sequential": None,
    }


# ─── AGENT EXECUTION ─── #

async def _ollama_generate(
    prompt: str,
    model: str = OLLAMA_MODEL,
    max_tokens: int = 1024,
    system_prompt: str | None = None,
) -> str:
    """Send prompt to Ollama via HTTP."""
    import urllib.request
    import urllib.error

    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens, "num_ctx": 4096},
    }
    if system_prompt:
        payload["system"] = system_prompt

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    _log("AGENT", f"Calling Ollama ({model})...")

    try:
        def _do_request():
            with urllib.request.urlopen(req, timeout=600) as resp:
                return json.loads(resp.read().decode("utf-8"))

        result = await asyncio.to_thread(_do_request)
        response_text = result.get("response", "").strip()
        _log("AGENT", f"Ollama responded ({len(response_text)} chars)")
        return response_text

    except urllib.error.URLError as exc:
        _log("ERROR", f"Ollama unavailable: {exc}")
        raise RuntimeError(f"Ollama unavailable at {OLLAMA_BASE_URL}: {exc}")
    except Exception as exc:
        _log("ERROR", f"Ollama call error: {exc}")
        raise


async def _execute_local_agent(agent_name: str, task: str) -> str:
    """Execute a local agent via Ollama."""
    agent_cfg = AGENTS[agent_name]
    model = agent_cfg.get("model", OLLAMA_MODEL)
    
    lang_str = "English" if BOT_LANG == "en" else "Portuguese"

    system_prompt = (
        f"You are the assistant '{agent_name}'. {agent_cfg.get('description', '')}. "
        f"Always answer in {lang_str} clearly and helpfully."
    )

    return await _ollama_generate(
        prompt=task,
        model=model,
        system_prompt=system_prompt,
    )


async def _execute_cloud_agent(agent_name: str, task: str) -> str:
    """Execute a cloud agent using Gemini Oficial with local fallback."""
    agent_cfg = AGENTS[agent_name]
    _log("AGENT", f"[{agent_name}] Command received: '{task[:200]}'")
    
    lang_str = "English" if BOT_LANG == "en" else "Portuguese"

    system_prompt = (
        f"You are the assistant '{agent_name}'. {agent_cfg.get('description', '')}. "
        f"Always answer in {lang_str} clearly, objectively and helpfully."
    )
    
    if GEMINI_API_KEY:
        model = agent_cfg.get("model", "gemini-2.5-flash")
        try:
            response = await asyncio.to_thread(
                _call_gemini_rest,
                prompt=f"User question: {task}",
                system_prompt=system_prompt,
                model=model
            )
            return response.strip()
        except Exception as exc:
            _log("AGENT", f"Gemini Oficial unavailable for {agent_name}, using Ollama: {exc}")

    # Fallback to local
    return await _ollama_generate(
        prompt=task,
        model=OLLAMA_MODEL,
        system_prompt=system_prompt,
    )


# ─── System Agent ─── #

def _run_ps_command(command: str, timeout: int = 30) -> str:
    """Run a PowerShell command and return output."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr.strip():
            output += f"\n[STDERR]: {result.stderr.strip()}"
        return output if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "[ERROR] Command timed out"
    except Exception as exc:
        return f"[ERROR] Command failed: {exc}"


def _normalize_text(text: str) -> str:
    """Normalize transcription text to correct common phonetic errors."""
    if not text:
        return text
    
    replacements = [
        (r"\bwhats\b", "whatsapp"),
        (r"\bwhats\s+app\b", "whatsapp"),
    ]
    
    normalized = text
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _check_service_status(service_cfg: dict) -> str:
    name = service_cfg.get("name", "Unknown")
    check_type = service_cfg.get("check", "process")
    target = service_cfg.get("url") or service_cfg.get("processName")
    
    if check_type == "http" and target:
        import urllib.request
        try:
            req = urllib.request.Request(target, method="HEAD")
            with urllib.request.urlopen(req, timeout=5):
                return f"🟢 {name} is reachable at {target}."
        except Exception as e:
            return f"❌ {name} is NOT reachable at {target}. ({e})"
    elif check_type == "process" and target:
        cmd = f"Get-Process -Name '{target}' -ErrorAction SilentlyContinue"
        res = _run_ps_command(cmd)
        if "(no output)" in res or not res.strip():
            return f"❌ {name} process ('{target}') is NOT running."
        return f"🟢 {name} process is running."
    
    return f"⚠️ {name} has invalid configuration."


async def _execute_system_agent(task: str) -> str:
    """Generic system agent: checks configured services."""
    _log("AGENT", f"[System] Processing: '{task[:200]}'")
    task_lower = task.lower()

    services = CONFIG.get("monitoring", {}).get("services", [])
    
    is_status_request = any(kw in task_lower for kw in ["status", "check", "running", "state"])
    
    if is_status_request:
        if not services:
            return "No monitoring services are configured in config.json."
        
        status_lines = ["=== SERVICES STATUS ==="]
        for s in services:
            # Check if a specific service was requested
            if any(w in task_lower for w in s.get("name", "").lower().split()):
                return _check_service_status(s)
            
            status_lines.append(_check_service_status(s))
            
        return "\n".join(status_lines)
    
    # Generic interpretation fallback
    prompt = (
        f"You are a system agent. The user asked: '{task}'\n\n"
        f"You can currently only report the status of configured services: {[s.get('name') for s in services]}.\n"
        f"Inform the user you can only check statuses at the moment."
    )
    try:
        return await _ollama_generate(prompt, model=OLLAMA_MODEL, max_tokens=256)
    except Exception:
        return "⚠️ Could not interpret system command. I can only check the status of configured services."


def _ensure_tools_initialized():
    """Initializes the tools system (once)."""
    if not _TOOLS_AVAILABLE:
        return False
    if not getattr(_ensure_tools_initialized, '_done', False):
        _init_tool_agent(
            gemini_api_key=GEMINI_API_KEY,
            ollama_base_url=OLLAMA_BASE_URL,
            ollama_model=OLLAMA_MODEL,
            tool_executor=_tool_executor,
        )
        _init_web_search(GEMINI_API_KEY)
        _ensure_tools_initialized._done = True
        _log("INIT", "Tools system initialized.")
    return True


async def execute_agent(agent_name: str, task: str) -> str:
    """Dispatches task to the correct agent and returns response."""
    if agent_name not in AGENTS:
        return f"⚠️ Agent '{agent_name}' not found in registry."

    agent_cfg = AGENTS[agent_name]
    agent_type = agent_cfg["type"]

    _log("AGENT", f"Executing agent '{agent_name}' (type={agent_type})")

    try:
        if agent_type == "system":
            return await _execute_system_agent(task)

        if agent_type in ("local", "api") and _ensure_tools_initialized():
            _log("AGENT", "Delegating to tool agent loop")
            return await _run_tool_agent(task)

        # Fallback
        if agent_type == "local":
            return await _execute_local_agent(agent_name, task)
        elif agent_type == "api":
            return await _execute_cloud_agent(agent_name, task)
        else:
            return f"⚠️ Unknown agent type: {agent_type}"

    except Exception as exc:
        _log("ERROR", f"Failed to execute agent '{agent_name}': {exc}")
        _log("ERROR", traceback.format_exc())
        return f"❌ Error executing agent '{agent_name}': {exc}"


# ─── TEXT TO SPEECH (TTS) ─── #

async def _synthesize_edge_tts(text: str, voice: str) -> Optional[Path]:
    try:
        import edge_tts
        output_path = TEMP_VOICE_DIR / f"tts_{int(time.time())}.mp3"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        _log("TTS", f"edge-tts synthesis saved to {output_path}")
        return output_path
    except ImportError:
        _log("ERROR", "edge-tts not installed.")
        return None
    except Exception as e:
        _log("ERROR", f"edge-tts error: {e}")
        return None


async def _synthesize_voicebox(text: str, voice: str = "Morgan") -> Optional[Path]:
    import requests
    url = f"{VOICEBOX_URL}/speak"
    headers = {
        "Content-Type": "application/json",
        "X-Voicebox-Client-Id": "bot-router"
    }
    data = {
        "text": text,
        "profile": voice,
        "personality": False
    }
    
    try:
        def _do_req():
            resp = requests.post(url, json=data, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
            
        await asyncio.to_thread(_do_req)
        _log("TTS", "Voicebox accepted speech.")
        return None
    except Exception as exc:
        _log("ERROR", f"Voicebox /speak failed: {exc}")
        return None


async def synthesize_speech(text: str, voice: str = None) -> Optional[Path]:
    """Architecture for speech synthesis."""
    if not text:
        return None
        
    tts_text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    tts_text = re.sub(r"[=*_`#~-]", "", tts_text)
    tts_text = re.sub(r"[❌✅🟢⚠️🔴]", "", tts_text)
    tts_text = re.sub(r"\s+", " ", tts_text).strip()
    
    if not tts_text:
        return None
        
    if TTS_ENGINE == "voicebox":
        return await _synthesize_voicebox(tts_text, voice or "Morgan")
    else:
        return await _synthesize_edge_tts(tts_text, voice or TTS_VOICE)


# ─── CLEANUP ─── #

def cleanup_old_temp_files(max_age_hours: int = 24) -> int:
    """Removes temporary files older than max_age_hours."""
    if not TEMP_VOICE_DIR.exists():
        return 0

    cutoff = time.time() - (max_age_hours * 3600)
    removed = 0

    for file_path in TEMP_VOICE_DIR.iterdir():
        if file_path.is_file() and file_path.stat().st_mtime < cutoff:
            try:
                file_path.unlink()
                removed += 1
            except OSError:
                pass

    if removed:
        _log("VOICE", f"Cleanup: {removed} temp file(s) removed")
    return removed


# ─── MAIN PIPELINE ─── #

async def process_voice_command(
    audio_bytes: bytes,
    audio_format: str = "wav",
    source: str = "local",
) -> dict:
    """Complete voice processing pipeline."""
    _log("VOICE", f"=== New voice command (source={source}, size={len(audio_bytes)} bytes, format={audio_format}) ===")

    result = {
        "text": "",
        "response": "",
        "audio_path": None,
        "agent": "",
        "auto_routed": False,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "error": None,
    }

    cleanup_old_temp_files()

    # Step 1: Transcription
    try:
        transcribed_text = await transcribe_audio(audio_bytes, audio_format)
        if not transcribed_text or transcribed_text.startswith("[Error"):
            result["error"] = f"Transcription failed: {transcribed_text}"
            result["response"] = "Sorry, I couldn't understand the audio. Can you repeat?"
            _log("ERROR", result["error"])
            result["audio_path"] = str(p) if (p := await synthesize_speech(result["response"])) else None
            return result
        normalized_text = _normalize_text(transcribed_text)
        result["text"] = normalized_text
        _log("VOICE", f"Transcription: '{transcribed_text}' (normalized: '{normalized_text}')")
    except Exception as exc:
        result["error"] = f"Critical transcription error: {exc}"
        result["response"] = "An error occurred during transcription."
        _log("ERROR", f"Critical transcription error: {exc}\n{traceback.format_exc()}")
        return result

    # Step 2: Routing
    try:
        route_plan = await route_command(normalized_text)
        result["agent"] = route_plan["agent"]
        result["auto_routed"] = route_plan["auto_routed"]

        routing_label = "auto-routed" if route_plan["auto_routed"] else "direct"
        _log("ROUTER", f"Plan: agent='{route_plan['agent']}', mode={routing_label}")

    except Exception as exc:
        _log("ERROR", f"Routing error: {exc}")
        fallback_agent = list(AGENTS.keys())[0] if AGENTS else "system"
        route_plan = {
            "agent": fallback_agent,
            "task": normalized_text,
            "auto_routed": True,
            "sequential": None,
        }
        result["agent"] = fallback_agent
        result["auto_routed"] = True

    # Step 3: Execution
    try:
        if route_plan.get("sequential"):
            _log("AGENT", f"Executing sequential routing ({len(route_plan['sequential'])} steps)...")
            responses = []
            previous_response = ""

            for i, step in enumerate(route_plan["sequential"]):
                step_agent = step["agent"]
                step_task = step["task"]

                if i > 0 and previous_response:
                    step_task = (
                        f"Context from previous step ({route_plan['sequential'][i-1]['agent']}): "
                        f"{previous_response}\n\n"
                        f"Task: {step_task}"
                    )

                _log("AGENT", f"Step {i+1}/{len(route_plan['sequential'])}: agent='{step_agent}'")
                step_response = await execute_agent(step_agent, step_task)
                responses.append(f"[{step_agent.upper()}]: {step_response}")
                previous_response = step_response

            result["response"] = "\n\n".join(responses)
        else:
            result["response"] = await execute_agent(
                route_plan["agent"], route_plan["task"]
            )

    except Exception as exc:
        _log("ERROR", f"Agent execution error: {exc}\n{traceback.format_exc()}")
        result["response"] = f"Error processing command with agent '{route_plan['agent']}': {exc}"
        result["error"] = str(exc)

    # Step 4: TTS Synthesis
    try:
        audio_path = await synthesize_speech(result["response"])
        if audio_path:
            result["audio_path"] = str(audio_path)
    except Exception as exc:
        _log("ERROR", f"TTS synthesis error: {exc}")

    _log("VOICE", f"=== Processing complete (agent={result['agent']}, auto={result['auto_routed']}) ===")
    return result


# ─── TEXT INTERFACE ─── #

async def process_text_command(text: str, source: str = "text") -> dict:
    """Processes a text command directly."""
    _log("VOICE", f"=== Text command received (source={source}): '{text[:120]}' ===")

    normalized_text = _normalize_text(text)

    result = {
        "text": normalized_text,
        "response": "",
        "audio_path": None,
        "agent": "",
        "auto_routed": False,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "error": None,
    }

    try:
        route_plan = await route_command(normalized_text)
        result["agent"] = route_plan["agent"]
        result["auto_routed"] = route_plan["auto_routed"]

        if route_plan.get("sequential"):
            responses = []
            previous_response = ""
            for i, step in enumerate(route_plan["sequential"]):
                step_task = step["task"]
                if i > 0 and previous_response:
                    step_task = (
                        f"Previous context ({route_plan['sequential'][i-1]['agent']}): "
                        f"{previous_response}\n\nTask: {step_task}"
                    )
                step_response = await execute_agent(step["agent"], step_task)
                responses.append(f"[{step['agent'].upper()}]: {step_response}")
                previous_response = step_response
            result["response"] = "\n\n".join(responses)
        else:
            result["response"] = await execute_agent(
                route_plan["agent"], route_plan["task"]
            )
    except Exception as exc:
        result["error"] = str(exc)
        result["response"] = f"Error: {exc}"

    _log("VOICE", f"=== Text processed (agent={result['agent']}) ===")
    return result


# ─── CLI MODE ─── #

def _safe_print(text: str) -> None:
    try:
        sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
    except Exception:
        print(text.encode("ascii", errors="replace").decode("ascii"))


async def _cli_process_audio_file(file_path: str, as_json: bool = False) -> None:
    path = Path(file_path)
    if not path.exists():
        if as_json:
            _original_stdout.buffer.write(json.dumps({"error": f"File not found: {file_path}"}).encode("utf-8"))
            _original_stdout.buffer.flush()
        else:
            _safe_print(f"[ERROR] File not found: {file_path}")
        return

    audio_bytes = path.read_bytes()
    audio_format = path.suffix.lstrip(".")
    if not as_json:
        _safe_print(f"\nProcessing file: {path.name} ({len(audio_bytes)} bytes, format={audio_format})\n")
    result = await process_voice_command(
        audio_bytes=audio_bytes,
        audio_format=audio_format,
        source="cli",
    )

    if as_json:
        _original_stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode("utf-8", errors="replace"))
        _original_stdout.buffer.flush()
        return

    _safe_print("\n" + "=" * 60)
    _safe_print(f"Transcription: {result['text']}")
    _safe_print(f"Agent: {result['agent']} {'(auto-routed)' if result['auto_routed'] else '(direct)'}")
    _safe_print(f"Response:\n{result['response']}")
    if result.get("audio_path"):
        _safe_print(f"Audio: {result['audio_path']}")
    if result.get("error"):
        _safe_print(f"Error: {result['error']}")
    _safe_print("=" * 60 + "\n")


async def _cli_interactive_mode() -> None:
    _safe_print("\n" + "=" * 60)
    _safe_print("  Voice Router - Text Interactive Mode")
    _safe_print("  Type commands as if they were voice transcriptions.")
    _safe_print("  Special commands: 'quit', 'exit'")
    _safe_print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            _safe_print("\nExiting...")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            _safe_print("Goodbye!")
            break

        result = await process_text_command(user_input, source="cli_interactive")

        _safe_print(f"\n[{result['agent'].upper()}] {'(auto)' if result['auto_routed'] else ''}")
        _safe_print(f"{result['response']}")
        if result["audio_path"]:
            _safe_print(f"Audio: {result['audio_path']}")
        print()


async def _cli_main() -> None:
    if len(sys.argv) >= 2:
        arg = sys.argv[1]

        if arg in ("--interactive", "-i"):
            await _cli_interactive_mode()
        elif arg in ("--text", "-t"):
            text = " ".join(sys.argv[2:])
            if not text:
                print("[ERROR] Provide text after -t.")
                return
            result = await process_text_command(text, source="cli_text")
            sys.stdout.buffer.write(f"\n[{result['agent'].upper()}] {result['response']}\n".encode("utf-8", errors="replace"))
        elif arg in ("--json-text", "-jt"):
            text = " ".join(sys.argv[2:])
            if not text:
                print(json.dumps({"error": "Empty text"}))
                return
            result = await process_text_command(text, source="cli_json_text")
            output_json = json.dumps(result, ensure_ascii=False)
            _original_stdout.buffer.write((output_json + "\n").encode("utf-8", errors="replace"))
            _original_stdout.buffer.flush()
        elif arg in ("--help", "-h"):
            print(
                "Usage:\n"
                "  python voice_router.py <audio_file>        Process audio file\n"
                "  python voice_router.py -i                  Text interactive mode\n"
                "  python voice_router.py -t <text>           Process text directly\n"
                "  python voice_router.py -jt <text>          Process text and return JSON\n"
                "  python voice_router.py -h                  Show help\n"
            )
        elif arg == "-ja" and len(sys.argv) == 3:
            await _cli_process_audio_file(sys.argv[2], as_json=True)
        else:
            await _cli_process_audio_file(arg)
    else:
        await _cli_interactive_mode()


if __name__ == "__main__":
    asyncio.run(_cli_main())
