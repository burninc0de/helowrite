"""Modal screen for entering Pomodoro timer duration."""

from typing import Any, cast

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Input,
    Static,
)

from pomodoro import parse_pomodoro_minutes


class PomodoroTimerScreen(ModalScreen):
    """Modal for entering Pomodoro timer duration."""

    DEFAULT_CSS = """
    PomodoroTimerScreen {
        align: center middle;
    }

    #timer-container {
        width: 50;
        height: auto;
        background: transparent;
        border: thick $primary;
        padding: 1 2;
    }

    #timer-header {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #time-input {
        margin-bottom: 1;
    }

    #timer-footer {
        text-align: center;
        color: $text-muted;
        text-style: dim;
        margin-top: 1;
    }

    #timer-hint {
        text-align: center;
        color: $primary;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        from textual.widgets import Input

        with Vertical(id="timer-container"):
            yield Static(" Pomodoro Timer ", id="timer-header")
            yield Input(placeholder="Enter minutes (e.g., 25)", id="time-input")
            yield Static("Enter: start | Esc: cancel", id="timer-footer")
            yield Static("Enter time in minutes", id="timer-hint")

    def on_mount(self):
        """Focus the input field on mount."""
        self.query_one("#time-input", Input).focus()

    def on_key(self, event):
        """Handle key presses."""
        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "enter":
            self.start_timer()

    def start_timer(self):
        """Parse input and start the timer."""
        app = cast(Any, self.app)
        input_widget = self.query_one("#time-input", Input)
        minutes, error = parse_pomodoro_minutes(input_widget.value)
        if error or minutes is None:
            app.show_message(error or "Please enter a valid number (e.g., 25)")
            return

        self.app.pop_screen()
        app.start_timer(minutes)

    def run_timer(self, minutes: int):
        """Deprecated - timer now runs via app."""
        pass
