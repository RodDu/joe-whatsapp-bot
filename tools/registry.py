# -*- coding: utf-8 -*-
"""
registry.py — Central registry for tools using Gemini Function Calling schema.
"""
from __future__ import annotations
from typing import Any

# ============================================================
# TOOL DEFINITIONS (Gemini Function Calling format)
# ============================================================

TOOL_DECLARATIONS = [
    {
        "name": "web_search",
        "description": "Searches for information on the internet. Use when the user asks for current information, news, data you don't know, or anything that requires an online search.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "notes_search",
        "description": "Searches for notes in the knowledge base/notes directory. Use to find stored information, documents, logs, or any previously saved knowledge.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term to find relevant notes"
                },
                "folder": {
                    "type": "string",
                    "description": "Optional subfolder to restrict the search. Leave empty to search the entire notes directory."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "notes_read",
        "description": "Reads the full content of a specific note. Use when you already know which note you want to read.",
        "parameters": {
            "type": "object",
            "properties": {
                "note_path": {
                    "type": "string",
                    "description": "Relative path of the note within the notes directory (e.g. 'project_x.md', 'drafts/idea.md')"
                }
            },
            "required": ["note_path"]
        }
    },
    {
        "name": "tasks_list",
        "description": "Lists current tasks. Shows tasks to do, in progress, and done.",
        "parameters": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "description": "Optional filter: 'todo', 'doing', 'done', or 'all'"
                }
            }
        }
    },
    {
        "name": "tasks_add",
        "description": "Adds a new task to the 'To Do' section.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the task to add"
                }
            },
            "required": ["description"]
        }
    },
    {
        "name": "file_list",
        "description": "Lists files in a local directory. Use to check what is in a folder.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Path to the directory (e.g. 'C:\\Users\\user\\Documents')"
                },
                "pattern": {
                    "type": "string",
                    "description": "Optional glob filter (e.g. '*.txt', '*.json')"
                }
            },
            "required": ["directory"]
        }
    },
    {
        "name": "file_read",
        "description": "Reads the content of a local text file. Use to read documents, logs, configs, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Full path to the file"
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (default: 100)"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "memory_recall",
        "description": "Searches previous conversations and saved memories. Use when the user asks 'do you remember...', 'what did we talk about...', or needs context from past interactions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in memories/previous conversations"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "memory_save",
        "description": "Saves important information to persistent memory for future reference. Use when the user asks to remember something, or when important information arises in conversation.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The content to save to memory"
                },
                "tags": {
                    "type": "string",
                    "description": "Comma-separated tags for categorization"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "system_status",
        "description": "Checks the status of configured system services. Use when asked how the system is doing or to verify if a process is running.",
        "parameters": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Specific service name to check, or 'all' for all configured services"
                }
            }
        }
    },
    {
        "name": "run_command",
        "description": "Executes a PowerShell command on the computer. Use with caution and only when necessary for automation, status checking, or explicitly requested tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "PowerShell command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)"
                }
            },
            "required": ["command"]
        }
    },
]


def get_gemini_tools_payload() -> list[dict]:
    """Returns the tools payload in Gemini API format."""
    return [{"function_declarations": TOOL_DECLARATIONS}]


def get_tool_names() -> list[str]:
    """Returns a list of available tool names."""
    return [t["name"] for t in TOOL_DECLARATIONS]


def get_tools_description_text() -> str:
    """Returns a textual description of all tools (useful for local LLM fallback)."""
    lines = ["Available tools:"]
    for t in TOOL_DECLARATIONS:
        params = t.get("parameters", {}).get("properties", {})
        param_list = ", ".join(f"{k}: {v.get('description', '')}" for k, v in params.items())
        lines.append(f"- {t['name']}: {t['description']}")
        if param_list:
            lines.append(f"  Parameters: {param_list}")
    return "\\n".join(lines)
