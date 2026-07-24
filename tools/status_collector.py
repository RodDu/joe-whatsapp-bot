from __future__ import annotations
import asyncio
import json
import logging
import os
import subprocess
import platform
import urllib.request
from typing import Any

logger = logging.getLogger('voice_router')

def _load_services() -> list[dict[str, Any]]:
    """Loads services to monitor from config.json"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.example.json")
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("monitoring", {}).get("services", [])
    except Exception as e:
        logger.error("[STATUS] Error loading config: %s", e)
        return []

def _check_http(url: str, timeout: int = 3) -> bool:
    """Checks if an HTTP endpoint is reachable."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except Exception:
        # Fallback to GET if HEAD is not supported
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout):
                return True
        except Exception:
            return False

def _check_process_windows(process_name: str) -> str:
    """Checks for a process on Windows using PowerShell."""
    try:
        cmd = f"Get-Process -Name '{process_name.replace('.exe','')}' -ErrorAction SilentlyContinue | Select-Object Id | Measure-Object | Select-Object -ExpandProperty Count"
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', cmd],
            capture_output=True, text=True, timeout=5
        )
        count = result.stdout.strip()
        if count and count != '0':
            return f"🟢 ACTIVE ({count} instances)"
        return "🔴 INACTIVE"
    except Exception as e:
        return f"⚠️ Error checking process: {e}"

def _check_process_unix(process_name: str) -> str:
    """Checks for a process on Unix using ps/grep."""
    try:
        cmd = f"ps aux | grep -i '{process_name}' | grep -v grep | wc -l"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        count = result.stdout.strip()
        if count and count != '0':
            return f"🟢 ACTIVE ({count} instances)"
        return "🔴 INACTIVE"
    except Exception as e:
        return f"⚠️ Error checking process: {e}"

async def check_system_status(service: str = 'all') -> str:
    """Checks the status of system services."""
    def _do():
        services = _load_services()
        if not services:
            return "No services configured for monitoring."
            
        if service != 'all':
            # Filter specific service
            services = [s for s in services if s.get('name', '').lower() == service.lower()]
            if not services:
                return f"Service '{service}' not found in configuration."
                
        parts = []
        is_windows = platform.system().lower() == 'windows'
        
        for svc in services:
            name = svc.get('name', 'Unknown')
            check_type = svc.get('check', 'unknown')
            desc = svc.get('description', '')
            
            label = f"{name}"
            if desc:
                label += f" ({desc})"
                
            if check_type == 'http':
                url = svc.get('url', '')
                if not url:
                    parts.append(f"⚠️ {label}: Invalid HTTP config (missing url)")
                    continue
                    
                is_up = _check_http(url)
                if is_up:
                    parts.append(f"🟢 {label}: ONLINE")
                else:
                    parts.append(f"🔴 {label}: OFFLINE (unreachable)")
                    
            elif check_type == 'process':
                proc_name = svc.get('processName', '')
                if not proc_name:
                    parts.append(f"⚠️ {label}: Invalid Process config (missing processName)")
                    continue
                    
                if is_windows:
                    status = _check_process_windows(proc_name)
                else:
                    status = _check_process_unix(proc_name)
                    
                parts.append(f"{status.split(' ')[0]} {label}: {status[2:].strip()}")
                
            else:
                parts.append(f"⚠️ {label}: Unknown check type '{check_type}'")
                
        return "\\n\\n".join(parts) if parts else "No results."
        
    return await asyncio.to_thread(_do)
