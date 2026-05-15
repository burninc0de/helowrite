"""Tests for Textual theme helpers."""

from __future__ import annotations

from pathlib import Path

from config import Config
from themes import choose_startup_theme, register_builtin_themes, register_system_theme


class FakeApp:
    """Small stand-in that records registered theme names."""

    def __init__(self) -> None:
        self.registered: list[str] = []

    def register_theme(self, theme) -> None:
        self.registered.append(theme.name)


def system_theme() -> dict:
    """Return a minimal parsed system theme."""
    return {
        "name": "system",
        "display_name": "System",
        "primary": "#5ea1ff",
        "background": "#101010",
        "surface": "#101010",
        "foreground": "#f0f0f0",
        "dark": True,
    }


def test_register_builtin_themes_registers_all_defaults() -> None:
    app = FakeApp()

    register_builtin_themes(app)

    assert app.registered == [
        "helowrite-dark",
        "helowrite-light",
        "kanso-zen",
        "kanso-pearl",
    ]


def test_register_system_theme_registers_theme_and_returns_metadata() -> None:
    app = FakeApp()
    theme = system_theme()

    registered, last_modified = register_system_theme(
        app, system_theme=theme, last_modified=123.0
    )

    assert registered == theme
    assert last_modified == 123.0
    assert app.registered == ["system"]


def test_choose_startup_theme_uses_system_on_first_launch(
    temp_config_dir: Path,
) -> None:
    config = Config(config_dir=temp_config_dir)
    config.set_show_welcome(False)

    theme = choose_startup_theme(
        config,
        {"helowrite-dark", "system"},
        system_theme(),
    )

    assert theme == "system"
    assert config.get_theme() == "system"


def test_choose_startup_theme_preserves_saved_choice(temp_config_dir: Path) -> None:
    config = Config(config_dir=temp_config_dir)
    config.set_theme("kanso-pearl")

    theme = choose_startup_theme(
        config,
        {"helowrite-dark", "kanso-pearl", "system"},
        system_theme(),
    )

    assert theme == "kanso-pearl"
    assert config.get_theme() == "kanso-pearl"


def test_choose_startup_theme_falls_back_when_system_missing(
    temp_config_dir: Path,
) -> None:
    config = Config(config_dir=temp_config_dir)
    config.set_theme("system")

    theme = choose_startup_theme(config, {"helowrite-dark"}, None)

    assert theme == "helowrite-dark"
    assert config.get_theme() == "helowrite-dark"
