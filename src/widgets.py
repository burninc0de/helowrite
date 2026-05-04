"""Custom widgets for HeloWrite."""

import datetime
import os
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.geometry import Size
from textual.widgets import DirectoryTree, Static, TextArea

from utils import detect_language, has_nerd_fonts


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

    .typewriter-hidden .text-area--cursor,
    .typewriter-hidden .text-area--cursor-line {
        opacity: 0;
    }

    .text-area--cursor-line {
        background: $primary-lighten-1;
    }
    """

    def __init__(self, **kwargs):
        self.typewriter_bottom_slack_lines = 0
        self._typewriter_adjusting = False
        self._typewriter_center_scheduled = False
        self._last_typewriter_center_state = None
        self._typewriter_recently_preserved = False
        self._typewriter_debug_enabled = bool(
            os.environ.get("HELOWRITE_TYPEWRITER_DEBUG", "")
        )
        super().__init__(**kwargs)
        self.language = None

    def set_typewriter_bottom_slack(self, lines: int) -> None:
        """Set extra virtual lines at EOF for typewriter centering."""
        safe_lines = max(0, int(lines))
        if self.typewriter_bottom_slack_lines == safe_lines:
            return
        self.typewriter_bottom_slack_lines = safe_lines
        self._refresh_size()

    def _can_center_typewriter(self) -> bool:
        return (
            getattr(self.app, "typewriter_mode", False)
            and not self._typewriter_adjusting
        )

    def _clear_typewriter_hidden(self) -> None:
        self.remove_class("typewriter-hidden")

    def _schedule_typewriter_center(self) -> None:
        if not self._typewriter_center_scheduled:
            self._typewriter_center_scheduled = True
            self.call_after_refresh(self._center_cursor_typewriter)

    def scroll_cursor_visible(self, *args, **kwargs):  # type: ignore[override]
        """Override to implement typewriter-mode centering.

        Calls super() first only outside typewriter mode. In typewriter mode we
        defer to our own centering logic and suppress repeated follow-up calls
        after a recent typewriter center.
        """
        if self._last_typewriter_center_state:
            last = self._last_typewriter_center_state
            if self.cursor_location == last["cursor"] and (
                self.scrollable_content_region.height == last["view_height"]
            ):
                # During refresh, max_scroll_y can briefly report a smaller value.
                # Don't restore a preserved scroll position that is currently invalid.
                if float(last["scroll_y"]) > float(self.max_scroll_y) + 1e-6:
                    self._clear_typewriter_hidden()
                    return None
                if abs(self.scroll_y - last["scroll_y"]) > 1e-6:
                    self.scroll_y = last["scroll_y"]
                if not self._typewriter_recently_preserved:
                    self._write_typewriter_debug("recent_center_preserved")
                    self._typewriter_recently_preserved = True
                self._clear_typewriter_hidden()
                return None
        if not self._can_center_typewriter():
            self._clear_typewriter_hidden()
            return super().scroll_cursor_visible(*args, **kwargs)
        if self._typewriter_center_scheduled:
            return None
        vp = self.scrollable_content_region.height
        if vp == 0:
            self._clear_typewriter_hidden()
            return None
        # During text reflow, max_scroll_y can transiently dip below the current
        # scroll position for a frame. Treat that frame as unstable and avoid
        # hide/schedule churn that would resolve to reveal_noop.
        if float(self.max_scroll_y) + 1e-6 < float(self.scroll_y):
            self._last_typewriter_center_state = {
                "cursor": self.cursor_location,
                "scroll_y": float(self.scroll_y),
                "target": float(self.scroll_y),
                "max_scroll_y": float(self.max_scroll_y),
                "view_height": int(vp),
            }
            self._clear_typewriter_hidden()
            return None
        if self._last_typewriter_center_state:
            last_cursor = self._last_typewriter_center_state["cursor"]
            same_row = self.cursor_location[0] == last_cursor[0]
            if same_row:
                target_scroll_y = self._get_typewriter_target_scroll_y()
                if abs(float(self.scroll_y) - target_scroll_y) < 1e-6:
                    self._last_typewriter_center_state = {
                        "cursor": self.cursor_location,
                        "scroll_y": float(self.scroll_y),
                        "target": float(target_scroll_y),
                        "max_scroll_y": float(self.max_scroll_y),
                        "view_height": int(vp),
                    }
                    self._clear_typewriter_hidden()
                    return None
        self.add_class("typewriter-hidden")
        self._write_typewriter_debug("hide")
        self._schedule_typewriter_center()
        return None

    def _get_typewriter_target_scroll_y(self) -> float:
        self._recompute_cursor_offset()
        _, vy = self._cursor_offset
        vp = self.scrollable_content_region.height
        half = vp // 2
        if getattr(self.app, "distraction_free", False):
            show_word_count = False
            config = getattr(self.app, "config", None)
            if config and hasattr(config, "get_show_word_count_distraction_free"):
                show_word_count = config.get_show_word_count_distraction_free()
            if show_word_count:
                half = max(half - 1, 0)
            else:
                half = max(half - 2, 0)
        return float(max(0, min(vy - half, self.max_scroll_y)))

    def _center_cursor_typewriter(self) -> None:
        """Apply typewriter centering after virtual_size has been updated."""
        self._typewriter_center_scheduled = False
        if not self._can_center_typewriter():
            self._clear_typewriter_hidden()
            return
        self._typewriter_adjusting = True
        try:
            vp = self.scrollable_content_region.height
            if vp == 0:
                self._clear_typewriter_hidden()
                return
            target_scroll_y = self._get_typewriter_target_scroll_y()
            if abs(float(self.scroll_y) - target_scroll_y) < 1e-6:
                self._last_typewriter_center_state = {
                    "cursor": self.cursor_location,
                    "scroll_y": float(self.scroll_y),
                    "target": float(target_scroll_y),
                    "max_scroll_y": float(self.max_scroll_y),
                    "view_height": int(vp),
                }
                self._clear_typewriter_hidden()
                self._write_typewriter_debug("reveal_noop")
                return
            self._write_typewriter_debug("center_start")
            self.scroll_y = target_scroll_y
            self._last_typewriter_center_state = {
                "cursor": self.cursor_location,
                "scroll_y": float(self.scroll_y),
                "target": float(target_scroll_y),
                "max_scroll_y": float(self.max_scroll_y),
                "view_height": int(vp),
            }
            self._typewriter_recently_preserved = False
            self._clear_typewriter_hidden()
            self._write_typewriter_debug("reveal")
            self._write_typewriter_debug("center_end")
        finally:
            self._typewriter_adjusting = False

    def _write_typewriter_debug(self, source: str) -> None:
        if not getattr(self.app, "typewriter_mode", False):
            return
        if not getattr(self, "_typewriter_debug_enabled", False):
            return
        try:
            path = getattr(self.app, "_typewriter_log_path", None)
            if path is None:
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            cursor_row, cursor_col = self.cursor_location
            vp = self.scrollable_content_region.height
            scroll_y = getattr(self, "scroll_y", "?")
            max_scroll_y = getattr(self, "max_scroll_y", "?")
            line = (
                f"{datetime.datetime.now().isoformat(timespec='milliseconds')}"
                f" source={source}"
                f" cursor=({cursor_row},{cursor_col})"
                f" scroll_y={scroll_y}"
                f" max_scroll_y={max_scroll_y}"
                f" view_height={vp}\n"
            )
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line)
        except Exception:
            pass

    def _refresh_size(self) -> None:
        """Refresh size and append optional virtual EOF slack lines."""
        super()._refresh_size()
        if getattr(self.app, "typewriter_mode", False):
            vp = self.scrollable_content_region.height
            if vp > 0:
                width, height = self.virtual_size
                extra = vp // 2 + self.typewriter_bottom_slack_lines
                self.virtual_size = Size(width, height + extra)

    def on_key(self, event):
        """Handle key presses, adding paragraph break on Enter."""
        if event.key == "enter":
            # Insert text directly and consume Enter so TextArea doesn't process
            # the same key a second time.
            self.insert("\n\n" if self.app.space_between_paragraphs else "\n")
            event.prevent_default()
            event.stop()
            if self.app.typewriter_mode:
                self.add_class("typewriter-hidden")
                self._write_typewriter_debug("hide_key_enter")
                self._schedule_typewriter_center()
                if self.app.typewriter_sounds:
                    self.app.play_sound("newline")
            else:
                self.call_after_refresh(self.scroll_cursor_visible)
            return True  # Prevent default handling

        if event.key == "backspace" and self.app.typewriter_mode:
            if self.app.typewriter_sounds:
                self.app.play_sound("ratchet")
            return False

        if self.app.typewriter_mode and event.key in ("up", "down"):
            self.add_class("typewriter-hidden")
            self._write_typewriter_debug(f"hide_key_{event.key}")
            self._schedule_typewriter_center()
            return False

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
            app = self.app
            app.file_path = file_path
            app.language = detect_language(file_path)
            try:
                content = file_path.read_text()
                editor = app.query_one("#editor", HeloWriteTextArea)
                editor.language = None if app.language == "text" else app.language
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
