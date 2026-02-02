"""Utility functions for HeloWrite."""

import subprocess
from pathlib import Path
from typing import Optional


def has_nerd_fonts() -> bool:
    """Check if Nerd Fonts are installed."""
    try:
        result = subprocess.run(["fc-list"], capture_output=True, text=True, timeout=2)
        return "Nerd Font" in result.stdout
    except Exception:
        return False


def detect_language(file_path: Optional[Path]) -> str:
    """Detect programming language from file extension."""
    if not file_path:
        return "text"

    ext = file_path.suffix.lower()
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".md": "markdown",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        ".sql": "sql",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".rs": "rust",
        ".go": "go",
        ".php": "php",
        ".rb": "ruby",
        ".pl": "perl",
        ".r": "r",
        ".scala": "scala",
        ".kt": "kotlin",
        ".swift": "swift",
        ".dart": "dart",
        ".lua": "lua",
        ".vim": "vim",
        ".dockerfile": "dockerfile",
    }
    return language_map.get(ext, "text")
