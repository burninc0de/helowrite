"""Unit tests for widget-level behavior."""

from __future__ import annotations

from widgets import StatusBar


class _StubApp:
    def __init__(self):
        self.updated = False

    def update_status(self):  # pragma: no cover - trivial
        self.updated = True


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
