"""Unit tests for ``src.config.Config``."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config import Config


def read_raw_config(config_dir: Path) -> str:
    return (config_dir / "config.conf").read_text()


def test_config_uses_custom_directory(temp_config_dir: Path) -> None:
    config = Config(config_dir=temp_config_dir)
    config.set_theme("textual-light")

    assert "theme=textual-light" in read_raw_config(temp_config_dir)


@pytest.mark.parametrize(
    "setter,value,expected",
    [
        ("set_editor_width", 55, "editor_width=55"),
        ("set_bottom_padding", 2, "bottom_padding=2"),
        ("set_distraction_top_padding", 3, "distraction_top_padding=3"),
        ("set_cursor_color", "#ffffff", "cursor_color=#ffffff"),
        ("set_open_last_file", True, "open_last_file=1"),
    ],
)
def test_config_setters_persist_values(temp_config_dir: Path, setter, value, expected):
    config = Config(config_dir=temp_config_dir)
    getattr(config, setter)(value)

    assert expected in read_raw_config(temp_config_dir)


def test_recent_files_keeps_latest_five(temp_config_dir: Path) -> None:
    config = Config(config_dir=temp_config_dir)
    for idx in range(7):
        config.add_recent_file(f"/tmp/file{idx}.md")

    assert config.get_recent_files() == [
        "/tmp/file6.md",
        "/tmp/file5.md",
        "/tmp/file4.md",
        "/tmp/file3.md",
        "/tmp/file2.md",
    ]


def test_recent_files_move_existing_to_front(temp_config_dir: Path) -> None:
    config = Config(config_dir=temp_config_dir)
    for idx in range(3):
        config.add_recent_file(f"/tmp/file{idx}.md")

    config.add_recent_file("/tmp/file1.md")

    assert config.get_recent_files()[0] == "/tmp/file1.md"
