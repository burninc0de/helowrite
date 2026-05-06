"""Unit tests for ``src.snippets``."""

from __future__ import annotations

from pathlib import Path

import pytest

from snippets import SnippetEngine, expand_placeholders, find_trigger


class TestExpandPlaceholders:
    def test_currenttime(self) -> None:
        result = expand_placeholders("Time: %CURRENTTIME")
        import re
        assert re.search(r"\d{2}:\d{2}", result)

    def test_escaped_percent(self) -> None:
        result = expand_placeholders("100%%")
        assert result == "100%"

    def test_unknown_placeholder_unchanged(self) -> None:
        result = expand_placeholders("foo %UNKNOWN bar")
        assert result == "foo %UNKNOWN bar"

    def test_escape_newline(self) -> None:
        result = expand_placeholders("line1\\nline2")
        assert result == "line1\nline2"

    def test_escape_tab(self) -> None:
        result = expand_placeholders("a\\tb")
        assert result == "a\tb"

    def test_escape_backslash_n(self) -> None:
        result = expand_placeholders("\\\\n")
        assert result == "\\n"


class TestFindTrigger:
    def test_exact_match_at_start(self) -> None:
        trigger, start, end = find_trigger("ttt", ["ttt"])
        assert trigger == "ttt"
        assert start == 0
        assert end == 3

    def test_match_after_space(self) -> None:
        trigger, start, end = find_trigger("hello ttt", ["ttt"])
        assert trigger == "ttt"
        assert start == 6
        assert end == 9

    def test_no_match_after_letter(self) -> None:
        trigger, start, end = find_trigger("hellottt", ["ttt"])
        assert trigger is None

    def test_longest_match_wins(self) -> None:
        trigger, start, end = find_trigger("ttttt", ["ttt", "ttttt"])
        assert trigger == "ttttt"
        assert start == 0
        assert end == 5

    def test_no_match_empty_text(self) -> None:
        trigger, start, end = find_trigger("", ["ttt"])
        assert trigger is None

    def test_no_match_empty_triggers(self) -> None:
        trigger, start, end = find_trigger("ttt", [])
        assert trigger is None

    def test_match_after_punctuation(self) -> None:
        trigger, start, end = find_trigger("(ttt)", ["ttt"])
        assert trigger == "ttt"
        assert start == 1
        assert end == 4

    def test_no_match_inside_word(self) -> None:
        trigger, start, end = find_trigger("battt", ["ttt"])
        assert trigger is None


class TestSnippetEngine:
    def test_load_snippets(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "helowrite"
        config_dir.mkdir()
        snippets_file = config_dir / "snippets.conf"
        snippets_file.write_text("ttt=hello\nsig=regards\n")

        engine = SnippetEngine(config_dir=config_dir)
        assert engine.get_snippets() == {"ttt": "hello", "sig": "regards"}

    def test_load_snippets_ignores_comments(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "helowrite"
        config_dir.mkdir()
        snippets_file = config_dir / "snippets.conf"
        snippets_file.write_text("# comment\nttt=hello\n# another\n")

        engine = SnippetEngine(config_dir=config_dir)
        assert engine.get_snippets() == {"ttt": "hello"}

    def test_save_and_reload(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "helowrite"
        config_dir.mkdir()
        engine = SnippetEngine(config_dir=config_dir)
        engine.set_snippets({"ttt": "**%CURRENTTIME**", "sig": "Best regards"})

        engine.save_snippets()
        reloaded = SnippetEngine(config_dir=config_dir)
        assert reloaded.get_snippets() == {"ttt": "**%CURRENTTIME**", "sig": "Best regards"}

    def test_add_snippet(self) -> None:
        engine = SnippetEngine()
        assert engine.add_snippet("ttt", "**hello**") is True
        assert engine.get_snippets() == {"ttt": "**hello**"}

    def test_add_snippet_invalid_trigger_rejects(self) -> None:
        engine = SnippetEngine()
        assert engine.add_snippet("", "hello") is False
        assert engine.add_snippet("a=b", "hello") is False
        assert engine.add_snippet("a\nb", "hello") is False

    def test_remove_snippet(self) -> None:
        engine = SnippetEngine()
        engine.set_snippets({"ttt": "hello"})
        assert engine.remove_snippet("ttt") is True
        assert "ttt" not in engine.get_snippets()

    def test_remove_snippet_missing(self) -> None:
        engine = SnippetEngine()
        assert engine.remove_snippet("ttt") is False

    def test_try_expand_no_match(self) -> None:
        engine = SnippetEngine()
        engine.set_snippets({"ttt": "**hello**"})
        expanded, replacement, start, end = engine.try_expand("xyz")
        assert expanded is False
        assert replacement is None

    def test_try_expand_match(self) -> None:
        engine = SnippetEngine()
        engine.set_snippets({"ttt": "**hello**"})
        expanded, replacement, start, end = engine.try_expand("hello ttt")
        assert expanded is True
        assert replacement == "**hello**"
        assert start == 6
        assert end == 9

    def test_try_expand_expands_placeholders(self) -> None:
        engine = SnippetEngine()
        engine.set_snippets({"ttt": "**%CURRENTTIME**"})
        expanded, replacement, start, end = engine.try_expand("ttt")
        import re

        assert expanded is True
        assert re.match(r"^\*\*\d{2}:\d{2}\*\*$", replacement)
