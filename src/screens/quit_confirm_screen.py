"""Screen to confirm quitting with unsaved changes."""

from typing import Any, cast

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Static,
)


class QuitConfirmScreen(ModalScreen):
    """Screen to confirm quitting with unsaved changes - TUI native design."""

    DEFAULT_CSS = """
    QuitConfirmScreen {
        align: center middle;
    }

    #quit-container {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $warning;
        padding: 1 2;
    }

    #quit-header {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #quit-message {
        text-align: center;
        margin-bottom: 1;
    }

    #quit-options {
        text-align: center;
        color: $primary;
        margin-bottom: 1;
    }

    #quit-footer {
        text-align: center;
        color: $text-muted;
        text-style: dim;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="quit-container"):
            yield Static(" Unsaved Changes ", id="quit-header")
            yield Static(
                "You have unsaved changes. What would you like to do?",
                id="quit-message",
            )
            yield Static(
                "S: Save & Quit | Q: Discard & Quit | Esc: Cancel", id="quit-footer"
            )

    def on_key(self, event) -> None:
        """Handle key presses."""
        app = cast(Any, self.app)
        if event.key == "escape" or event.key == "c":
            self.app.pop_screen()
        elif event.key == "s":
            app.action_save()
            app.exit()
        elif event.key == "q":
            app.exit()
        elif event.key == "q":
            app.exit()
