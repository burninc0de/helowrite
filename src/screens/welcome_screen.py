"""Welcome screen shown on first launch."""

from typing import TYPE_CHECKING, cast

import pyfiglet
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Static,
)

if TYPE_CHECKING:
    from app import HeloWrite


class WelcomeScreen(ModalScreen):
    """Welcome screen shown on first launch."""

    DEFAULT_CSS = """
WelcomeScreen {
        align: center middle;
        background: $surface;
        scrollbar-size: 1 1;
        scrollbar-color: $surface-lighten-2;
        scrollbar-color-hover: $surface-lighten-1;
        scrollbar-background: $surface;
    }

    #welcome-container {
        width: 90;
        height: auto;
        padding: 2 4;
    }

    #welcome-title {
        text-align: center;
        color: $primary;
        text-style: bold;
    }

    #welcome-subtitle {
        text-align: center;
        color: $text;
        text-style: italic;
    }

    #welcome-section {
        width: 100%;
        text-align: center;
    }

    #welcome-hint {
        color: $text-muted;
        text-align: center;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        ascii_art = pyfiglet.figlet_format("HeloWrite", font="slant")

        with Vertical(id="welcome-container"):
            yield Static(ascii_art, id="welcome-title")
            yield Static("The Tactical Blade for Prose", id="welcome-subtitle")
            yield Static(
                """
Press [bold $primary]Ctrl+P[/] to open the [bold $primary]Command Palette[/] — choose a theme and customize settings.

Customize your keybindings in: [bold $primary]~/.config/helowrite/keybindings.conf[/]
""",
                id="welcome-section",
            )
            yield Static(
                "Press any key to begin, or (x) to disable this message...",
                id="welcome-hint",
            )

    def on_key(self, event) -> None:
        app = cast("HeloWrite", self.app)
        if event.key.lower() == "x":
            app.config.set_show_welcome(False)
        app.editor_width = app.config.get_editor_width()
        app.apply_editor_settings()
        self.app.pop_screen()
