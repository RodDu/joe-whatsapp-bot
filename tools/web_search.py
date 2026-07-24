from __future__ import annotations
import asyncio
import json
import logging
import re
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional

logger = logging.getLogger('voice_router')

# Gemini API key set externally
_GEMINI_API_KEY = ''

def init(api_key: str):
    """Initialize the module with the Gemini API Key."""
    global _GEMINI_API_KEY
    _GEMINI_API_KEY = api_key


async def web_search(query: str) -> str:
    """Search the web using Gemini grounding or DuckDuckGo fallback."""
    if _GEMINI_API_KEY:
        try:
            return await _gemini_search(query)
        except Exception as exc:
            logger.warning('Gemini search failed: %s, using DuckDuckGo fallback', exc)
    return await _duckduckgo_search(query)


async def _gemini_search(query: str) -> str:
    def _do():
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={_GEMINI_API_KEY}'
        payload = {
            'contents': [{'parts': [{'text': f'Search and answer concisely: {query}'}]}],
            'tools': [{'google_search': {}}],
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            
        # Extract text
        candidates = result.get('candidates', [])
        if candidates:
            parts = candidates[0].get('content', {}).get('parts', [])
            texts = [p['text'] for p in parts if 'text' in p]
            return '\\n'.join(texts) if texts else 'No results.'
        return 'No search results.'
    return await asyncio.to_thread(_do)


async def _duckduckgo_search(query: str) -> str:
    def _do():
        encoded = urllib.parse.quote_plus(query)
        url = f'https://html.duckduckgo.com/html/?q={encoded}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='replace')
            
        # Simple HTML parse of results
        results = []
        for match in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            link = match.group(1)
            # Remove DuckDuckGo proxy url prefix if present
            if link.startswith('//duckduckgo.com/l/?uddg='):
                link = urllib.parse.unquote(link.split('uddg=')[1].split('&')[0])
                
            if title and link:
                results.append(f'- {title}\\n  {link}')
            if len(results) >= 5:
                break
                
        # Also attempt to grab snippets
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</[^>]+>', html, re.DOTALL)
        formatted = []
        for i, r_line in enumerate(results):
            formatted.append(r_line)
            if i < len(snippets):
                snip = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                if snip:
                    formatted.append(f'  {snip}')
                    
        return '\\n'.join(formatted) if formatted else 'No results found on DuckDuckGo.'
    return await asyncio.to_thread(_do)
