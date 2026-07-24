# -*- coding: utf-8 -*-
"""
agent.py — Agent loop with Gemini Function Calling + local LLM fallback (Ollama)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any, Optional

from .registry import get_gemini_tools_payload, get_tools_description_text

logger = logging.getLogger("voice_router")

# ============================================================
# CONFIGURATION
# ============================================================
_GEMINI_API_KEY: str = ""
_OLLAMA_BASE_URL: str = "http://localhost:11434"
_OLLAMA_MODEL: str = "gemma2"
_SYSTEM_PROMPT: str = ""

# Tool executor (will be injected on init)
_tool_executor = None

def _load_config() -> dict:
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.example.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("[AGENT] Error loading config: %s", e)
        return {}


def init(gemini_api_key: str, ollama_base_url: str, ollama_model: str, tool_executor):
    """Initializes the agent with settings and tool executor."""
    global _GEMINI_API_KEY, _OLLAMA_BASE_URL, _OLLAMA_MODEL, _tool_executor, _SYSTEM_PROMPT
    _GEMINI_API_KEY = gemini_api_key
    _OLLAMA_BASE_URL = ollama_base_url
    _OLLAMA_MODEL = ollama_model
    _tool_executor = tool_executor

    config = _load_config()
    bot_config = config.get("bot", {})
    bot_name = bot_config.get("name", "Assistant")
    user_title = bot_config.get("userTitle", "User")
    custom_prompt = bot_config.get("systemPrompt", "")

    if custom_prompt:
        _SYSTEM_PROMPT = custom_prompt
    else:
        _SYSTEM_PROMPT = f"""You are {bot_name}, a personal assistant AI. You communicate via WhatsApp.

Your personality:
- Efficient, direct, but with a touch of warmth
- Address the user as "{user_title}" if appropriate
- Always execute requested actions instead of just suggesting them

You have access to powerful tools. USE THEM actively:
- For factual/current questions -> web_search
- For knowledge base/documents -> notes_search / notes_read
- For tasks -> tasks_list / tasks_add
- To view files -> file_list / file_read
- To remember things -> memory_recall / memory_save
- For system status -> system_status
- For automation -> run_command

RULES:
1. ALWAYS use tools when a question requires information you don't have
2. Never invent information — search first
3. Be concise — the user is on a small screen
4. Use emojis sparingly for visual clarity
"""


# ============================================================
# GEMINI FUNCTION CALLING (REST API)
# ============================================================

def _gemini_request(contents: list[dict], tools: Optional[list] = None, model: str = "gemini-2.5-flash") -> dict:
    """REST call to Gemini with function calling support."""
    if not _GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={_GEMINI_API_KEY}"
    
    payload: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        },
        "systemInstruction": {
            "parts": [{"text": _SYSTEM_PROMPT}]
        },
    }
    
    if tools:
        payload["tools"] = tools
        # Allow the model to call tools OR generate text
        payload["toolConfig"] = {
            "functionCallingConfig": {
                "mode": "AUTO"
            }
        }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_response(result: dict) -> tuple[Optional[str], Optional[list[dict]]]:
    """
    Extracts text and/or function calls from Gemini response.
    Returns (text, function_calls) where function_calls is a list of {name, args}.
    """
    candidates = result.get("candidates", [])
    if not candidates:
        return "I didn't receive a response from the model.", None
    
    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    
    text_parts = []
    function_calls = []
    
    for part in parts:
        if "text" in part:
            text_parts.append(part["text"])
        elif "functionCall" in part:
            fc = part["functionCall"]
            function_calls.append({
                "name": fc["name"],
                "args": fc.get("args", {})
            })
    
    text = "\\n".join(text_parts) if text_parts else None
    return text, function_calls if function_calls else None


# ============================================================
# MAIN AGENT LOOP
# ============================================================

async def run_agent(user_message: str, max_iterations: int = 5) -> str:
    """
    Runs the agent loop with tool-calling.
    
    1. Sends message + tools to Gemini
    2. If Gemini returns function_call -> executes and resends
    3. If Gemini returns text -> returns as final response
    4. Fallback to local LLM if Gemini is unavailable
    """
    logger.info("[AGENT] Starting agent loop for: '%s'", user_message[:100])
    
    # Try Gemini with tools first
    if _GEMINI_API_KEY:
        try:
            return await _run_gemini_agent(user_message, max_iterations)
        except Exception as exc:
            logger.info("[AGENT] Gemini unavailable (%s), using local fallback", exc)
    
    # Fallback: Local LLM via Ollama
    return await _run_local_fallback(user_message)


async def _run_gemini_agent(user_message: str, max_iterations: int) -> str:
    """Agent loop using Gemini with native function calling."""
    tools = get_gemini_tools_payload()
    
    # Message history
    contents = [
        {"role": "user", "parts": [{"text": user_message}]}
    ]
    
    for iteration in range(max_iterations):
        logger.info("[AGENT] Iteration %d/%d", iteration + 1, max_iterations)
        
        # Call Gemini
        result = await asyncio.to_thread(_gemini_request, contents, tools)
        text, function_calls = _extract_response(result)
        
        # If there are no function calls, return the text
        if not function_calls:
            logger.info("[AGENT] Final response received (%d chars)", len(text or ""))
            return text or "I couldn't generate a response."
        
        # Execute function calls
        logger.info("[AGENT] %d tool call(s) to execute", len(function_calls))
        
        # Add model's function calls to history
        model_parts = []
        for fc in function_calls:
            model_parts.append({"functionCall": {"name": fc["name"], "args": fc["args"]}})
        contents.append({"role": "model", "parts": model_parts})
        
        # Execute each tool and collect results
        tool_response_parts = []
        for fc in function_calls:
            tool_name = fc["name"]
            tool_args = fc["args"]
            logger.info("[AGENT] Executing tool: %s(%s)", tool_name, json.dumps(tool_args, ensure_ascii=False)[:200])
            
            try:
                result_text = await _tool_executor(tool_name, tool_args)
                # Truncate very long results to avoid context overflow
                if len(result_text) > 4000:
                    result_text = result_text[:4000] + "\\n\\n[... result truncated, showing first 4000 characters]"
            except Exception as exc:
                result_text = f"Error executing {tool_name}: {exc}"
                logger.error("[AGENT] Error in tool %s: %s", tool_name, exc)
            
            tool_response_parts.append({
                "functionResponse": {
                    "name": tool_name,
                    "response": {"result": result_text}
                }
            })
        
        # Add results to history
        contents.append({"role": "user", "parts": tool_response_parts})
    
    # If out of iterations, ask for final response without tools
    logger.info("[AGENT] Iteration limit reached, requesting final response")
    result = await asyncio.to_thread(_gemini_request, contents, None)
    text, _ = _extract_response(result)
    return text or "Processing exceeded the iteration limit."


async def _run_local_fallback(user_message: str) -> str:
    """
    Fallback using local LLM via Ollama.
    No native function calling — uses prompt engineering.
    """
    tools_desc = get_tools_description_text()
    
    prompt = f"""Respond to the user's question.

If you need to use a tool, respond ONLY with a JSON in this format:
{{"tool": "tool_name", "args": {{"param": "value"}}}}

If you DO NOT need a tool, respond directly in text.

{tools_desc}

User question: {user_message}"""

    url = f"{_OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": _OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 1024, "num_ctx": 4096},
        "system": _SYSTEM_PROMPT,
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    def _do_request():
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read().decode("utf-8"))
    
    result = await asyncio.to_thread(_do_request)
    response_text = result.get("response", "").strip()
    
    # Try to parse as a tool call
    try:
        # Look for JSON in text
        json_match = response_text
        if "```" in response_text:
            import re
            match = re.search(r'```(?:json)?\\s*(\\{.*?\\})\\s*```', response_text, re.DOTALL)
            if match:
                json_match = match.group(1)
        
        tool_call = json.loads(json_match)
        if "tool" in tool_call and "args" in tool_call:
            tool_name = tool_call["tool"]
            tool_args = tool_call["args"]
            logger.info("[AGENT-FALLBACK] Local LLM requested tool: %s", tool_name)
            
            tool_result = await _tool_executor(tool_name, tool_args)
            
            # Second call with the result
            followup_prompt = f"""Result of the tool {tool_name}: 

{tool_result[:3000]}

Now answer the user's original question based on this result: {user_message}

Be concise."""

            payload["prompt"] = followup_prompt
            data = json.dumps(payload).encode("utf-8")
            req2 = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            result2 = await asyncio.to_thread(lambda: urllib.request.urlopen(req2, timeout=600).read())
            return json.loads(result2.decode("utf-8")).get("response", "").strip()
    except (json.JSONDecodeError, KeyError, TypeError):
        pass  # Was not a tool call, return text directly
    
    return response_text
