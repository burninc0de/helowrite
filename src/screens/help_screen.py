"""Screen showing keyboard shortcuts and help information."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Static,
)


class HelpScreen(ModalScreen):
    """Screen showing keyboard shortcuts and help information."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-container {
        width: 70;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2 3;
    }

    #help-content {
        text-align: left;
    }
    """

    def compose(self) -> ComposeResult:
        from constants import HELP_TEXT

        help_content = HELP_TEXT.replace(
            "Press F1 again to return to editing...", "Press Escape to close"
        )

        with Vertical(id="help-container"):
            yield Static(help_content, id="help-content")

    def on_key(self, event):
        """Handle key presses to close on Escape."""
        if event.key == "escape":
            self.app.pop_screen()
