"""Screen showing about information with ASCII art."""

import pyfiglet
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Static,
)


class AboutScreen(ModalScreen):
    """Screen showing about information with ASCII art."""

    DEFAULT_CSS = """
    AboutScreen {
        align: center middle;
        scrollbar-size: 1 1;
        scrollbar-color: $surface-lighten-2;
        scrollbar-color-hover: $surface-lighten-1;
        scrollbar-background: $surface;
    }

    #about-container {
        width: 80;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2 3;
    }

    #about-content {
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        ascii_art = pyfiglet.figlet_format("HeloWrite", font="slant")

        # Create a color palette display using actual theme colors
        colors = [
            ("[bold $primary]██[/bold $primary]", "Primary"),
            ("[bold $primary-darken-1]██[/bold $primary-darken-1]", "Primary Dark"),
            ("[bold $primary-lighten-1]██[/bold $primary-lighten-1]", "Primary Light"),
            ("[$surface-darken-1]██[/$surface-darken-1]", "Surface Dark"),
            ("[$text]██[/$text]", "Text"),
            ("[$text-muted]██[/$text-muted]", "Text Muted"),
            ("[$success]██[/$success]", "Success"),
        ]
        color_display = "   ".join(color for color, _ in colors)

        about_text = f"""{ascii_art}
A distraction-free writing environment for the terminal.
Designed for focused composition with minimal UI and keyboard-driven workflow.

• Persistent themes and customizable editor settings
• Distraction-free mode for immersive writing
• Git integration and auto-save
• Keyboard shortcuts for everything

{color_display}

HeloWrite - Write without distraction.

Version: 0.8.81

Press Escape to close"""
        with Vertical(id="about-container"):
            yield Static(about_text, id="about-content")

    def on_key(self, event):
        """Handle key presses to close on Escape."""
        if event.key == "escape":
            self.app.pop_screen()
