"""Utility functions for HeloWrite."""

import os
import subprocess
from pathlib import Path
from typing import Optional

SYSTEM_THEME_SOURCES = [
    Path.home() / ".config/omarchy/current/theme/colors.toml",
    Path.home() / ".config/helowrite/system-theme/colors.toml",
]


def has_nerd_fonts() -> bool:
    """Check if Nerd Fonts are installed."""
    try:
        result = subprocess.run(["fc-list"], capture_output=True, text=True, timeout=2)
        return "Nerd Font" in result.stdout
    except Exception:
        return False


def _resolve_system_theme_files() -> tuple[Optional[Path], Optional[Path]]:
    """Resolve colors and name files for the active system theme source."""
    custom_colors = (
        Path(env).expanduser()
        if (env := os.environ.get("HELOWWRITE_SYSTEM_THEME_FILE"))
        else None
    )
    colors_candidates = []
    if custom_colors:
        colors_candidates.append(custom_colors)
    colors_candidates.extend(SYSTEM_THEME_SOURCES)

    colors_file: Optional[Path] = next(
        (candidate for candidate in colors_candidates if candidate.exists()), None
    )
    if not colors_file:
        return None, None

    custom_name = (
        Path(env).expanduser()
        if (env := os.environ.get("HELOWWRITE_SYSTEM_THEME_NAME_FILE"))
        else None
    )
    if custom_name and custom_name.exists():
        return colors_file, custom_name

    name_candidates = [
        colors_file.parent / "theme.name",
        colors_file.parent.parent / "theme.name",
    ]
    name_file = next(
        (candidate for candidate in name_candidates if candidate.exists()), None
    )
    return colors_file, name_file


def _is_dark_color(hex_color: str) -> bool:
    """Infer dark/light mode from a hex color using relative luminance."""
    normalized = hex_color.strip().lstrip("#")
    if len(normalized) == 3:
        normalized = "".join(ch * 2 for ch in normalized)
    if len(normalized) != 6:
        return True

    try:
        red = int(normalized[0:2], 16)
        green = int(normalized[2:4], 16)
        blue = int(normalized[4:6], 16)
    except ValueError:
        return True

    luminance = (0.299 * red) + (0.587 * green) + (0.114 * blue)
    return luminance < 140


def is_system_theme_available() -> bool:
    """Check if system theme is available."""
    colors_file, _ = _resolve_system_theme_files()
    return colors_file is not None


def get_system_theme_name(name_file: Optional[Path] = None) -> Optional[str]:
    """Get the current system theme name."""
    _, resolved_name_file = _resolve_system_theme_files()
    candidate = name_file or resolved_name_file
    if not candidate:
        return None
    try:
        return candidate.read_text().strip()
    except Exception:
        pass
    return None


def parse_system_theme_colors(theme_file: Optional[Path] = None) -> dict[str, str]:
    """Parse system theme colors into a dict."""
    colors = {}
    resolved_theme_file, _ = _resolve_system_theme_files()
    candidate = theme_file or resolved_theme_file
    if not candidate:
        return colors

    try:
        content = candidate.read_text()
        for line in content.splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                colors[key.strip()] = value.strip().strip('"')
    except Exception:
        pass

    return colors


def get_system_theme_last_modified() -> Optional[float]:
    """Return the most recent mtime across active system theme source files."""
    colors_file, name_file = _resolve_system_theme_files()
    if not colors_file:
        return None

    mtimes = []
    for candidate in (colors_file, name_file):
        if candidate and candidate.exists():
            try:
                mtimes.append(candidate.stat().st_mtime)
            except Exception:
                pass

    if not mtimes:
        return None
    return max(mtimes)


def create_system_theme() -> Optional[dict]:
    """Create a theme dict from system theme."""
    colors_file, name_file = _resolve_system_theme_files()
    if not colors_file:
        return None

    colors = parse_system_theme_colors(colors_file)
    if not colors:
        return None

    theme_name = get_system_theme_name(name_file) or "System"
    background = colors.get("background", "#1a1b26")

    return {
        "name": "system",
        "display_name": theme_name,
        "primary": colors.get("accent", "#7aa2f7"),
        "background": background,
        "surface": background,
        "foreground": colors.get("foreground", "#a9b1d6"),
        "cursor": colors.get("cursor", "#c0caf5"),
        "selection_bg": colors.get("selection_background", "#7aa2f7"),
        "selection_fg": colors.get("selection_foreground", "#c0caf5"),
        "dark": _is_dark_color(background),
        "colors": colors,
        "source_colors_file": str(colors_file),
        "source_name_file": str(name_file) if name_file else "",
    }


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
