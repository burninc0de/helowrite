"""Integration tests for the main application."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import HeloWrite


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
            "cursor": (editor.cursor_location[0], max(editor.cursor_location[1] - 1, 0)),
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
