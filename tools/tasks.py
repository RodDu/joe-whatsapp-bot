from __future__ import annotations
import asyncio
import json
import logging
import os
import re
from datetime import datetime

logger = logging.getLogger('voice_router')

def _get_tasks_file() -> str:
    """Returns the tasks file path from env var, config, or default."""
    if "TASKS_FILE" in os.environ:
        return os.environ["TASKS_FILE"]
        
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "tasksFile" in config:
                    return config["tasksFile"]
        except Exception:
            pass
            
    # Default
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "tasks.md")

def _ensure_tasks_file(filepath: str):
    """Creates the tasks file with sections if it doesn't exist."""
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Tasks\n\n## To Do\n\n## In Progress\n\n## Done\n")

async def tasks_list(filter: str = 'all') -> str:
    """Lists tasks from the tasks markdown file."""
    def _do():
        tasks_path = _get_tasks_file()
        _ensure_tasks_file(tasks_path)
        
        with open(tasks_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        sections = {'todo': [], 'doing': [], 'done': []}
        current = None
        
        for line in content.split('\\n'):
            line_stripped = line.strip()
            
            # Match English and Portuguese section headers
            if re.match(r'^##\s*(To\s*Do|A\s+Fazer)', line_stripped, re.IGNORECASE):
                current = 'todo'
            elif re.match(r'^##\s*(In\s*Progress|Em\s+Andamento)', line_stripped, re.IGNORECASE):
                current = 'doing'
            elif re.match(r'^##\s*(Done|Conclu[ííi]do|Feito)', line_stripped, re.IGNORECASE):
                current = 'done'
            elif line_stripped.startswith('## '):
                current = None
            elif current and re.match(r'^-\s*\[', line_stripped):
                sections[current].append(line_stripped)
                
        parts = []
        if filter in ('all', 'todo') and sections['todo']:
            parts.append('📝 To Do:\\n' + '\\n'.join(sections['todo']))
        if filter in ('all', 'doing') and sections['doing']:
            parts.append('🔄 In Progress:\\n' + '\\n'.join(sections['doing']))
        if filter in ('all', 'done') and sections['done']:
            last_done = sections['done'][-10:]  # Only last 10
            parts.append('✅ Done (recent):\\n' + '\\n'.join(last_done))
            
        if not parts:
            return 'No tasks found.'
            
        return '\\n\\n'.join(parts)
        
    return await asyncio.to_thread(_do)

async def tasks_add(description: str) -> str:
    """Adds a task to the To Do section."""
    def _do():
        tasks_path = _get_tasks_file()
        _ensure_tasks_file(tasks_path)
        
        with open(tasks_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
        # Find the To Do line and insert after it
        insert_idx = None
        for i, line in enumerate(lines):
            if re.match(r'^##\s*(To\s*Do|A\s+Fazer)', line.strip(), re.IGNORECASE):
                insert_idx = i + 1
                break
                
        if insert_idx is None:
            # If section doesn't exist, append it
            lines.extend(['\\n## To Do\\n'])
            insert_idx = len(lines)
            
        today = datetime.now().strftime('%Y-%m-%d')
        new_task = f'- [ ] {description} (added {today})\\n'
        lines.insert(insert_idx, new_task)
        
        with open(tasks_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        return f'Task added: {description}'
        
    return await asyncio.to_thread(_do)
