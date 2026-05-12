"""Integration tests for the main application."""

from __future__ import annotations

from pathlib import Path

import pytest
from textual.widgets import Input

from app import HeloWrite
from config import Config
from screens import WelcomeScreen
from widgets import FindBar


@pytest.mark.asyncio
async def test_app_startup_and_quit(temp_config_dir: Path):
    """Test that the app starts and can be quit."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        # Check initial state
        assert app.file_path is None

        # Quit
        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_welcome_screen_is_disabled_in_tests(temp_config_dir: Path):
    """Ensure the welcome screen is disabled for headless pytest runs."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        assert not any(isinstance(screen, WelcomeScreen) for screen in app.screen_stack)
        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_ctrl_f_opens_find_bar_and_focuses_input(temp_config_dir: Path):
    """Ctrl+F should open the top find bar and focus the search input."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+f")
        await pilot.pause()

        find_bar = app.query_one("#find-bar", FindBar)
        find_input = app.query_one("#find-input", Input)
        assert find_bar.has_class("visible")
        assert app.screen.focused == find_input

        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_find_bar_navigation_and_enter_close(temp_config_dir: Path):
    """Typing should highlight matches; arrows navigate and Enter closes."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor")
        editor.load_text("alpha beta alpha")
        await pilot.pause()

        app.action_find()
        await pilot.pause()

        find_input = app.query_one("#find-input", Input)
        find_input.value = "alpha"
        app.apply_find_query("alpha")
        await pilot.pause()

        assert len(app.find_matches) == 2
        assert app.find_active_match_index == 0
        assert any(
            span[2] in {"search_result", "search_result_current"}
            for spans in editor._highlights.values()
            for span in spans
        )

        await pilot.press("down")
        await pilot.pause()
        assert app.find_active_match_index == 1

        await pilot.press("enter")
        await pilot.pause()

        find_bar = app.query_one("#find-bar", FindBar)
        assert not find_bar.has_class("visible")
        assert app.find_query == ""
        assert app.find_matches == []

        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_find_bar_shows_query_text_and_arrows(temp_config_dir: Path):
    """Find bar should visibly render the current query and arrow controls."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+f")
        await pilot.pause()

        find_input = app.query_one("#find-input", Input)
        find_input.value = "vault"
        await pilot.pause()

        find_text = app.query_one("#find-text")
        find_arrows = app.query_one("#find-arrows")
        rendered_find_text = str(find_text.content)
        assert rendered_find_text.startswith("Find:")
        assert "vault" in rendered_find_text
        assert "↑" in str(find_arrows.content)
        assert "↓" in str(find_arrows.content)

        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_app_loads_file(tmp_path: Path, temp_config_dir: Path):
    """Test that the app loads a file correctly."""
    # Create a dummy file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")

    app = HeloWrite(str(test_file))
    async with app.run_test() as pilot:
        # Check if file was loaded
        assert app.file_path == test_file

        # Check editor content
        editor = app.query_one("#editor")
        assert editor.text == "Hello World"

        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_app_save_file(tmp_path: Path, temp_config_dir: Path):
    """Test saving a file."""
    test_file = tmp_path / "save_test.txt"
    test_file.write_text("Original")

    app = HeloWrite(str(test_file))
    async with app.run_test() as pilot:
        editor = app.query_one("#editor")

        # Modify text directly
        # Note: We need to ensure the app knows it's dirty.
        # Setting text directly on TextArea might not trigger 'changed' message in a way
        # that updates is_dirty immediately depending on how it's wired,
        # but HeloWrite.on_text_area_changed listens for it.
        # Let's simulate typing or just set text and wait for event processing.

        editor.load_text("Modified")
        # Force dirty state or wait for event?
        # Textual's run_test handles message pump.
        # However, load_text typically resets the "original text" logic in some editors,
        # but let's check HeloWrite.load_text usage.

        # In HeloWrite.__init__:
        # editor.load_text(content)
        # self._original_text = content

        # If I call load_text again, _original_text doesn't update automatically
        # unless I update it myself.
        # But wait, HeloWrite doesn't override load_text on the editor, it calls it on the widget.
        # And on_text_area_changed compares editor.text with self._original_text.

        # So:
        # 1. App starts, loads "Original". _original_text="Original".
        # 2. We call editor.load_text("Modified").
        # 3. on_text_area_changed fires. editor.text ("Modified") != _original_text ("Original").
        # 4. is_dirty becomes True.

        await pilot.pause()
        assert app.is_dirty

        # Save
        await pilot.press("ctrl+s")

        # Wait a bit for async save
        await pilot.pause()

        # Check if dirty flag cleared
        assert not app.is_dirty

        # Verify file on disk
        assert test_file.read_text() == "Modified"

        # Clean exit
        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_typewriter_scroll_visible_is_idempotent(temp_config_dir: Path):
    """Ensure repeated visibility updates do not retrigger typewriter centering."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor")
        app.typewriter_mode = True

        await pilot.pause()

        view_height = editor.scrollable_content_region.height
        editor._last_typewriter_center_state = {
            "cursor": editor.cursor_location,
            "scroll_y": float(editor.scroll_y),
            "target": float(editor.scroll_y),
            "max_scroll_y": float(editor.max_scroll_y),
            "view_height": int(view_height),
        }
        editor._typewriter_recently_preserved = False

        initial_scroll = float(editor.scroll_y)

        editor.scroll_cursor_visible()
        assert not editor._typewriter_center_scheduled
        assert not editor.has_class("typewriter-hidden")
        assert float(editor.scroll_y) == initial_scroll

        await pilot.pause()

        editor.scroll_cursor_visible()
        assert not editor._typewriter_center_scheduled
        assert float(editor.scroll_y) == initial_scroll

        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_typewriter_same_line_typing_no_hide_when_scroll_unchanged(
    temp_config_dir: Path,
):
    """Ensure cursor-column movement doesn't hide cursor when center target is unchanged."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor")
        app.typewriter_mode = True

        await pilot.pause()

        initial_scroll = float(editor.scroll_y)
        view_height = editor.scrollable_content_region.height

        editor._last_typewriter_center_state = {
            "cursor": (
                editor.cursor_location[0],
                max(editor.cursor_location[1] - 1, 0),
            ),
            "scroll_y": initial_scroll,
            "target": initial_scroll,
            "max_scroll_y": float(editor.max_scroll_y),
            "view_height": int(view_height),
        }

        original_get_target = editor._get_typewriter_target_scroll_y
        editor._get_typewriter_target_scroll_y = lambda: initial_scroll
        try:
            editor.scroll_cursor_visible()
        finally:
            editor._get_typewriter_target_scroll_y = original_get_target

        assert not editor._typewriter_center_scheduled
        assert not editor.has_class("typewriter-hidden")
        assert float(editor.scroll_y) == initial_scroll

        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_typewriter_skips_invalid_preserved_scroll_on_transient_geometry(
    temp_config_dir: Path,
):
    """Do not restore preserved scroll when current max_scroll_y is temporarily smaller."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor")
        app.typewriter_mode = True

        await pilot.pause()

        initial_scroll = float(editor.scroll_y)
        view_height = editor.scrollable_content_region.height
        editor._last_typewriter_center_state = {
            "cursor": editor.cursor_location,
            "scroll_y": float(editor.max_scroll_y) + 1.0,
            "target": float(editor.max_scroll_y) + 1.0,
            "max_scroll_y": float(editor.max_scroll_y) + 1.0,
            "view_height": int(view_height),
        }

        editor.scroll_cursor_visible()

        assert float(editor.scroll_y) == initial_scroll
        assert not editor._typewriter_center_scheduled
        assert not editor.has_class("typewriter-hidden")

        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_typewriter_enter_advances_single_line(temp_config_dir: Path):
    """Enter should advance one line, not two, in typewriter mode."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor")
        app.typewriter_mode = True
        app.space_between_paragraphs = False

        await pilot.pause()

        start_row, _ = editor.cursor_location
        await pilot.press("enter")
        await pilot.pause()
        end_row, _ = editor.cursor_location

        assert end_row == start_row + 1

        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_typewriter_enter_advances_double_line_with_paragraph_spacing(
    temp_config_dir: Path,
):
    """Enter should advance two lines when paragraph spacing mode is enabled."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor")
        app.typewriter_mode = True
        app.space_between_paragraphs = True

        await pilot.pause()

        start_row, _ = editor.cursor_location
        await pilot.press("enter")
        await pilot.pause()
        end_row, _ = editor.cursor_location

        assert end_row == start_row + 2

        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_system_theme_auto_selected_on_first_launch(
    temp_config_dir: Path, monkeypatch
):
    system_theme = {
        "name": "system",
        "display_name": "System",
        "primary": "#5ea1ff",
        "background": "#101010",
        "surface": "#101010",
        "foreground": "#f0f0f0",
        "dark": True,
    }
    monkeypatch.setattr("app.create_system_theme", lambda: system_theme)
    monkeypatch.setattr("app.get_system_theme_last_modified", lambda: 123.0)
    monkeypatch.setattr("app.is_system_theme_available", lambda: True)

    app = HeloWrite()
    async with app.run_test() as pilot:
        assert app.theme == "system"
        assert Config(config_dir=temp_config_dir).get_theme() == "system"
        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_system_theme_does_not_override_saved_user_choice(
    temp_config_dir: Path, monkeypatch
):
    Config(config_dir=temp_config_dir).set_theme("kanso-pearl")
    system_theme = {
        "name": "system",
        "display_name": "System",
        "primary": "#5ea1ff",
        "background": "#101010",
        "surface": "#101010",
        "foreground": "#f0f0f0",
        "dark": True,
    }
    monkeypatch.setattr("app.create_system_theme", lambda: system_theme)
    monkeypatch.setattr("app.get_system_theme_last_modified", lambda: 123.0)
    monkeypatch.setattr("app.is_system_theme_available", lambda: True)

    app = HeloWrite()
    async with app.run_test() as pilot:
        assert app.theme == "kanso-pearl"
        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_system_theme_falls_back_when_source_disappears(
    temp_config_dir: Path, monkeypatch
):
    Config(config_dir=temp_config_dir).set_theme("system")
    state = {"available": True}
    system_theme = {
        "name": "system",
        "display_name": "System",
        "primary": "#5ea1ff",
        "background": "#101010",
        "surface": "#101010",
        "foreground": "#f0f0f0",
        "dark": True,
    }

    monkeypatch.setattr("app.create_system_theme", lambda: system_theme)
    monkeypatch.setattr("app.get_system_theme_last_modified", lambda: 123.0)
    monkeypatch.setattr("app.is_system_theme_available", lambda: state["available"])

    app = HeloWrite()
    async with app.run_test() as pilot:
        assert app.theme == "system"
        state["available"] = False
        app._check_system_theme_update()
        assert app.theme == "helowrite-dark"
        assert Config(config_dir=temp_config_dir).get_theme() == "helowrite-dark"
        assert app._system_watcher_active is False
        await pilot.press("ctrl+q")


@pytest.mark.asyncio
async def test_system_theme_update_reapplies_dynamic_highlight_styles(
    temp_config_dir: Path, monkeypatch
):
    Config(config_dir=temp_config_dir).set_theme("system")
    state = {
        "available": True,
        "mtime": 100.0,
        "primary": "#5ea1ff",
    }

    def make_theme() -> dict:
        return {
            "name": "system",
            "display_name": "System",
            "primary": state["primary"],
            "background": "#101010",
            "surface": "#101010",
            "foreground": "#f0f0f0",
            "dark": True,
        }

    monkeypatch.setattr("app.create_system_theme", make_theme)
    monkeypatch.setattr("app.get_system_theme_last_modified", lambda: state["mtime"])
    monkeypatch.setattr("app.is_system_theme_available", lambda: state["available"])

    app = HeloWrite()
    async with app.run_test() as pilot:
        assert app.theme == "system"

        calls = {"count": 0}
        original_apply_cursor_color = app.apply_cursor_color

        def track_apply_cursor_color() -> None:
            calls["count"] += 1
            original_apply_cursor_color()

        app.apply_cursor_color = track_apply_cursor_color

        state["primary"] = "#ff8a00"
        state["mtime"] = 101.0
        app._check_system_theme_update()

        assert calls["count"] == 1
        assert app._system_theme is not None
        assert app._system_theme["primary"] == "#ff8a00"
        await pilot.press("ctrl+q")


def test_read_text_file_supports_legacy_cp1252(tmp_path: Path, temp_config_dir: Path):
    """Legacy cp1252 files should still load correctly."""
    path = tmp_path / "legacy.md"
    path.write_bytes(b"\x93hello\x94")

    app = HeloWrite()
    assert app.read_text_file(path) == "\u201chello\u201d"


def test_write_text_file_always_uses_utf8(tmp_path: Path, temp_config_dir: Path):
    """Editor writes should always use UTF-8 for portability."""
    path = tmp_path / "utf8.md"

    HeloWrite.write_text_file(path, "\u201chello\u201d")

    assert path.read_bytes() == b"\xe2\x80\x9chello\xe2\x80\x9d"
