"""Textual theme registration helpers for HeloWrite."""

from typing import Any, Optional

from textual.theme import Theme

from config import Config
from utils import create_system_theme, get_system_theme_last_modified


def register_builtin_themes(app: Any) -> None:
    """Register HeloWrite's bundled themes with the app."""
    for theme in (
        Theme(
            name="helowrite-dark",
            primary="#7aa2f7",
            background="#1a1a2e",
            surface="#1a1a2e",
            foreground="#e6e6fa",
            dark=True,
        ),
        Theme(
            name="helowrite-light",
            primary="#61dafb",
            background="#ffffff",
            surface="#ffffff",
            foreground="#1a1a2e",
            dark=False,
        ),
        Theme(
            name="kanso-zen",
            primary="#8ba4b0",
            background="#090E13",
            surface="#090E13",
            foreground="#C5C9C7",
            dark=True,
        ),
        Theme(
            name="kanso-pearl",
            primary="#9fb5c9",
            background="#f2f1ef",
            surface="#f2f1ef",
            foreground="#22262D",
            dark=False,
        ),
    ):
        app.register_theme(theme)


def register_system_theme(
    app: Any,
    system_theme: Optional[dict] = None,
    last_modified: Optional[float] = None,
) -> tuple[Optional[dict], float]:
    """Register the discovered system theme and return its metadata."""
    system_theme = system_theme if system_theme is not None else create_system_theme()
    if not system_theme:
        return None, 0.0

    app.register_theme(theme_from_system_theme(system_theme))
    if last_modified is None:
        last_modified = get_system_theme_last_modified() or 0.0
    return system_theme, last_modified


def theme_from_system_theme(system_theme: dict) -> Theme:
    """Create a Textual theme from parsed system theme metadata."""
    return Theme(
        name="system",
        primary=system_theme["primary"],
        background=system_theme["background"],
        surface=system_theme["surface"],
        foreground=system_theme["foreground"],
        dark=system_theme["dark"],
    )


def choose_startup_theme(
    config: Config, available_themes: set[str], system_theme: Optional[dict]
) -> str:
    """Choose and persist the startup theme from config and system availability."""
    theme = config.get_theme()
    has_saved_theme = config.has_theme_preference()

    if system_theme and not has_saved_theme:
        config.set_theme("system")
        return "system"
    if theme == "system" and not system_theme:
        config.set_theme("helowrite-dark")
        return "helowrite-dark"
    if theme not in available_themes:
        config.set_theme("helowrite-dark")
        return "helowrite-dark"
    return theme


def apply_system_theme_update(app: Any, system_theme: dict) -> None:
    """Re-register the system theme and force Textual to apply its new colors."""
    app.register_theme(theme_from_system_theme(system_theme))
    app.theme = "textual-dark"
    app.theme = "system"
