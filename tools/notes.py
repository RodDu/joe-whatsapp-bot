from __future__ import annotations
import asyncio
import json
import logging
import os
from typing import Optional

logger = logging.getLogger('voice_router')

def _get_notes_dir() -> str:
    """Returns the notes directory from env var, config, or default."""
    if "NOTES_DIR" in os.environ:
        return os.environ["NOTES_DIR"]
        
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "notesDir" in config:
                    return config["notesDir"]
        except Exception:
            pass
            
    # Default
    default_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "notes")
    if not os.path.exists(default_dir):
        os.makedirs(default_dir, exist_ok=True)
    return default_dir

async def notes_search(query: str, folder: str = '') -> str:
    """Searches for notes in the directory that contain the query."""
    def _do():
        notes_root = _get_notes_dir()
        search_root = os.path.join(notes_root, folder) if folder else notes_root
        
        if not os.path.isdir(search_root):
            return f'Directory not found: {search_root}'
            
        query_lower = query.lower()
        results = []
        
        for dirpath, _, filenames in os.walk(search_root):
            # Skip hidden folders
            if any(part.startswith('.') for part in dirpath.replace(notes_root, '').split(os.sep)):
                continue
                
            for fname in filenames:
                if not fname.endswith(('.md', '.txt')):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                        
                    if query_lower in content.lower():
                        # Find snippet with context
                        idx = content.lower().find(query_lower)
                        start = max(0, idx - 80)
                        end = min(len(content), idx + len(query) + 80)
                        snippet = content[start:end].replace('\\n', ' ').strip()
                        rel_path = os.path.relpath(fpath, notes_root)
                        results.append(f'📝 {rel_path}\\n   ...{snippet}...')
                except Exception:
                    continue
                
                if len(results) >= 10:
                    break
            if len(results) >= 10:
                break
                
        if not results:
            return f'No notes found containing "{query}".'
            
        return f'Found {len(results)} note(s):\\n\\n' + '\\n\\n'.join(results)
        
    return await asyncio.to_thread(_do)

async def notes_read(note_path: str) -> str:
    """Reads the content of a note."""
    def _do():
        notes_root = _get_notes_dir()
        full_path = os.path.join(notes_root, note_path)
        
        # Prevent directory traversal
        if not os.path.abspath(full_path).startswith(os.path.abspath(notes_root)):
            return "Security block: Cannot read files outside the notes directory."
            
        if not os.path.isfile(full_path):
            # Try with .md extension
            if not full_path.endswith('.md') and not full_path.endswith('.txt'):
                full_path += '.md'
            if not os.path.isfile(full_path):
                return f'Note not found: {note_path}'
                
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            if len(content) > 5000:
                return content[:5000] + f'\\n\\n[... note truncated, total of {len(content)} characters]'
            return content
        except Exception as exc:
            return f'Error reading note: {exc}'
            
    return await asyncio.to_thread(_do)
