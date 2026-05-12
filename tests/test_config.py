"""Unit tests for ``src.config.Config``."""

from __future__ import annotations

from pathlib import Path

import pytest

from config import Config


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
        ("set_space_between_paragraphs", True, "space_between_paragraphs=1"),
    ],
)
def test_config_setters_persist_values(temp_config_dir: Path, setter, value, expected):
    config = Config(config_dir=temp_config_dir)
    getattr(config, setter)(value)

    assert expected in read_raw_config(temp_config_dir)


def test_snippet_highlighting_setting_persists(temp_config_dir: Path) -> None:
    config = Config(config_dir=temp_config_dir)
    config.set_snippet_highlighting_enabled(False)

    assert "snippet_highlighting_enabled=0" in read_raw_config(temp_config_dir)
    assert config.get_snippet_highlighting_enabled() is False


def test_markdown_highlighting_setting_persists(temp_config_dir: Path) -> None:
    config = Config(config_dir=temp_config_dir)
    config.set_markdown_highlighting_enabled(False)

    assert "markdown_highlighting_enabled=0" in read_raw_config(temp_config_dir)
    assert config.get_markdown_highlighting_enabled() is False


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


def test_smart_quote_replacements_defaults_and_persistence(
    temp_config_dir: Path,
) -> None:
    config = Config(config_dir=temp_config_dir)

    assert config.get_smart_quote_open_single() == "\u2018"
    assert config.get_smart_quote_close_single() == "\u2019"
    assert config.get_smart_quote_open_double() == "\u201c"
    assert config.get_smart_quote_close_double() == "\u201d"

    config.set_smart_quote_open_single("<")
    config.set_smart_quote_close_single(">")
    config.set_smart_quote_open_double("[")
    config.set_smart_quote_close_double("]")

    assert config.get_smart_quote_open_single() == "<"
    assert config.get_smart_quote_close_single() == ">"
    assert config.get_smart_quote_open_double() == "["
    assert config.get_smart_quote_close_double() == "]"


def test_config_file_is_written_in_utf8_for_smart_quotes(
    temp_config_dir: Path,
) -> None:
    config = Config(config_dir=temp_config_dir)
    config.set_smart_quote_open_double("\u201c")

    raw = (temp_config_dir / "config.conf").read_bytes()
    assert b"\xe2\x80\x9c" in raw
