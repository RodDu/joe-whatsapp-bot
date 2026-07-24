from __future__ import annotations
import asyncio
import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger('voice_router')

def _get_memory_file() -> str:
    """Returns the memory file path from env var, config, or default."""
    if "MEMORY_DIR" in os.environ:
        mem_dir = os.environ["MEMORY_DIR"]
    else:
        mem_dir = None
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    if "memoryDir" in config:
                        mem_dir = config["memoryDir"]
            except Exception:
                pass
                
        if not mem_dir:
            # Default
            mem_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "memory")
            
    os.makedirs(mem_dir, exist_ok=True)
    return os.path.join(mem_dir, "bot_memory.jsonl")

async def memory_save(content: str, tags: str = '') -> str:
    """Saves information to persistent memory."""
    def _do():
        memory_file = _get_memory_file()
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'content': content,
            'tags': [t.strip() for t in tags.split(',') if t.strip()] if tags else []
        }
        with open(memory_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\\n')
        return f'Memory saved successfully. Tags: {entry["tags"] or "none"}'
    return await asyncio.to_thread(_do)

async def memory_recall(query: str) -> str:
    """Searches previous memories."""
    def _do():
        memory_file = _get_memory_file()
        if not os.path.isfile(memory_file):
            return 'No memories saved yet.'
            
        query_lower = query.lower()
        matches = []
        with open(memory_file, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                    
                content = entry.get('content', '')
                tags_str = ' '.join(entry.get('tags', []))
                
                if query_lower in content.lower() or query_lower in tags_str.lower():
                    ts = entry.get('timestamp', '?')
                    # format ISO timestamp
                    if 'T' in ts:
                        ts = ts.split('T')[0]
                    tag_display = f' [{tags_str}]' if tags_str else ''
                    matches.append(f'💬 {ts}{tag_display}\\n   {content}')
                    
        if not matches:
            return f'No memory found containing "{query}".'
            
        # Return last 5
        recent = matches[-5:]
        return f'Found {len(matches)} memory(ies) (showing {len(recent)} recent):\\n\\n' + '\\n\\n'.join(recent)
    return await asyncio.to_thread(_do)
