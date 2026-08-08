"""Modal screen showing recent files for quick access."""

from pathlib import Path
from typing import Any, cast

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Static,
)

from utils import detect_language
from widgets import HeloWriteTextArea


class RecentFilesScreen(ModalScreen):
    """Modal screen showing recent files for quick access."""

    DEFAULT_CSS = """
    RecentFilesScreen {
        align: center middle;
    }

    #recent-container {
        width: 70;
        height: auto;
        max-height: 20;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #recent-header {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #recent-list {
        height: auto;
        max-height: 12;
        border: solid $primary;
    }

    #recent-empty {
        text-align: center;
        color: $text-muted;
        padding: 1;
    }

    #recent-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="recent-container"):
            yield Static("Recent Files", id="recent-header")
            app = cast(Any, self.app)
            recent_files = app.config.get_recent_files()
            if recent_files:
                from textual.widgets import OptionList

                options = [
                    f"{i + 1}. {Path(f).name}" for i, f in enumerate(recent_files)
                ]
                yield OptionList(*options, id="recent-list")
                yield Static(
                    "↑↓ to select, Enter to open, Esc to close", id="recent-hint"
                )
            else:
                yield Static("No recent files", id="recent-empty")
                yield Static("Press Escape to close", id="recent-hint")

    def on_key(self, event) -> None:
        """Handle key presses - Enter opens selected file, Esc closes."""
        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "enter":
            self.open_selected_file()

    def open_selected_file(self):
        """Open the currently selected file."""
        try:
            app = cast(Any, self.app)
            from textual.widgets import OptionList

            list_widget = self.query_one("#recent-list", OptionList)
            selected = list_widget.highlighted

            if selected is not None:
                recent_files = app.config.get_recent_files()
                if 0 <= selected < len(recent_files):
                    file_path = Path(recent_files[selected])
                    if file_path.exists():
                        app.file_path = file_path
                        app.language = detect_language(file_path)
                        try:
                            content = app.read_text_file(
                                file_path, show_encoding_notice=True
                            )
                            editor = app.query_one("#editor", HeloWriteTextArea)
                            editor.language = app.language
                            editor.load_text(content)
                            app._original_text = content
                            app.show_message(f"Loaded: {file_path}")
                            app.is_dirty = False
                            app.update_status()
                        except Exception as e:
                            app.show_message(f"Error loading file: {e}")
                    else:
                        app.show_message(f"File not found: {file_path}")
                        # Remove from recent files
                        app.config.add_recent_file(
                            str(file_path)
                        )  # This will remove it
            self.app.pop_screen()
        except Exception:
            pass
