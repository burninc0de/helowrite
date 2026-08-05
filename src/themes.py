"""Textual theme registration helpers for HeloWrite."""

from typing import TYPE_CHECKING, Any, Optional

from textual.theme import Theme

from config import Config
from utils import (
    create_system_theme,
    get_system_theme_last_modified,
    is_system_theme_available,
)

if TYPE_CHECKING:
    from app import HeloWrite


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


def start_system_theme_watcher(app: "HeloWrite") -> None:
    """Enable periodic checks for active system theme changes."""
    if app._system_watcher_active:
        return
    if not app._system_theme:
        return
    app._system_watcher_timer = app.set_interval(
        app._system_watch_interval_seconds,
        lambda: check_system_theme_update(app),
    )
    app._system_watcher_active = True


def stop_system_theme_watcher(app: "HeloWrite") -> None:
    """Disable periodic checks for system theme changes."""
    if app._system_watcher_timer:
        app._system_watcher_timer.stop()
        app._system_watcher_timer = None
    app._system_watcher_active = False


def check_system_theme_update_once(app: "HeloWrite") -> None:
    """Check system theme once on startup; start watcher if system theme is available."""
    if not app._system_theme:
        return
    if app.theme != "system":
        return
    check_system_theme_update(app)
    if app._system_theme:
        start_system_theme_watcher(app)


def fallback_to_default_theme(app: "HeloWrite") -> None:
    """Fallback when system theme disappears or becomes invalid."""
    app._system_theme = None
    app._system_last_check = 0.0
    stop_system_theme_watcher(app)
    app.theme = "helowrite-dark"
    app.config.set_theme("helowrite-dark")
    app.notify(
        "System theme unavailable. Falling back to helowrite-dark.",
        severity="warning",
    )


def check_system_theme_update(app: "HeloWrite") -> None:
    """Check if system theme has changed and update if needed."""
    if not is_system_theme_available():
        if app.theme == "system":
            fallback_to_default_theme(app)
        return

    if not app._system_theme:
        app._system_theme = create_system_theme()
        app._system_last_check = get_system_theme_last_modified() or 0.0
        if not app._system_theme:
            return

    try:
        current_mtime = get_system_theme_last_modified() or 0.0
        if current_mtime > app._system_last_check:
            new_system_theme = create_system_theme()
            if new_system_theme:
                app._system_theme = new_system_theme
                app._system_last_check = current_mtime
                if app.theme == "system":
                    app._applying_system_update = True
                    try:
                        apply_system_theme_update(app, new_system_theme)
                    finally:
                        app._applying_system_update = False

                    app.refresh_css()
                    app.screen.refresh()
                    app.apply_cursor_color()
            elif app.theme == "system":
                fallback_to_default_theme(app)
    except Exception:
        pass
