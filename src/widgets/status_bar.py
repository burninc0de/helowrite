"""Status bar widget showing file and cursor information."""

from pathlib import Path
from typing import Optional

from textual.widgets import Static


class StatusBar(Static):
    """Status bar widget showing file and cursor information."""

    DEFAULT_CSS = """
    StatusBar {
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
        height: 1;
        margin: 0;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_rendered_text = ""

    def update_status(
        self,
        file_path: Optional[Path],
        is_dirty: bool,
        word_count: int,
        language: str = "text",
    ):
        """Update the status bar with current information."""
        filename = (
            f"{file_path.name if file_path else 'untitled'}{' *' if is_dirty else ''}"
        )
        status = f" {filename} | {language.capitalize()} | Words: {word_count} "
        self._last_rendered_text = status
        self.update(status)
