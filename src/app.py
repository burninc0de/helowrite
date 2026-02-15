import datetime
import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.theme import Theme
from textual.timer import Timer
from textual.widgets import Footer, Header, Static, TextArea

from config import Config
from constants import HELP_TEXT
from screens import (
    AboutScreen,
    QuitConfirmScreen,
    RecentFilesScreen,
    SaveAsScreen,
    SettingsScreen,
)
from utils import detect_language
from widgets import CenteredEditor, FileOpenPanel, HeloWriteTextArea, StatusBar


class HeloWrite(App):
    """A simple text editor TUI application."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+o", "open", "Open"),
        Binding("ctrl+n", "new", "New"),
        Binding("ctrl+f", "find", "Find/Replace", priority=True),
        Binding("alt+left", "decrease_width", "Decrease Width"),
        Binding("alt+right", "increase_width", "Increase Width"),
        Binding("alt+a", "select_all", "Select All"),
        Binding("f1", "toggle_help", "Help"),
        Binding("f3", "settings", "Settings"),
        Binding("f5", "recent_files", "Recent Files"),
        Binding("alt+d", "create_daily_note", "Create Daily Note"),
        Binding("f11", "toggle_distraction_free", "Distraction Free Mode"),
        Binding("f12", "about", "About"),
        Binding("alt+g", "git_push", "Git Push"),
        Binding("alt+h", "git_pull", "Git Pull"),
        Binding("alt+up", "change_to_parent_dir", "Change to Parent Directory"),
        Binding("alt+down", "change_to_child_dir", "Change to Child Directory"),
    ]

    def get_system_commands(self, screen):
        for cmd in super().get_system_commands(screen):
            # Filter out textual-light and textual-dark theme commands from command palette
            if cmd.title not in ["Minimize", "Maximize", "Screenshot"] and not (
                cmd.title.startswith("Switch to textual-")
            ):
                yield cmd
        yield SystemCommand(
            "Git Push", "Push current file changes to remote", self.action_git_push
        )
        yield SystemCommand(
            "Git Pull", "Pull remote changes and update editor", self.action_git_pull
        )
        yield SystemCommand(
            "Change to Vault",
            "Change working directory to Obsidian vault",
            self.action_change_to_vault,
        )

    DEFAULT_CSS = """Screen {
    background: $surface;
}

    CenteredEditor {
        align: center middle;
        height: 1fr;
        width: 100%;
        padding-bottom: 0;
    }

    CenteredEditor.distraction-free {
        padding-top: 2;
    }

    TextArea {
        border: none;
        background: transparent;
        width: 70%;
        height: 100%;
        padding: 2 4;
        scrollbar-size: 1 1;
        scrollbar-color: $surface-lighten-2;
        scrollbar-color-hover: $surface-lighten-1;
        scrollbar-background: $surface;
    }

    #editor {
        border: none;
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

    /* TextArea internal content background - force match screen */
    TextArea > .text-area--content {
        background: $surface !important;
    }

    /* Also try targeting the text area lines directly */
    .text-area--lines {
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

    StatusBar {
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
        height: 1;
        margin: 0;
    }

    #message-bar {
        background: $success;
        color: $text;
        padding: 0 1;
        height: 1;
        margin: 0;
    }

    Footer {
        padding: 0;
        margin: 0;
        dock: bottom;
    }

    #distraction-word-count {
        height: 1;
        text-align: right;
        padding: 0 2;
        margin: 1 0;
        color: $text;
        background: transparent;
        opacity: 0;
        display: none;
    }

    #distraction-word-count.visible {
        display: block;
        opacity: 0.3;
    }
    """

    def __init__(self, file_path: Optional[str] = None):
        super().__init__()
        self.file_path: Optional[Path] = Path(file_path) if file_path else None
        self.is_dirty = False
        self._original_text = ""
        self.console = Console()
        self.config = Config()
        self.distraction_free = False
        self.language = "text"
        self._word_count_timer: Optional[Timer] = None
        # Load editor settings
        self.editor_width = self.config.get_editor_width()
        self.cursor_color = self.config.get_cursor_color()
        # Auto-save settings
        self.auto_save_enabled = self.config.get_auto_save_enabled()
        self.auto_save_interval = self.config.get_auto_save_interval()
        self.auto_save_timer = None

        # Scrollbar setting
        self.scrollbar_enabled = self.config.get_scrollbar_enabled()

        # Space between paragraphs setting
        self.space_between_paragraphs = self.config.get_space_between_paragraphs()

        # Directory navigation stack
        self.dir_stack = []

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with CenteredEditor():
            yield HeloWriteTextArea(id="editor", highlight_cursor_line=False)
        yield StatusBar()
        yield Static("Welcome to HeloWrite! Press F1 for help.", id="message-bar")
        yield Footer()
        yield Static("", id="distraction-word-count")

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Register our custom themes
        helowrite_theme = Theme(
            name="helowrite-dark",
            primary="#7aa2f7",  # TokyoNight blue tones
            background="#1a1a2e",  # Deep dark blue background
            surface="#1a1a2e",  # Same as background
            foreground="#e6e6fa",  # Light lavender text
            dark=True,
        )
        self.register_theme(helowrite_theme)

        helowrite_light_theme = Theme(
            name="helowrite-light",
            primary="#61dafb",  # Bright cyan/blue accent
            background="#ffffff",  # Clean white background
            surface="#ffffff",  # Same as background
            foreground="#1a1a2e",  # Dark text on light background
            dark=False,  # Light theme
        )
        self.register_theme(helowrite_light_theme)

        # Register Kanso themes
        kanso_zen_theme = Theme(
            name="kanso-zen",
            primary="#8ba4b0",  # Blue accent from Kansō
            background="#090E13",  # Deep zen background
            surface="#090E13",  # Same as background
            foreground="#C5C9C7",  # Main foreground
            dark=True,
        )
        self.register_theme(kanso_zen_theme)

        kanso_pearl_theme = Theme(
            name="kanso-pearl",
            primary="#9fb5c9",  # Blue accent from Kansō pearl
            background="#f2f1ef",  # Pearl white background
            surface="#f2f1ef",  # Same as background
            foreground="#22262D",  # Dark text on light bg
            dark=False,  # Light theme
        )
        self.register_theme(kanso_pearl_theme)

        # Load saved theme now that UI is ready
        theme = self.config.get_theme()
        # Ensure theme is valid, default to helowrite-dark if not
        valid_themes = {"helowrite-dark", "helowrite-light", "kanso-zen", "kanso-pearl"}
        if theme not in valid_themes:
            theme = "helowrite-dark"
            self.config.set_theme("helowrite-dark")
        self.theme = theme
        # Force refresh to ensure theme colors are applied to Screen background
        self.screen.refresh()

        editor = self.query_one("#editor", HeloWriteTextArea)
        editor.focus()

        # Check if we should open the last file (when no CLI arg provided)
        if not self.file_path and self.config.get_open_last_file():
            last_file = self.config.get_last_file_path()
            if last_file:
                last_path = Path(last_file)
                if last_path.exists():
                    self.file_path = last_path
                    self.show_message(f"Restoring last file: {last_path}")
                else:
                    # Clear the invalid last file path
                    self.config.set_last_file_path("")

        # Set language based on file extension
        self.language = detect_language(self.file_path)
        editor.language = self.language

        # Load file if provided
        if self.file_path and self.file_path.exists():
            try:
                content = self.file_path.read_text()
                editor.load_text(content)
                self._original_text = content
                # Restore cursor position if this was an auto-loaded last file
                if (
                    self.config.get_open_last_file()
                    and str(self.file_path) == self.config.get_last_file_path()
                ):
                    saved_cursor = self.config.get_last_cursor_position()
                    lines = content.split("\n")
                    # Validate and clamp cursor position to file bounds
                    valid_line = max(0, min(saved_cursor[0], len(lines) - 1))
                    valid_col = max(0, min(saved_cursor[1], len(lines[valid_line])))
                    editor.cursor_location = (valid_line, valid_col)
                self.show_message(f"Loaded: {self.file_path}")
            except Exception as e:
                self.show_message(f"Error loading file: {e}")
        else:
            self.show_message(
                "HeloWrite - Ctrl+S:save, Ctrl+Q:quit, Ctrl+O:open, Ctrl+N:new, F1:help"
            )

        # Update status initially
        self.update_status()

        # Apply cursor color styling
        self.apply_cursor_color()

        # Apply editor settings
        self.apply_editor_settings()

        # Restore persisted distraction-free state (if enabled previously)
        try:
            self.distraction_free = self.config.get_distraction_free()
            # Apply UI changes for distraction-free if needed, without announcing
            self._apply_distraction_free_ui(announce=False)
            # Re-apply editor settings so layout/padding recalculates correctly
            self.apply_editor_settings()
        except Exception:
            pass

        # Start auto-save if enabled
        if self.auto_save_enabled:
            self.start_auto_save()

    def watch_theme(self, old_theme: str, new_theme: str) -> None:
        """Called when the theme changes - save it to config."""
        if old_theme != new_theme:
            self.config.set_theme(new_theme)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Called when text changes."""
        editor = self.query_one("#editor", HeloWriteTextArea)
        if editor.text != self._original_text:
            self.is_dirty = True
        self.update_status()
        # In distraction-free mode, hide word count while typing and show after inactivity
        if self.distraction_free:
            word_count_widget = self.query_one("#distraction-word-count", Static)
            # keep in layout but make invisible to avoid layout shifts
            try:
                word_count_widget.styles.opacity = 0
            except Exception:
                pass
            # Cancel any previous delayed show
            if self._word_count_timer is not None:
                self._word_count_timer.stop()
            # Schedule to show word count after 3 seconds of inactivity
            self._word_count_timer = self.set_timer(
                3.0, self.show_distraction_word_count
            )

    def on_text_area_selection_changed(self, event: TextArea.SelectionChanged) -> None:
        """Called when cursor/selection changes."""
        self.update_status()

    def update_status(self):
        """Update the status bar with current information."""
        editor = self.query_one("#editor", HeloWriteTextArea)
        status_bar = self.query_one(StatusBar)

        text = editor.text
        lines = text.split("\n")

        # Count words
        words = [word for line in lines for word in line.split() if word.strip()]
        word_count = len(words)

        status_bar.update_status(
            self.file_path,
            self.is_dirty,
            word_count,
            self.language,
        )

    def apply_editor_settings(self):
        """Apply current editor settings to the UI."""
        centered_editor = self.query_one(CenteredEditor)
        editor = self.query_one("#editor", HeloWriteTextArea)

        # Apply width
        editor.styles.width = f"{self.editor_width}%"

        # Apply distraction-free top padding if in distraction-free mode
        if self.distraction_free:
            centered_editor.styles.padding_top = 2
            # Update word count visibility in distraction-free mode
            word_count_widget = self.query_one("#distraction-word-count", Static)
            if self.config.get_show_word_count_distraction_free():
                word_count_widget.add_class("visible")
                self.update_distraction_word_count()
            else:
                word_count_widget.remove_class("visible")
        else:
            centered_editor.styles.padding_top = 0

        # Apply scrollbar visibility
        try:
            editor.styles.scrollbar_visibility = (
                "visible" if self.scrollbar_enabled else "hidden"
            )
        except Exception:
            pass

    def apply_cursor_color(self):
        """Apply cursor color styling dynamically."""
        try:
            editor = self.query_one("#editor", HeloWriteTextArea)

            # Use theme color if set to 'theme', otherwise use custom color
            if self.cursor_color.lower() == "theme":
                color = "$primary"
                # For theme colors, use a lighter variant for cursor line
                cursor_line_color = "$primary-lighten-1"
            else:
                color = self.cursor_color
                # For hex colors, append opacity
                cursor_line_color = f"{color}20"

            # Simple approach: add CSS that will apply on restart
            cursor_css = f"""
            TextArea > .text-area--cursor {{
                background: {color};
                color: #ffffff;
                text-style: bold;
            }}

            TextArea > .text-area--cursor-line {{
                background: {cursor_line_color};
            }}
            """

            # Add CSS to the app's stylesheet (will apply on next restart)
            self.stylesheet.add_source(cursor_css)
            editor.refresh(layout=True)
        except Exception:
            # If dynamic CSS fails, the static CSS will be used
            pass

    def update_distraction_word_count(self, *args):
        """Update the distraction-free word count display."""
        editor = self.query_one("#editor", HeloWriteTextArea)
        text = editor.text
        words = [
            word for line in text.split("\n") for word in line.split() if word.strip()
        ]
        word_count = len(words)
        widget = self.query_one("#distraction-word-count", Static)
        widget.update(f"{word_count} words")

    def show_distraction_word_count(self, *args):
        """Update and show the distraction-free word count after inactivity."""
        self.update_distraction_word_count()
        widget = self.query_one("#distraction-word-count", Static)
        try:
            widget.styles.opacity = 0.2
        except Exception:
            pass

    def show_message(self, message: str):
        """Show a message in the message bar."""
        message_bar = self.query_one("#message-bar", Static)
        message_bar.update(message)

    def action_save(self):
        """Save the current file."""
        editor = self.query_one("#editor", TextArea)
        text = editor.text

        if not self.file_path:
            # Show save-as dialog if no file path
            self.push_screen(SaveAsScreen())
            return

        try:
            self.file_path.write_text(text)
            self._original_text = text
            self.is_dirty = False
            self.update_status()
            self._feedback(
                f"Saved: {self.file_path}", distraction_free_message="Saved", timeout=2
            )
            # Save cursor position for potential auto-restore
            cursor_pos = editor.cursor_location
            self.config.set_last_cursor_position(cursor_pos)
            # Add to recent files
            self.config.add_recent_file(str(self.file_path))
            # Update last file path for open last file on startup
            self.config.set_last_file_path(str(self.file_path))
        except Exception as e:
            self._feedback(f"Error saving file: {e}", severity="error")

    async def action_quit(self):
        """Quit the application."""
        if self.is_dirty:
            self.push_screen(QuitConfirmScreen())
            return
        # Stop timers to allow clean exit
        if self._word_count_timer:
            self._word_count_timer.stop()
        self.stop_auto_save()
        self.exit()

    def action_open(self):
        """Open a file dialog as a right-side panel (toggle)."""
        # Toggle the file panel mounted inside the `CenteredEditor` (left side)
        try:
            existing = self.query_one("#file-open-panel")
            existing.remove()
            return
        except Exception:
            pass
        centered = self.query_one(CenteredEditor)
        editor = centered.query_one("#editor")
        # Mount the panel before the editor so it appears on the left
        centered.mount(FileOpenPanel(id="file-open-panel"), before=editor)
        # Auto-focus the file tree
        tree = self.query_one("#file-tree-panel")
        tree.focus()

    def action_new(self):
        """Create a new empty file."""
        editor = self.query_one("#editor", HeloWriteTextArea)
        editor.load_text("")
        self._original_text = ""
        self.file_path = None
        self.is_dirty = False
        self.update_status()
        self.show_message("New file created")

    def action_find(self):
        """Toggle find mode in status bar."""
        status_bar = self.query_one(StatusBar)
        if status_bar.find_mode:
            status_bar.disable_find_mode()
            # Return focus to editor
            editor = self.query_one("#editor", HeloWriteTextArea)
            editor.focus()
        else:
            status_bar.enable_find_mode()
            status_bar.focus()

    def action_find_next(self):
        """Find next occurrence of search text."""
        status_bar = self.query_one(StatusBar)
        if not status_bar.find_mode or not status_bar.find_text:
            return

        editor = self.query_one("#editor", HeloWriteTextArea)
        text = editor.text
        find_text = status_bar.find_text
        cursor_pos = editor.cursor_location

        # Find from current position
        start = (
            cursor_pos[1] + cursor_pos[0] * len(text.split("\n")[cursor_pos[0]])
            if cursor_pos[0] < len(text.split("\n"))
            else 0
        )
        pos = text.find(find_text, start)
        if pos == -1 and start > 0:  # Wrap around
            pos = text.find(find_text, 0)

        if pos != -1:
            # Calculate line and column
            lines = text[:pos].split("\n")
            line = len(lines) - 1
            col = len(lines[-1])
            editor.cursor_location = (line, col)
            self.show_message(f"Found at line {line + 1}, column {col + 1}")
        else:
            self.show_message("Text not found")

    def action_settings(self):
        """Open settings dialog."""
        self.push_screen(SettingsScreen())

    def action_recent_files(self):
        """Open recent files dialog (F5)."""
        self.push_screen(RecentFilesScreen())

    def action_create_daily_note(self):
        """Create daily note in Obsidian vault (Alt+D)."""
        vault_path = self.config.get_obsidian_vault_path()
        if not vault_path:
            self.show_message("Please set Obsidian vault path in settings (F3)")
            return

        if not os.path.exists(vault_path):
            self.show_message("Vault path does not exist")
            return

        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(vault_path, f"{date_str}.md")

        # Create the file if it doesn't exist
        if not os.path.exists(file_path):
            try:
                with open(file_path, "w") as f:
                    f.write("")
            except Exception as e:
                self.show_message(f"Error creating daily note: {e}")
                return

        # Open the file
        file_path_obj = Path(file_path)
        self.file_path = file_path_obj
        self.language = detect_language(file_path_obj)
        try:
            content = file_path_obj.read_text()
            editor = self.query_one("#editor", HeloWriteTextArea)
            editor.language = self.language
            editor.load_text(content)
            self._original_text = content
            self.show_message(f"Loaded: {file_path}")
            self.is_dirty = False
            self.update_status()
            # Save as last file if setting is enabled
            if self.config.get_open_last_file():
                self.config.set_last_file_path(file_path)
            # Add to recent files
            self.config.add_recent_file(file_path)
        except Exception as e:
            self.show_message(f"Error loading daily note: {e}")

    def action_change_to_vault(self):
        """Change working directory to Obsidian vault path."""
        vault_path = self.config.get_obsidian_vault_path()
        if not vault_path:
            self.show_message("Please set Obsidian vault path in settings (F3)")
            return

        if not os.path.exists(vault_path):
            self.show_message("Vault path does not exist")
            return

        try:
            os.chdir(vault_path)
            self.show_message(f"Changed working directory to: {vault_path}")
        except Exception as e:
            self.show_message(f"Error changing directory: {e}")

    def action_toggle_help(self):
        """Toggle help view on F1: show help or restore original content."""
        editor = self.query_one("#editor", HeloWriteTextArea)
        # If we're currently showing help, restore original content
        if getattr(self, "_in_help_mode", False) and hasattr(self, "_original_text"):
            editor.load_text(self._original_text)
            self._in_help_mode = False
            self.show_message("Returned to editing")
            return

        # Otherwise, save current content and show help
        self._original_text = editor.text
        editor.load_text(HELP_TEXT)
        self._in_help_mode = True
        self.show_message("Press F1 again to return to editing...")

    def action_toggle_distraction_free(self):
        """Toggle distraction-free mode (F11)."""
        # Toggle, persist, and apply UI changes
        self.distraction_free = not self.distraction_free
        try:
            self.config.set_distraction_free(self.distraction_free)
        except Exception:
            pass
        self._apply_distraction_free_ui(announce=True)
        # Apply padding/layout changes
        self.apply_editor_settings()

    def _apply_distraction_free_ui(self, announce: bool = True):
        """Apply UI changes for current `self.distraction_free` state.

        If `announce` is True, show a brief message to the user.
        """
        centered = self.query_one(CenteredEditor)
        editor = self.query_one("#editor", HeloWriteTextArea)
        header = self.query_one(Header)
        footer = self.query_one(Footer)
        status_bar = self.query_one(StatusBar)
        message_bar = self.query_one("#message-bar", Static)
        word_count_widget = self.query_one("#distraction-word-count", Static)

        if self.distraction_free:
            centered.add_class("distraction-free")
            editor.add_class("distraction-free")
            header.display = False
            footer.display = False
            status_bar.display = False
            message_bar.display = False
            # Show word count if enabled in settings
            if self.config.get_show_word_count_distraction_free():
                word_count_widget.add_class("visible")
                self.update_distraction_word_count()
            else:
                word_count_widget.remove_class("visible")
            editor.styles.width = "100%"
            # Add horizontal padding so the editor doesn't touch edges
            centered.styles.padding_left = 2
            centered.styles.padding_right = 2
            # Hide scrollbar in distraction-free mode
            try:
                editor.styles.scrollbar_visibility = "hidden"
            except Exception:
                pass
            if announce:
                self.show_message("Entered distraction-free mode (F11 to exit)")
        else:
            centered.remove_class("distraction-free")
            editor.remove_class("distraction-free")
            header.display = True
            footer.display = True
            status_bar.display = True
            message_bar.display = True
            # Hide word count
            word_count_widget.remove_class("visible")
            editor.styles.width = f"{self.editor_width}%"
            # Remove horizontal padding applied for distraction-free
            centered.styles.padding_left = 0
            centered.styles.padding_right = 0
            try:
                editor.styles.scrollbar_visibility = (
                    "visible" if self.scrollbar_enabled else "hidden"
                )
            except Exception:
                pass
            if announce:
                self.show_message("Exited distraction-free mode")

    def action_about(self):
        """Show about dialog."""
        self.push_screen(AboutScreen())

    def action_increase_width(self):
        """Increase editor width by 5%."""
        editor = self.query_one("#editor", HeloWriteTextArea)
        current_width = self.editor_width
        new_width = min(current_width + 5, 100)
        self.editor_width = new_width
        editor.styles.width = f"{new_width}%"
        self.config.set_editor_width(new_width)
        self.show_message(f"Editor width: {new_width}%")

    def action_decrease_width(self):
        """Decrease editor width by 5%."""
        editor = self.query_one("#editor", HeloWriteTextArea)
        current_width = self.editor_width
        new_width = max(current_width - 5, 20)
        self.editor_width = new_width
        editor.styles.width = f"{new_width}%"
        self.config.set_editor_width(new_width)
        self.show_message(f"Editor width: {new_width}%")

    def action_select_all(self):
        """Select all text in the editor."""
        editor = self.query_one("#editor", HeloWriteTextArea)
        editor.select_all()

    def start_auto_save(self):
        """Start the auto-save timer."""
        if self.auto_save_timer:
            self.auto_save_timer.stop()
        interval_seconds = self.auto_save_interval * 60
        self.auto_save_timer = self.set_interval(
            interval_seconds, self.perform_auto_save
        )

    def stop_auto_save(self):
        """Stop the auto-save timer."""
        if self.auto_save_timer:
            self.auto_save_timer.stop()
            self.auto_save_timer = None

    def perform_auto_save(self):
        """Perform auto-save if file is dirty and has a path."""
        if not self.is_dirty or not self.file_path:
            return
        try:
            editor = self.query_one("#editor", TextArea)
            text = editor.text
            self.file_path.write_text(text)
            self.is_dirty = False
            self.update_status()
            self._feedback(
                f"Auto-saved at {datetime.datetime.now().strftime('%H:%M:%S')}",
                timeout=2,
                show_in_distraction_free=False,
            )
        except Exception as e:
            self.show_message(f"Auto-save failed: {e}")

    def _feedback(
        self,
        message: str,
        severity: str = "information",
        timeout: int = 5,
        show_in_distraction_free: bool = True,
        distraction_free_message: Optional[str] = None,
    ):
        """Show feedback via notification in distraction-free mode, message bar otherwise."""
        if self.distraction_free and show_in_distraction_free:
            msg = distraction_free_message if distraction_free_message else message
            self.notify(msg, severity=severity, timeout=timeout)
        elif not self.distraction_free:
            self.show_message(message)

    def action_git_push(self):
        """Push current file changes to remote (Alt+G)."""
        if not self.file_path:
            self.show_message("No file open")
            return

        self.run_worker(self._async_git_push())

    def action_git_pull(self):
        """Pull remote changes and update editor (Alt+H)."""
        if not self.file_path:
            self.show_message("No file open")
            return

        self.run_worker(self._async_git_pull())

    def action_change_to_parent_dir(self):
        """Change working directory to parent directory (Alt+Up)."""
        current_dir = os.getcwd()
        parent_dir = os.path.dirname(current_dir)
        if parent_dir != current_dir:
            self.dir_stack.append(current_dir)
            os.chdir(parent_dir)
            self.show_message(f"Changed directory to: {parent_dir}")
            # Refresh file manager if open
            try:
                panel = self.query_one("#file-open-panel")
                tree = panel.query_one("#file-tree-panel")
                tree.reload()
            except Exception:
                pass
        else:
            self.show_message("Already at root directory")

    def action_change_to_child_dir(self):
        """Change working directory back to previous directory (Alt+Down)."""
        if self.dir_stack:
            target_dir = self.dir_stack.pop()
            os.chdir(target_dir)
            self.show_message(f"Changed directory to: {target_dir}")
            # Refresh file manager if open
            try:
                panel = self.query_one("#file-open-panel")
                tree = panel.query_one("#file-tree-panel")
                tree.reload()
            except Exception:
                pass
        else:
            self.show_message("No previous directory to go back to")

    async def _async_git_push(self):
        """Async part of git push."""
        import asyncio
        import os
        import subprocess

        file_dir = str(self.file_path.parent)
        file_name = str(self.file_path.name)
        log_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "git_sync_errors.log"
        )

        async def run_subprocess(cmd, cwd):
            return await asyncio.to_thread(
                subprocess.run, cmd, cwd=cwd, capture_output=True, text=True, check=True
            )

        try:
            current_cmd = None

            # Stash any unstaged changes
            current_cmd = "git stash push"
            cmd = ["git", "stash", "push", "-m", "auto-stash before sync"]
            try:
                await run_subprocess(cmd, file_dir)
            except subprocess.CalledProcessError as e:
                if (
                    "No local changes to save" in e.stdout
                    or "No local changes to save" in e.stderr
                ):
                    pass  # No changes to stash, continue
                else:
                    raise

            # Pop the stash
            current_cmd = "git stash pop"
            cmd = ["git", "stash", "pop"]
            try:
                await run_subprocess(cmd, file_dir)
            except subprocess.CalledProcessError as e:
                if "No stash entries found" in e.stderr:
                    pass  # No stash to pop, continue
                else:
                    # If stash pop fails due to conflicts, abort the push
                    error_msg = "Git push aborted: conflicts detected when restoring stashed changes. Please resolve manually."
                    self._feedback(error_msg, severity="error", timeout=10)
                    # Try to abort any ongoing rebase/merge
                    try:
                        abort_cmd = ["git", "rebase", "--abort"]
                        await run_subprocess(abort_cmd, file_dir)
                    except subprocess.CalledProcessError:
                        pass  # Ignore if no rebase to abort
                    try:
                        abort_cmd = ["git", "merge", "--abort"]
                        await run_subprocess(abort_cmd, file_dir)
                    except subprocess.CalledProcessError:
                        pass  # Ignore if no merge to abort
                    return

            # git add
            current_cmd = "git add"
            cmd = ["git", "add", file_name]
            await run_subprocess(cmd, file_dir)

            # git commit
            current_cmd = "git commit"
            commit_msg = f"Update {file_name}"
            cmd = ["git", "commit", "-m", commit_msg]
            try:
                await run_subprocess(cmd, file_dir)
            except subprocess.CalledProcessError as e:
                if "nothing to commit" in e.stdout or "nothing to commit" in e.stderr:
                    self._feedback("No changes to commit", timeout=2)
                    return  # Skip push
                else:
                    raise

            # git push
            current_cmd = "git push"
            cmd = ["git", "push"]
            try:
                await run_subprocess(cmd, file_dir)
            except subprocess.CalledProcessError as e:
                if (
                    "Everything up-to-date" in e.stdout
                    or "Everything up-to-date" in e.stderr
                    or "up to date" in e.stdout
                    or "up to date" in e.stderr
                ):
                    pass  # Already pushed, continue
                else:
                    raise

            self._feedback(f"Git push completed for {file_name}", timeout=2)
        except subprocess.CalledProcessError as e:
            error_details = (
                e.stderr.strip()
                or e.stdout.strip()
                or f"Command failed with return code {e.returncode}"
            )
            if "up to date" in error_details:
                self._feedback("Git push completed (already up to date)", timeout=2)
            else:
                # Check for specific error that requires pulling first
                if (
                    "Updates were rejected because the remote contains work"
                    in error_details
                ):
                    error_msg = "Git push failed: remote has changes you don't have. Try pulling first with Alt+H, then push again."
                elif "no upstream branch" in error_details:
                    error_msg = "Git push failed: no upstream branch set. Try pulling first with Alt+H to set it up."
                else:
                    error_msg = "Git push failed - check git_sync_errors.log for details. You may need to resolve conflicts manually."
                with open(log_file, "a") as f:
                    f.write(f"Command '{current_cmd}' failed: {error_details}\n")
                self._feedback(error_msg, severity="error", timeout=10)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            with open(log_file, "a") as f:
                f.write(error_msg + "\n")
            self._feedback(error_msg, severity="error", timeout=10)

    async def _async_git_pull(self):
        """Async part of git pull."""
        import asyncio
        import os
        import subprocess

        file_dir = str(self.file_path.parent)
        file_name = str(self.file_path.name)
        log_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "git_sync_errors.log"
        )

        async def run_subprocess(cmd, cwd):
            return await asyncio.to_thread(
                subprocess.run, cmd, cwd=cwd, capture_output=True, text=True, check=True
            )

        try:
            current_cmd = None

            # Stash any unstaged changes
            current_cmd = "git stash push"
            cmd = ["git", "stash", "push", "-m", "auto-stash before pull"]
            try:
                await run_subprocess(cmd, file_dir)
            except subprocess.CalledProcessError as e:
                if (
                    "No local changes to save" in e.stdout
                    or "No local changes to save" in e.stderr
                ):
                    pass  # No changes to stash, continue
                else:
                    raise

            # git pull (using merge instead of rebase to avoid conflicts)
            current_cmd = "git pull"
            cmd = ["git", "pull"]
            try:
                await run_subprocess(cmd, file_dir)
            except subprocess.CalledProcessError as e:
                if (
                    "Already up to date" in e.stdout
                    or "Already up to date" in e.stderr
                    or "up to date" in e.stdout
                    or "up to date" in e.stderr
                ):
                    pass  # Already up to date, continue
                elif "There is no tracking information" in e.stderr:
                    # Try to infer and set upstream
                    try:
                        # Get current branch
                        branch_cmd = ["git", "branch", "--show-current"]
                        branch_result = await run_subprocess(branch_cmd, file_dir)
                        current_branch = branch_result.stdout.strip()

                        # Get remotes
                        remote_cmd = ["git", "remote"]
                        remote_result = await run_subprocess(remote_cmd, file_dir)
                        remotes = remote_result.stdout.strip().split("\n")

                        if "origin" in remotes:
                            # Set upstream and retry pull
                            upstream_cmd = [
                                "git",
                                "branch",
                                "--set-upstream-to",
                                f"origin/{current_branch}",
                                current_branch,
                            ]
                            await run_subprocess(upstream_cmd, file_dir)

                            # Retry pull
                            cmd = ["git", "pull"]
                            await run_subprocess(cmd, file_dir)
                        else:
                            raise  # No origin remote, re-raise original error
                    except subprocess.CalledProcessError:
                        raise  # Re-raise original error if inference fails
                else:
                    raise

            # Pop the stash
            current_cmd = "git stash pop"
            cmd = ["git", "stash", "pop"]
            try:
                await run_subprocess(cmd, file_dir)
            except subprocess.CalledProcessError as e:
                if "No stash entries found" in e.stderr:
                    pass  # No stash to pop, continue
                else:
                    # If stash pop fails due to conflicts, abort the pull
                    error_msg = "Git pull aborted: conflicts detected when restoring stashed changes. Please resolve manually."
                    self._feedback(error_msg, severity="error", timeout=10)
                    # Try to abort any ongoing rebase/merge
                    try:
                        abort_cmd = ["git", "rebase", "--abort"]
                        await run_subprocess(abort_cmd, file_dir)
                    except subprocess.CalledProcessError:
                        pass  # Ignore if no rebase to abort
                    try:
                        abort_cmd = ["git", "merge", "--abort"]
                        await run_subprocess(abort_cmd, file_dir)
                    except subprocess.CalledProcessError:
                        pass  # Ignore if no merge to abort
                    return

            # Reload file content in editor after successful pull
            self.reload_file_content()

            self._feedback(f"Git pull completed for {file_name}", timeout=2)
        except subprocess.CalledProcessError as e:
            error_details = (
                e.stderr.strip()
                or e.stdout.strip()
                or f"Command failed with return code {e.returncode}"
            )
            if "up to date" in error_details:
                self._feedback("Git pull completed (already up to date)", timeout=2)
            else:
                error_msg = "Git pull failed - check git_sync_errors.log for details. You may need to resolve conflicts manually."
                with open(log_file, "a") as f:
                    f.write(f"Command '{current_cmd}' failed: {error_details}\n")
                self._feedback(error_msg, severity="error", timeout=10)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            with open(log_file, "a") as f:
                f.write(error_msg + "\n")
            self._feedback(error_msg, severity="error", timeout=10)

    def reload_file_content(self):
        """Reload the current file content into the editor after git pull."""
        if not self.file_path or not self.file_path.exists():
            return
        try:
            content = self.file_path.read_text(encoding="utf-8")
            if content != self._original_text:
                editor = self.query_one("#editor", HeloWriteTextArea)
                # Save current cursor position
                saved_cursor = editor.cursor_location
                # Load new content
                editor.load_text(content)
                # Restore cursor position, clamped to new content bounds
                lines = content.split("\n")
                valid_line = max(0, min(saved_cursor[0], len(lines) - 1))
                valid_col = max(0, min(saved_cursor[1], len(lines[valid_line])))
                editor.cursor_location = (valid_line, valid_col)
                self._original_text = content
                self.is_dirty = False
                self.update_status()
        except Exception as e:
            self._feedback(
                f"Error reloading file after pull: {e}", severity="error", timeout=5
            )


def main():
    """Main entry point for the application."""
    import sys

    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = HeloWrite(file_path)
    app.run()


if __name__ == "__main__":
    main()
