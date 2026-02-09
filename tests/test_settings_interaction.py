"""Integration tests for user settings interaction."""

from __future__ import annotations

from pathlib import Path

import pytest
from textual.widgets import Checkbox, Input

from app import HeloWrite
from src.config import Config


from src.screens import SettingsScreen


@pytest.mark.asyncio
async def test_settings_change_editor_width(temp_config_dir: Path):
    """Test changing editor width via Settings screen."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        # Open Settings
        await pilot.press("f3")
        await pilot.pause()  # Wait for screen to mount
        
        # Verify Settings Screen is active
        assert isinstance(app.screen, SettingsScreen)
        
        # Change width value directly (simulating user input)
        width_input = app.screen.query_one("#width-input", Input)
        width_input.value = "55"
        
        # Save
        await pilot.press("enter")
        await pilot.pause() # Wait for save and pop_screen
        
        # Verify app state updated
        assert app.editor_width == 55
        
        # Verify visual style updated
        editor = app.query_one("#editor")
        assert editor.styles.width.value == 55.0
        
        # Verify config persisted
        config = Config(config_dir=temp_config_dir)
        assert config.get_editor_width() == 55


@pytest.mark.asyncio
async def test_settings_toggle_scrollbar(temp_config_dir: Path):
    """Test toggling scrollbar via Settings screen."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        # Default is off (0) based on config.py? 
        # let's check config default in src/config.py: get_scrollbar_enabled default "0"
        assert not app.scrollbar_enabled
        
        # Open Settings
        await pilot.press("f3")
        await pilot.pause()
        
        # Toggle scrollbar checkbox
        checkbox = app.screen.query_one("#show-scrollbar-checkbox", Checkbox)
        checkbox.value = True
        
        # Save
        await pilot.press("enter")
        await pilot.pause()
        
        # Verify app state
        assert app.scrollbar_enabled
        
        # Verify config persisted
        config = Config(config_dir=temp_config_dir)
        assert config.get_scrollbar_enabled()


@pytest.mark.asyncio
async def test_distraction_free_toggle(temp_config_dir: Path):
    """Test toggling distraction free mode via shortcut (F11)."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        assert not app.distraction_free
        
        # Toggle On
        await pilot.press("f11")
        assert app.distraction_free
        assert app.query_one("#editor").has_class("distraction-free")
        
        # Toggle Off
        await pilot.press("f11")
        assert not app.distraction_free
        assert not app.query_one("#editor").has_class("distraction-free")


@pytest.mark.asyncio
async def test_settings_validation_keeps_screen_open(temp_config_dir: Path):
    """Test that invalid input prevents closing settings."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        await pilot.press("f3")
        await pilot.pause()
        
        # Enter invalid width
        width_input = app.screen.query_one("#width-input", Input)
        width_input.value = "999" # Limit is 90
        
        # Try to save
        await pilot.press("enter")
        await pilot.pause()
        
        # Should still be in settings (SettingsScreen widgets still exist)
        assert isinstance(app.screen, SettingsScreen)
        assert app.screen.query_one("#width-input", Input)
        
        # App state should NOT have changed
        assert app.editor_width != 999
