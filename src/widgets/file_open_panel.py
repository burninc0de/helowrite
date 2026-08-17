"""Left-side panel showing a directory tree for opening files."""

from pathlib import Path
from typing import TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DirectoryTree

from utils import detect_language, has_nerd_fonts

if TYPE_CHECKING:
    from app import HeloWrite

from .editor import HeloWriteTextArea


class FileOpenPanel(Vertical):
    """A left-side panel that shows a directory tree for opening files.

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
        /* hide the horizontal scrollbar (0 = disabled) and keep a slim vertical one */
        scrollbar-size-horizontal: 0;
        scrollbar-size-vertical: 1;
        scrollbar-color: $surface-lighten-2;
        scrollbar-color-hover: $surface-lighten-1;
        scrollbar-background: $surface;

    }

    DirectoryTree > .directory-tree--folder {
        color: $primary;
    }

    DirectoryTree > .directory-tree--file {
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        from config import Config

        config = Config()
        default_dir = config.get_default_working_directory()
        tree_path = default_dir if default_dir else "./"

        tree = DirectoryTree(tree_path, id="file-tree-panel")

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
            app = cast("HeloWrite", self.app)
            app.file_path = file_path
            app.language = detect_language(file_path)
            try:
                content = app.read_text_file(file_path, show_encoding_notice=True)
                editor = app.query_one("#editor", HeloWriteTextArea)
                editor.language = None if app.language == "text" else app.language
                editor.load_text(content)
                app._original_text = content
                app.show_message(f"Loaded: {file_path}")
                app.is_dirty = False
                app.update_status()
                app._update_file_watcher()
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
