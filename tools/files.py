from __future__ import annotations
import asyncio
import fnmatch
import logging
import os
from datetime import datetime

logger = logging.getLogger('voice_router')

# Project root directory for security restrictions
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _is_allowed(path: str) -> bool:
    """Check if the path is within the project directory."""
    try:
        abs_path = os.path.abspath(path)
        return abs_path.startswith(_PROJECT_ROOT)
    except Exception:
        return False

async def file_list(directory: str, pattern: str = '*') -> str:
    """Lists files in a directory."""
    def _do():
        if not _is_allowed(directory):
            return f'Security block: Access denied to {directory}. Can only read within project folder.'
            
        if not os.path.isdir(directory):
            return f'Directory not found: {directory}'
            
        entries = []
        for name in os.listdir(directory):
            if not fnmatch.fnmatch(name, pattern):
                continue
                
            fpath = os.path.join(directory, name)
            try:
                stat = os.stat(fpath)
                is_dir = os.path.isdir(fpath)
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                icon = '📁' if is_dir else '📄'
                
                if size > 1_000_000:
                    size_str = f'{size/1_000_000:.1f}MB'
                elif size > 1000:
                    size_str = f'{size/1000:.1f}KB'
                else:
                    size_str = f'{size}B'
                    
                entries.append(f'{icon} {name}  ({size_str}, {mtime})')
            except Exception:
                entries.append(f'❓ {name}  (inaccessible)')
                
            if len(entries) >= 30:
                entries.append('... (more items omitted)')
                break
                
        if not entries:
            return f'Directory empty or no files match "{pattern}".'
            
        return f'Contents of {directory}:\\n\\n' + '\\n'.join(entries)
    return await asyncio.to_thread(_do)

async def file_read(file_path: str, max_lines: int = 100) -> str:
    """Reads content of a text file."""
    def _do():
        if not _is_allowed(file_path):
            return f'Security block: Access denied to {file_path}. Can only read within project folder.'
            
        if not os.path.isfile(file_path):
            return f'File not found: {file_path}'
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f'\\n[... file truncated at {max_lines} lines]')
                        break
                    lines.append(line)
            return ''.join(lines)
        except Exception as exc:
            return f'Error reading {file_path}: {exc}'
    return await asyncio.to_thread(_do)
