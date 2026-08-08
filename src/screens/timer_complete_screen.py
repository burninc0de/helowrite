"""Screen shown when the timer completes."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Static,
)


class TimerCompleteScreen(ModalScreen):
    """Screen shown when the timer completes."""

    DEFAULT_CSS = """
    TimerCompleteScreen {
        align: center middle;
    }

    #complete-container {
        width: 50;
        height: auto;
        background: transparent;
        border: thick $primary;
        padding: 2 3;
    }

    #complete-header {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #complete-message {
        text-align: center;
        margin-bottom: 1;
    }

    #complete-footer {
        text-align: center;
        color: $text-muted;
        text-style: dim;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="complete-container"):
            yield Static(" Time's Up! ", id="complete-header")
            yield Static("Great work! Take a break.", id="complete-message")
            yield Static("Press any key or Escape to close", id="complete-footer")

    def on_key(self, event):
        """Handle key presses to close."""
        if event.key == "escape":
            self.app.pop_screen()
        else:
            self.app.pop_screen()
