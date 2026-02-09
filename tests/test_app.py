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
