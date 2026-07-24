from __future__ import annotations
import asyncio
import logging
import subprocess
from typing import Any

logger = logging.getLogger('voice_router')

# Relative tool imports
from . import web_search as ws_mod
from . import notes as notes_mod
from . import tasks as tasks_mod
from . import files as files_mod
from . import memory as memory_mod
from . import status_collector as status_mod


async def execute_tool(tool_name: str, args: dict[str, Any]) -> str:
    """Central dispatcher mapping tool_name to its function."""
    logger.info('[EXECUTOR] Executing tool: %s with args: %s', tool_name, str(args)[:200])
    try:
        if tool_name == 'web_search':
            return await ws_mod.web_search(args.get('query', ''))
        elif tool_name == 'notes_search':
            return await notes_mod.notes_search(args.get('query', ''), args.get('folder', ''))
        elif tool_name == 'notes_read':
            return await notes_mod.notes_read(args.get('note_path', ''))
        elif tool_name == 'tasks_list':
            return await tasks_mod.tasks_list(args.get('filter', 'all'))
        elif tool_name == 'tasks_add':
            return await tasks_mod.tasks_add(args.get('description', ''))
        elif tool_name == 'file_list':
            return await files_mod.file_list(args.get('directory', ''), args.get('pattern', '*'))
        elif tool_name == 'file_read':
            return await files_mod.file_read(args.get('file_path', ''), args.get('max_lines', 100))
        elif tool_name == 'memory_save':
            return await memory_mod.memory_save(args.get('content', ''), args.get('tags', ''))
        elif tool_name == 'memory_recall':
            return await memory_mod.memory_recall(args.get('query', ''))
        elif tool_name == 'system_status':
            return await status_mod.check_system_status(args.get('service', 'all'))
        elif tool_name == 'run_command':
            return await _run_command(args.get('command', ''), args.get('timeout', 30))
        else:
            return f'Unknown tool: {tool_name}'
    except Exception as exc:
        logger.error('[EXECUTOR] Error in %s: %s', tool_name, exc)
        return f'Error executing {tool_name}: {exc}'


async def _run_command(command: str, timeout: int = 30) -> str:
    """Executes a PowerShell/Shell command with a timeout."""
    def _do():
        # Basic security blocklist
        blocked = ['rm -rf', 'format c:', 'format d:', 'del /s /q c:\\', 'Remove-Item -Recurse -Force C:\\']
        for b in blocked:
            if b.lower() in command.lower():
                return f'Command blocked for security: contains "{b}"'
        try:
            # Note: This defaults to powershell on Windows, but could be adapted for cross-platform
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', command],
                capture_output=True, text=True, encoding='utf-8',
                timeout=min(timeout, 120)  # Max 2 minutes
            )
            output = result.stdout.strip()
            errors = result.stderr.strip()
            if result.returncode != 0 and errors:
                return f'Error (code {result.returncode}):\\n{errors}'
            return output if output else '(command executed with no output)'
        except subprocess.TimeoutExpired:
            return f'Command timed out after {timeout}s.'
        except Exception as exc:
            return f'Error executing command: {exc}'
    return await asyncio.to_thread(_do)
