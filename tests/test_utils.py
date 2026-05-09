"""Unit tests for ``src.utils`` helpers."""

from __future__ import annotations

import importlib
from pathlib import Path

import utils
from utils import detect_language


def test_detect_language_returns_text_when_no_path():
    assert detect_language(None) == "text"


def test_detect_language_matches_known_extension(tmp_path: Path):
    file_path = tmp_path / "notes.md"
    file_path.write_text("# Notes")

    assert detect_language(file_path) == "markdown"


def test_detect_language_falls_back_to_text(tmp_path: Path):
    file_path = tmp_path / "unknown.ext"
    file_path.write_text("data")

    assert detect_language(file_path) == "text"


def test_create_system_theme_uses_env_source_and_detects_light_mode(
    tmp_path: Path, monkeypatch
):
    colors_file = tmp_path / "colors.toml"
    colors_file.write_text(
        '\n'.join(
            [
                'accent = "#0066cc"',
                'background = "#f7f7f7"',
                'foreground = "#222222"',
            ]
        )
    )
    name_file = tmp_path / "theme.name"
    name_file.write_text("Solar")

    monkeypatch.setenv("HELOWWRITE_SYSTEM_THEME_FILE", str(colors_file))
    monkeypatch.setenv("HELOWWRITE_SYSTEM_THEME_NAME_FILE", str(name_file))
    importlib.reload(utils)

    theme = utils.create_system_theme()

    assert theme is not None
    assert theme["display_name"] == "Solar"
    assert theme["background"] == "#f7f7f7"
    assert theme["dark"] is False


def test_create_system_theme_supports_parent_theme_name_layout(
    tmp_path: Path, monkeypatch
):
    current_dir = tmp_path / "current"
    theme_dir = current_dir / "theme"
    theme_dir.mkdir(parents=True)

    colors_file = theme_dir / "colors.toml"
    colors_file.write_text(
        '\n'.join(
            [
                'accent = "#7aa2f7"',
                'background = "#1a1b26"',
                'foreground = "#a9b1d6"',
            ]
        )
    )
    (current_dir / "theme.name").write_text("Tokyo Night")

    monkeypatch.setenv("HELOWWRITE_SYSTEM_THEME_FILE", str(colors_file))
    monkeypatch.delenv("HELOWWRITE_SYSTEM_THEME_NAME_FILE", raising=False)
    importlib.reload(utils)

    theme = utils.create_system_theme()

    assert theme is not None
    assert theme["display_name"] == "Tokyo Night"
    assert theme["dark"] is True
