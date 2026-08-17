"""Modal screen for saving a new file with a filename."""

from pathlib import Path
from typing import Any, cast

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Input,
    Static,
)

from utils import detect_language
from widgets import HeloWriteTextArea


class SaveAsScreen(ModalScreen):
    """Modal screen for saving a new file with a filename."""

    DEFAULT_CSS = """
    SaveAsScreen {
        align: center middle;
    }

    #save-container {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #save-header {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #filename-input {
        margin-bottom: 1;
    }

    #save-footer {
        text-align: center;
        color: $text-muted;
        text-style: dim;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="save-container"):
            yield Static(" Save As ", id="save-header")
            yield Input(placeholder="Enter filename...", id="filename-input")
            yield Static("Enter: save | Esc: cancel", id="save-footer")

    def on_mount(self):
        """Focus the input field on mount."""
        self.query_one("#filename-input", Input).focus()

    def on_key(self, event):
        """Handle key presses to save on Enter or close on Escape."""
        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "enter":
            self.save_file()

    def save_file(self):
        """Save the file with the entered filename."""
        app = cast(Any, self.app)
        filename = self.query_one("#filename-input", Input).value.strip()

        if not filename:
            app.show_message("Please enter a filename")
            return

        # Ensure the filename has an extension
        if not Path(filename).suffix:
            filename += ".txt"

        # Create the full path in the current directory
        file_path = Path(filename)

        try:
            editor = app.query_one("#editor", HeloWriteTextArea)
            text = editor.text

            app.write_text_file(file_path, text)
            app.file_path = file_path
            app.language = detect_language(file_path)
            editor.language = app.language
            app.is_dirty = False
            app.update_status()
            app.show_message(f"Saved: {file_path}")
            app._update_file_watcher()
            self.app.pop_screen()
        except Exception as e:
            app.show_message(f"Error saving file: {e}")
