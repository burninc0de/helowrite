"""Unit tests for ``src.utils`` helpers."""

from __future__ import annotations

from pathlib import Path

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
