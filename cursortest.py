#!/usr/bin/env python3
"""
Minimal test file for experimenting with cursor/caret customization in Textual.
"""

from textual.app import App, ComposeResult
from textual.widgets import TextArea, Header, Footer, Static
from textual.containers import Container


class CursorTestApp(App):
    """Minimal app to test cursor color and style."""

    CSS = """
    Screen {
        background: #1e1e1e;
    }

    Container {
        align: center middle;
        height: 100%;
    }

    TextArea {
        width: 80%;
        height: 60%;
        border: round white;
    }

    /* WORKS! Styles the entire cursor line with subtle highlight */
    .text-area--cursor-line {
        background: #2a2a3a;
    }

    /* WORKS! Styles the actual cursor character */
    .text-area--cursor {
        background: #00ff00;
        color: #000000;
        text-style: bold;
    }

    /* WORKS! Styles the gutter (line numbers) area on cursor line */
    .text-area--cursor-gutter {
        background: #3a3a4a;
    }

    #info {
        dock: top;
        height: 4;
        text-align: center;
        padding: 1;
        background: #2e2e2e;
        color: white;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create the UI."""
        yield Static(
            "✓ SUCCESS! Cursor customization is working!\n" +
            "The cursor should be bright green with a purple line highlight.\n" +
            "Move the cursor around to see the effect.\n" +
            "Press Ctrl+Q to quit",
            id="info"
        )
        yield Header()
        with Container():
            yield TextArea(
                "Try moving the cursor around and typing!\n\n" +
                "Working CSS classes discovered:\n" +
                "✓ .text-area--cursor (green cursor cell)\n" +
                "✓ .text-area--cursor-line (purple line highlight)\n" +
                "✓ .text-area--cursor-gutter (gutter highlight, if line numbers shown)\n\n" +
                "You can customize:\n" +
                "- background: cursor/line background color\n" +
                "- color: cursor text color\n" +
                "- text-style: bold, italic, underline, etc.\n\n" +
                "These classes are the key to cursor customization in Textual!",
                id="editor"
            )
        yield Footer()

    def on_mount(self):
        """Focus the editor on startup."""
        editor = self.query_one("#editor", TextArea)
        editor.focus()


def main():
    app = CursorTestApp()
    app.run()


if __name__ == "__main__":
    main()
