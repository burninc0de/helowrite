"""Custom widgets for HeloWrite."""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DirectoryTree, Static, TextArea

from src.utils import detect_language, has_nerd_fonts


class StatusBar(Static):
    """Status bar widget showing file and cursor information."""

    can_focus = True

    DEFAULT_CSS = """
    StatusBar {
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
        height: 1;
        margin: 0;
    }

    StatusBar.find-mode {
        background: $primary;
    }

    StatusBar:focus {
        background: $primary;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.find_mode = False
        self.find_text = ""
        self._last_rendered_text = ""

    def update_status(
        self,
        file_path: Optional[Path],
        is_dirty: bool,
        word_count: int,
        language: str = "text",
    ):
        """Update the status bar with current information."""
        if self.find_mode:
            # Show find prompt
            prompt = f" Find: {self.find_text}_  (Enter=next, Esc=close)"
            self._last_rendered_text = prompt
            self.update(prompt)
        else:
            filename = f"{file_path.name if file_path else 'untitled'}{' *' if is_dirty else ''}"
            status = f" {filename} | {language.capitalize()} | Words: {word_count} "
            self._last_rendered_text = status
            self.update(status)

    def enable_find_mode(self):
        """Enable find mode in status bar."""
        self.find_mode = True
        self.find_text = ""
        self.add_class("find-mode")
        self.update_status(None, False, 0, "text")

    def disable_find_mode(self):
        """Disable find mode and restore normal status."""
        self.find_mode = False
        self.find_text = ""
        self.remove_class("find-mode")
        # Trigger status update from app
        app = getattr(self, "_app", None) or getattr(self, "app", None)
        if app and hasattr(app, "update_status"):
            app.update_status()

    def on_key(self, event) -> None:
        """Handle key presses when in find mode."""
        if not self.find_mode:
            return

        if event.key == "escape":
            self.disable_find_mode()
            # Return focus to editor
            try:
                editor = self.app.query_one("#editor")
                editor.focus()
            except Exception:
                pass
        elif event.key in ("enter", "return"):
            # Trigger find next
            app = getattr(self, "app", None)
            action_find_next = getattr(app, "action_find_next", None) if app else None
            if callable(action_find_next):
                action_find_next()
            # Exit find mode and return focus to editor
            self.disable_find_mode()
            try:
                editor = self.app.query_one("#editor")
                editor.focus()
            except Exception:
                pass
        elif event.key == "backspace":
            self.find_text = self.find_text[:-1]
            self.update_status(None, False, 0, "text")
        elif len(event.key) == 1 and event.key.isprintable():
            self.find_text += event.key
            self.update_status(None, False, 0, "text")


class CenteredEditor(Horizontal):
    """A horizontal container that centers its content."""

    DEFAULT_CSS = """
    CenteredEditor {
        align: center middle;
        height: 1fr;
        width: 100%;
        padding-bottom: 0;
    }

    CenteredEditor.distraction-free {
        padding-top: 2;
    }
    """
    pass


class HeloWriteTextArea(TextArea):
    """Custom TextArea with additional commands and paragraph spacing."""

    DEFAULT_CSS = """
    TextArea {
        border: none;
        background: $surface;
        width: 70%;
        height: 100%;
        padding: 2 4;
        scrollbar-size: 1 1;
        scrollbar-color: $surface-lighten-2;
        scrollbar-color-hover: $surface-lighten-1;
        scrollbar-background: $surface;
    }

    TextArea.distraction-free {
        padding: 1 2;
    }

    /* Scrollbar styling for distraction-free (fullscreen) mode */
    TextArea.distraction-free {
        scrollbar-background: $surface;
        scrollbar-background-hover: $surface;
        scrollbar-background-active: $surface;
        scrollbar-color: #d0d0d0;
        scrollbar-color-hover: #cfcfcf;
        scrollbar-color-active: #bfbfbf;
        scrollbar-size: 1 1;
    }

    /* TextArea internal content background */
    TextArea > .text-area--content {
        background: $surface;
    }

    /* Cursor styling - uses theme color by default */
    .text-area--cursor {
        background: $primary;
        color: #ffffff;
        text-style: bold;
    }

    .text-area--cursor-line {
        background: $primary-lighten-1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.language = "text"

    def on_key(self, event):
        """Handle key presses, adding paragraph break on Enter."""
        if event.key == "enter":
            if self.app.space_between_paragraphs:
                # Insert one newline for paragraph break (spacing handled by CSS)
                self.insert("\n")
            # Ensure cursor remains visible after newline insertion
            self.app.call_later(self.scroll_cursor_visible)
            return True  # Prevent default handling
        # For other keys, let Textual handle them normally
        return False

    def action_home(self):
        """Override Ctrl+A to select all instead of going to start of line."""
        self.select_all()

    def select_all(self):
        """Select all text in the editor."""
        # Get the last cursor position (end of text)
        lines = self.text.split("\n")
        last_row = len(lines) - 1
        last_col = len(lines[-1]) if lines else 0
        # Move cursor to end while selecting everything from start
        self.move_cursor((0, 0))
        self.move_cursor((last_row, last_col), select=True)


class FileOpenPanel(Vertical):
    """A right-side panel that shows a directory tree for opening files.

    This is mounted into the existing UI so it doesn't block the whole screen.
    """

    DEFAULT_CSS = """
    FileOpenPanel {
        width: 30%;
        height: 100%;
        background: $surface;
        padding: 1 1;
    }

    #file-open-header-panel {
        padding-bottom: 1;
        color: $primary;
        text-style: bold;
    }

    #file-tree-panel {
        height: 1fr;
        overflow: auto;
                    scrollbar-size: 1 1;
        scrollbar-color: $surface-lighten-2;
        scrollbar-color-hover: $surface-lighten-1;
        scrollbar-background: $surface;
        overflow_x:hidden;
    }

    DirectoryTree > .directory-tree--folder {
        color: $primary;
    }

    DirectoryTree > .directory-tree--file {
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        tree = DirectoryTree("./", id="file-tree-panel")

        # Use Nerd Font icons if available, otherwise fall back to emojis
        if has_nerd_fonts():
            tree.ICON_NODE = "\uf07b "  # Folder closed
            tree.ICON_NODE_EXPANDED = "\uf07c "  # Folder open
            tree.ICON_FILE = "\uf016 "  # File
        else:
            # Fallback to emoji icons
            tree.ICON_NODE = "📁 "
            tree.ICON_NODE_EXPANDED = "📂 "
            tree.ICON_FILE = "📄 "

        yield tree

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        file_path = Path(event.path)
        if file_path.is_file():
            app = self.app
            app.file_path = file_path
            app.language = detect_language(file_path)
            try:
                content = file_path.read_text()
                editor = app.query_one("#editor", HeloWriteTextArea)
                editor.language = app.language
                editor.load_text(content)
                app._original_text = content
                app.show_message(f"Loaded: {file_path}")
                app.is_dirty = False
                app.update_status()
                # Save as last file if setting is enabled
                if app.config.get_open_last_file():
                    app.config.set_last_file_path(str(file_path))
                # Add to recent files
                app.config.add_recent_file(str(file_path))
            except Exception as e:
                app.show_message(f"Error loading file: {e}")
        # remove panel after selection
        try:
            self.remove()
        except Exception:
            pass

    def on_key(self, event) -> None:
        if getattr(event, "key", None) == "escape":
            try:
                self.remove()
            except Exception:
                pass
