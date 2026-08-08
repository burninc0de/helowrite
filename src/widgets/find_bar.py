"""Top search bar for in-buffer find navigation."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Input, Static


class FindInput(Input):
    """An Input that passes Ctrl+F through to the app find action."""

    def action_delete_right_word(self) -> None:
        app = self.screen.app
        if hasattr(app, "action_find"):
            app.action_find()


class FindBar(Horizontal):
    """Top search bar for in-buffer find navigation."""

    DEFAULT_CSS = """
    FindBar {
        height: 1;
        padding: 0 1;
        background: $primary-darken-2;
        color: $text;
        display: none;
    }

    FindBar.visible {
        display: block;
    }

    #find-text {
        width: auto;
        color: $text;
    }

    #find-input {
        width: 0;
        min-width: 0;
        height: 1;
        border: none;
        background: transparent;
        color: transparent;
        padding: 0;
    }

    #find-meta {
        width: auto;
        padding-left: 1;
        color: $text-muted;
    }

    #find-arrows {
        width: auto;
        padding-left: 1;
        color: $primary;
        text-style: bold;
    }

    #find-spacer {
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Find:", id="find-text")
        yield FindInput(placeholder="Type to search...", id="find-input")
        yield Static("0 matches", id="find-meta")
        yield Static("", id="find-spacer")
        yield Static("ESC ↑ ↓", id="find-arrows")

    def set_query(self, query: str) -> None:
        """Render the query visibly in the top bar."""
        label = self.query_one("#find-text", Static)
        if query:
            label.update(f'Find: "{query}"')
        else:
            label.update("Find:")

    def set_match_count(self, count: int, current_index: int = -1) -> None:
        """Update the match counter in the find bar."""
        meta = self.query_one("#find-meta", Static)
        if count <= 0:
            meta.update("0 matches")
            return
        if 0 <= current_index < count:
            meta.update(f"{current_index + 1}/{count}")
            return
        meta.update(f"{count} matches")
