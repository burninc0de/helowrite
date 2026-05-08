"""Unit tests for widget-level behavior."""

from __future__ import annotations

import textual.message_pump as mp
from textual.app import App

from widgets import HeloWriteTextArea, StatusBar


class _StubApp:
    def __init__(self):
        self.updated = False

    def update_status(self):  # pragma: no cover - trivial
        self.updated = True


class _SnippetApp(App):
    def __init__(self):
        super().__init__()
        self._snippets = {"eee": "Société Anonyme Belge pour le Commerce du Haut-Congo"}
        self.snippet_highlighting_enabled = True
        self.markdown_highlighting_enabled = True
        self.language = "text"

    def compose(self):
        return


def test_status_bar_updates_display_text():
    bar = StatusBar()
    bar.update_status(None, False, 50, "markdown")

    assert "untitled" in bar._last_rendered_text
    assert "Words: 50" in bar._last_rendered_text


def test_status_bar_find_mode_prompt():
    bar = StatusBar()
    bar.enable_find_mode()
    bar.find_text = "elo"
    bar.update_status(None, False, 0, "text")

    assert "Find: elo" in bar._last_rendered_text
    assert bar.has_class("find-mode")


def test_status_bar_disable_find_mode_restores_state():
    bar = StatusBar()
    bar._app = _StubApp()  # type: ignore[attr-defined]
    bar.enable_find_mode()
    bar.disable_find_mode()

    assert not bar.find_mode
    assert not bar.has_class("find-mode")
    assert bar._app.updated  # type: ignore[attr-defined]


def test_snippet_highlight_uses_utf8_byte_offsets_for_unicode() -> None:
    app = _SnippetApp()
    token = mp.active_app.set(app)
    try:
        widget = HeloWriteTextArea()
        widget.text = app._snippets["eee"]
        widget._highlights.clear()
        widget._build_snippet_highlights()

        expected_end = len(widget.text.encode("utf-8"))
        assert widget._highlights[0] == [(0, expected_end, "snippet")]
    finally:
        mp.active_app.reset(token)


def test_markdown_highlights_headings_links_images_and_blockquotes() -> None:
    app = _SnippetApp()
    app.language = "markdown"
    token = mp.active_app.set(app)
    try:
        widget = HeloWriteTextArea()
        widget.text = "# Heading\n> Quote\n[site](https://example.com) ![img](a.png)"
        widget._highlights.clear()
        widget._build_markdown_highlights()

        assert any(span[2] == "markdown_heading" for span in widget._highlights[0])
        assert any(span[2] == "markdown_blockquote" for span in widget._highlights[1])
        assert any(span[2] == "markdown_link" for span in widget._highlights[2])
        assert any(span[2] == "markdown_image" for span in widget._highlights[2])
    finally:
        mp.active_app.reset(token)
