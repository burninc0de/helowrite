import datetime
import os
import platform
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.style import Style
from textual.app import App, ComposeResult, SystemCommand
from textual.command import CommandPalette
from textual.timer import Timer
from textual.widgets import Footer, Header, Input, Static, TextArea

from config import Config
from git_sync import GitSyncResult, run_git_pull, run_git_pull_vault, run_git_push
from screens import (
    AboutScreen,
    HelpScreen,
    PomodoroTimerScreen,
    QuitConfirmScreen,
    RecentFilesScreen,
    SaveAsScreen,
    SettingsScreen,
    TimerCompleteScreen,
    WelcomeScreen,
)
from search import SearchMatch, SearchState
from styles import APP_DEFAULT_CSS
from themes import (
    apply_system_theme_update,
    choose_startup_theme,
    register_builtin_themes,
    register_system_theme,
)
from utils import (
    create_system_theme,
    detect_language,
    get_system_theme_last_modified,
    is_system_theme_available,
)
from widgets import CenteredEditor, FileOpenPanel, FindBar, HeloWriteTextArea, StatusBar


class HeloWriteCommandPalette(CommandPalette):
    """Custom command palette with nerd font search icon."""

    DEFAULT_CSS = """
    HeloWriteCommandPalette SearchIcon {
        color: $primary;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the command palette with custom icon."""
        from textual.command import CommandInput, CommandList, SearchIcon
        from textual.containers import Horizontal, Vertical
        from textual.widgets import Button, LoadingIndicator

        with Vertical(id="--container"):
            with Horizontal(id="--input"):
                # Use nerd font magnifying glass (\uf002)
                # Fallback to emoji if nerd font not available
                search_icon = SearchIcon()
                search_icon.icon = "\uf002"  # Nerd Font 'nf-fa-search'
                yield search_icon
                yield CommandInput(placeholder=self._placeholder, select_on_focus=False)
                if not self.run_on_select:
                    yield Button("\u25b6")
            with Vertical(id="--results"):
                yield CommandList()
                yield LoadingIndicator()


class HeloWrite(App):
    """A simple text editor TUI application."""

    DEFAULT_KEYBINDINGS = {
        "save": "ctrl+s",
        "quit": "ctrl+q",
        "open": "ctrl+o",
        "new": "ctrl+n",
        "find": "ctrl+f",
        "decrease_width": "alt+left",
        "increase_width": "alt+right",
        "select_all": "alt+a",
        "toggle_help": "f1",
        "settings": "f3",
        "recent_files": "f5",
        "create_daily_note": "alt+d",
        "toggle_distraction_free": "f11",
        "about": "f12",
        "git_push": "alt+g",
        "git_pull": "alt+h",
        "git_pull_vault": "alt+j",
        "change_to_parent_dir": "alt+up",
        "change_to_child_dir": "alt+down",
        "toggle_insert_newline": "alt+i",
        "pomodoro_timer": "ctrl+t",
        "toggle_typewriter_mode": "ctrl+shift+t",
    }

    DEFAULT_KEYBINDING_DESCRIPTIONS = {
        "save": "Save",
        "quit": "Quit",
        "open": "Open",
        "new": "New",
        "find": "Find",
        "decrease_width": "Decrease Width",
        "increase_width": "Increase Width",
        "select_all": "Select All",
        "toggle_help": "Help",
        "settings": "Settings",
        "recent_files": "Recent Files",
        "create_daily_note": "Create Daily Note",
        "toggle_distraction_free": "Distraction Free Mode",
        "about": "About",
        "git_push": "Git Push",
        "git_pull": "Git Pull",
        "git_pull_vault": "Git Pull Vault",
        "change_to_parent_dir": "Change to Parent Directory",
        "change_to_child_dir": "Change to Child Directory",
        "toggle_insert_newline": "Toggle Insert Newline",
        "pomodoro_timer": "Pomodoro Timer",
        "toggle_typewriter_mode": "Typewriter Mode",
    }

    BINDINGS = []

    @staticmethod
    def _read_text_with_fallback(path: Path) -> tuple[str, str]:
        """Read UTF-8 text with fallback for legacy cp1252-encoded files."""
        try:
            return path.read_text(encoding="utf-8"), "utf-8"
        except UnicodeDecodeError:
            return path.read_text(encoding="cp1252"), "cp1252"

    def read_text_file(self, path: Path, show_encoding_notice: bool = False) -> str:
        """Read file text safely for editor content and optional encoding notice."""
        content, encoding = self._read_text_with_fallback(path)
        if show_encoding_notice and encoding != "utf-8":
            self._feedback(
                "Loaded with legacy cp1252 encoding. Save to convert to UTF-8.",
                severity="warning",
                timeout=5,
            )
        return content

    @staticmethod
    def write_text_file(path: Path, text: str) -> None:
        """Write text using UTF-8 so smart quotes are portable across tools."""
        path.write_text(text, encoding="utf-8")

    def _bind_keybindings(self) -> None:
        """Bind actions using user keybindings or defaults."""
        self.config.save_default_keybindings(self.DEFAULT_KEYBINDINGS)
        saved_keybindings = self.config.get_keybindings()

        for action, default_key in self.DEFAULT_KEYBINDINGS.items():
            key = saved_keybindings.get(action, default_key)
            description = self.DEFAULT_KEYBINDING_DESCRIPTIONS.get(
                action, action.replace("_", " ").title()
            )
            try:
                self.bind(key, action, description=description)
            except Exception:
                # Ignore invalid or malformed binding values and continue.
                pass

    def get_system_commands(self, screen):
        from screens import WelcomeScreen

        is_welcome = any(isinstance(s, WelcomeScreen) for s in self.screen_stack)

        # Collect parent commands into a dict for easy lookup
        parent_commands = {}
        for cmd in super().get_system_commands(screen):
            if cmd.title not in ["Minimize", "Maximize", "Screenshot"] and not (
                cmd.title.startswith("Switch to textual-")
            ):
                parent_commands[cmd.title] = cmd

        # Yield in exact desired order (skip some on welcome screen)
        if not is_welcome:
            yield SystemCommand(
                "Workspace: Vault",
                "Switch working directory to vault",
                self.action_change_to_vault,
            )

        # Keys (skip on welcome screen)
        if not is_welcome and "Keys" in parent_commands:
            yield parent_commands["Keys"]

        # Pomodoro Timer (skip on welcome screen)
        if not is_welcome:
            yield SystemCommand(
                "Pomodoro Timer", "Start a focus timer", self.action_pomodoro_timer
            )

        # Settings
        yield SystemCommand(
            "Settings", "Open application settings", self.action_settings
        )

        # Theme
        if "Theme" in parent_commands:
            yield parent_commands["Theme"]

        # Typewriter Mode (skip on welcome screen)
        if not is_welcome:
            yield SystemCommand(
                "Typewriter Mode",
                "Toggle typewriter mode (centered cursor)",
                self.action_toggle_typewriter_mode,
            )

        # Distraction Free Mode (skip on welcome screen)
        if not is_welcome:
            yield SystemCommand(
                "Distraction Free Mode",
                "Toggle distraction-free mode",
                self.action_toggle_distraction_free,
            )

    DEFAULT_CSS = APP_DEFAULT_CSS

    def __init__(self, file_path: Optional[str] = None):
        super().__init__()
        self.file_path: Optional[Path] = Path(file_path) if file_path else None
        self.is_dirty = False
        self._original_text = ""
        self.console = Console()
        self.config = Config()
        self._bind_keybindings()
        self.distraction_free = False
        self.language = "text"
        self._word_count_timer: Optional[Timer] = None
        self.search_state = SearchState()
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

        # Smart quotes setting
        self.smart_quotes = self.config.get_smart_quotes()
        self.smart_quote_open_single = self.config.get_smart_quote_open_single()
        self.smart_quote_close_single = self.config.get_smart_quote_close_single()
        self.smart_quote_open_double = self.config.get_smart_quote_open_double()
        self.smart_quote_close_double = self.config.get_smart_quote_close_double()

        # Typewriter mode setting
        self.typewriter_mode = self.config.get_typewriter_mode()
        self.typewriter_sounds = self.config.get_typewriter_sounds()
        self._typewriter_adjusting = False
        self._typewriter_log_path = self.config.config_dir / "typewriter_debug.log"

        # Directory navigation stack
        self.dir_stack = []

        # System theme integration
        self._system_theme: Optional[dict] = None
        self._system_last_check: float = 0.0
        self._applying_system_update: bool = False
        self._system_watcher_active: bool = False
        self._system_watcher_timer: Optional[Timer] = None
        self._system_watch_interval_seconds: float = 1.0

        # Snippets
        self._snippets = self.config.get_snippets()
        self.snippet_highlighting_enabled = (
            self.config.get_snippet_highlighting_enabled()
        )
        self.markdown_highlighting_enabled = (
            self.config.get_markdown_highlighting_enabled()
        )

    @property
    def find_query(self) -> str:
        """Return the active find query."""
        return self.search_state.query

    @find_query.setter
    def find_query(self, value: str) -> None:
        self.search_state.query = value

    @property
    def find_matches(self) -> list[SearchMatch]:
        """Return active find matches for widget highlighting."""
        return self.search_state.matches

    @find_matches.setter
    def find_matches(self, value: list[SearchMatch]) -> None:
        self.search_state.matches = value

    @property
    def find_active_match_index(self) -> int:
        """Return the active find match index."""
        return self.search_state.active_match_index

    @find_active_match_index.setter
    def find_active_match_index(self, value: int) -> None:
        self.search_state.active_match_index = value

    def reload_snippets(self) -> None:
        """Reload snippets from config file."""
        self._snippets = self.config.get_snippets()
        try:
            editor = self.query_one("#editor", HeloWriteTextArea)
            editor._build_highlight_map()
            editor.refresh()
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield FindBar(id="find-bar")
        with CenteredEditor():
            yield HeloWriteTextArea(id="editor", highlight_cursor_line=False)
        yield StatusBar()
        yield Static("Welcome to HeloWrite! Press F1 for help.", id="message-bar")
        yield Footer()
        yield Static("", id="distraction-word-count")

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Load CLI-provided file FIRST, before any chdir, so paths are resolved
        # relative to where the user invoked the app (not the configured working dir)
        editor = self.query_one("#editor", HeloWriteTextArea)
        editor.focus()

        if self.file_path:
            self.file_path = Path(self.file_path).resolve()
            self.language = detect_language(self.file_path)
            editor.language = None if self.language == "text" else self.language
            if self.file_path.exists():
                try:
                    content = self.read_text_file(
                        self.file_path, show_encoding_notice=True
                    )
                    editor.load_text(content)
                    self._original_text = content
                    self.show_message(f"Loaded: {self.file_path}")
                except Exception as e:
                    self.show_message(f"Error loading file: {e}")

        # Change to default working directory if configured
        # This only affects the file manager panels, not CLI-provided files
        default_dir = self.config.get_default_working_directory()
        if default_dir and os.path.isdir(default_dir):
            try:
                os.chdir(default_dir)
            except Exception:
                pass

        # Git pull on load for Obsidian vault if enabled
        vault_path = self.config.get_obsidian_vault_path()
        git_pull_on_load = self.config.get_obsidian_git_pull_on_load()
        if vault_path and git_pull_on_load and os.path.isdir(vault_path):
            vault_git = os.path.join(vault_path, ".git")
            if os.path.isdir(vault_git):
                self.run_worker(self._async_git_pull_vault(vault_path))

        # Show welcome screen on first launch
        if self.config.get_show_welcome():
            self.push_screen(WelcomeScreen())

        register_builtin_themes(self)
        system_theme = create_system_theme()
        self._system_theme, self._system_last_check = register_system_theme(
            self,
            system_theme=system_theme,
            last_modified=get_system_theme_last_modified() or 0.0,
        )
        theme = choose_startup_theme(
            self.config, set(self.available_themes.keys()), self._system_theme
        )

        self.theme = theme
        self._theme_initialized = True
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
                    self.file_path = last_path.resolve()
                    self.show_message(f"Restoring last file: {self.file_path}")

        # Set language based on file extension
        self.language = detect_language(self.file_path)
        editor.language = None if self.language == "text" else self.language

        # Load file content (CLI file was loaded early; last file needs loading here)
        if self.file_path and self.file_path.exists():
            try:
                content = self.read_text_file(self.file_path, show_encoding_notice=True)
                editor.load_text(content)
                self._original_text = content
                # Restore cursor position for auto-loaded last file
                if (
                    self.config.get_open_last_file()
                    and str(self.file_path) == self.config.get_last_file_path()
                ):
                    saved_cursor = self.config.get_last_cursor_position()
                    lines = content.split("\n")
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

        # Start system theme watcher only if system theme is currently selected
        if self._system_theme and self.theme == "system":
            self._start_system_theme_watcher()

    def _start_system_theme_watcher(self) -> None:
        """Enable periodic checks for active system theme changes."""
        if self._system_watcher_active:
            return
        self._system_watcher_timer = self.set_interval(
            self._system_watch_interval_seconds, self._check_system_theme_update
        )
        self._system_watcher_active = True

    def _stop_system_theme_watcher(self) -> None:
        """Disable periodic checks for system theme changes."""
        if self._system_watcher_timer:
            self._system_watcher_timer.stop()
            self._system_watcher_timer = None
        self._system_watcher_active = False

    def _fallback_to_default_theme(self) -> None:
        """Fallback when system theme disappears or becomes invalid."""
        self._system_theme = None
        self._system_last_check = 0.0
        self._stop_system_theme_watcher()
        self.theme = "helowrite-dark"
        self.config.set_theme("helowrite-dark")
        self.notify(
            "System theme unavailable. Falling back to helowrite-dark.",
            severity="warning",
        )

    def watch_theme(self, old_theme: str, new_theme: str) -> None:
        """Called when the theme changes - save it to config."""
        if getattr(self, "_applying_system_update", False):
            return
        if old_theme != new_theme and getattr(self, "_theme_initialized", False):
            self.config.set_theme(new_theme)
            self.notify(f"Theme changed to {new_theme}", severity="information")
            self.apply_cursor_color()
            # Start/stop system theme watcher based on selection
            if new_theme == "system" and self._system_theme:
                self._start_system_theme_watcher()
            elif old_theme == "system":
                self._stop_system_theme_watcher()

    def _check_system_theme_update(self) -> None:
        """Check if system theme has changed and update if needed."""
        if not is_system_theme_available():
            if self.theme == "system":
                self._fallback_to_default_theme()
            return

        if not self._system_theme:
            self._system_theme = create_system_theme()
            self._system_last_check = get_system_theme_last_modified() or 0.0
            if not self._system_theme:
                return

        try:
            current_mtime = get_system_theme_last_modified() or 0.0
            if current_mtime > self._system_last_check:
                new_system_theme = create_system_theme()
                if new_system_theme:
                    self._system_theme = new_system_theme
                    self._system_last_check = current_mtime
                    if self.theme == "system":
                        self._applying_system_update = True
                        try:
                            apply_system_theme_update(self, new_system_theme)
                        finally:
                            self._applying_system_update = False

                        self.refresh_css()
                        self.screen.refresh()
                        # Re-apply dynamic cursor/syntax styles that depend on current theme.
                        self.apply_cursor_color()
                elif self.theme == "system":
                    self._fallback_to_default_theme()
        except Exception:
            pass

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

        if self.find_query:
            self.apply_find_query(self.find_query)

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

        # Rebuild snippet highlight map when the setting changes.
        try:
            if hasattr(editor, "_build_highlight_map"):
                editor._build_highlight_map()
                editor.refresh(layout=True)
        except Exception:
            pass

        # Keep typewriter layout synced if the mode is active.
        if self.typewriter_mode:
            try:
                editor._refresh_size()
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
            TextArea .text-area--cursor {{
                background: {color};
                color: #ffffff;
                text-style: bold;
            }}

            TextArea .text-area--cursor-line {{
                background: {cursor_line_color};
            }}

            TextArea .text-area--selection {{
                background: {color};
                color: #ffffff;
                text-style: bold;
            }}
            """

            # Add CSS to the app's stylesheet (will apply on next restart)
            self.stylesheet.add_source(cursor_css)

            highlight_color = (
                self.current_theme.primary
                if self.cursor_color.lower() == "theme"
                else self.cursor_color
            )
            try:
                editor._theme.syntax_styles["snippet"] = Style(
                    color=highlight_color,
                    bold=True,
                )
                editor._theme.syntax_styles["markdown_heading"] = Style(
                    color=highlight_color,
                    bold=True,
                )
                editor._theme.syntax_styles["markdown_link"] = Style(
                    color=highlight_color,
                    underline=True,
                )
                editor._theme.syntax_styles["markdown_image"] = Style(
                    color=highlight_color,
                    italic=True,
                )
                editor._theme.syntax_styles["markdown_blockquote"] = Style(
                    color=highlight_color,
                    dim=True,
                )
                editor._theme.syntax_styles["markdown_italic"] = Style(
                    color=highlight_color,
                    italic=True,
                )
                editor._theme.syntax_styles["markdown_bold"] = Style(
                    color=highlight_color,
                    bold=True,
                )
                editor._theme.syntax_styles["markdown_code"] = Style(
                    color=highlight_color,
                )
                editor._theme.syntax_styles["markdown_codeblock"] = Style(
                    color=highlight_color,
                    bold=True,
                )
                editor._theme.syntax_styles["search_result"] = Style(
                    bgcolor=highlight_color,
                    color=self.current_theme.background,
                )
                editor._theme.syntax_styles["search_result_current"] = Style(
                    bgcolor=highlight_color,
                    color=self.current_theme.background,
                    bold=True,
                )
            except Exception:
                pass

            editor.refresh(layout=True)
            try:
                self.refresh(layout=True)
            except Exception:
                pass
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
            self.write_text_file(self.file_path, text)
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
        self._stop_system_theme_watcher()
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

        def focus_tree() -> None:
            tree = self.query_one("#file-tree-panel")
            tree.focus()

        self.call_after_refresh(focus_tree)

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
        """Toggle the top search bar and focus the search input."""
        find_bar = self.query_one("#find-bar", FindBar)
        if find_bar.has_class("visible"):
            self.close_find_bar(clear_query=True)
            return

        find_bar.add_class("visible")
        find_input = find_bar.query_one("#find-input", Input)
        find_input.value = self.find_query
        find_bar.set_query(self.find_query)
        find_bar.set_match_count(len(self.find_matches), self.find_active_match_index)
        find_input.focus()

    def action_find_next(self):
        """Jump to the next search result."""
        if not self.find_matches:
            return

        match_index = self.search_state.select_next()
        self.jump_to_find_result(match_index)
        self.refresh_find_highlights()

    def action_find_previous(self) -> None:
        """Jump to the previous search result."""
        if not self.find_matches:
            return

        match_index = self.search_state.select_previous()
        self.jump_to_find_result(match_index)
        self.refresh_find_highlights()

    def close_find_bar(self, clear_query: bool = True) -> None:
        """Close the find bar and optionally clear search highlights."""
        find_bar = self.query_one("#find-bar", FindBar)
        find_bar.remove_class("visible")
        find_input = find_bar.query_one("#find-input", Input)
        find_input.value = ""
        find_bar.set_query("")

        if clear_query:
            self.search_state.clear()
            self.refresh_find_highlights()

        editor = self.query_one("#editor", HeloWriteTextArea)
        editor.focus()

    def refresh_find_highlights(self) -> None:
        """Rebuild highlights and update find-bar metadata."""
        try:
            editor = self.query_one("#editor", HeloWriteTextArea)
            editor._build_highlight_map()
            editor.refresh(layout=True)
        except Exception:
            pass

        try:
            find_bar = self.query_one("#find-bar", FindBar)
            find_bar.set_match_count(
                len(self.find_matches), self.find_active_match_index
            )
        except Exception:
            pass

    def apply_find_query(self, query: str) -> None:
        """Compute all matches for the active query and update highlights."""
        editor = self.query_one("#editor", HeloWriteTextArea)
        self.search_state.apply_query(editor.text, query)
        self.refresh_find_highlights()

    def jump_to_find_result(self, index: int) -> None:
        """Move cursor and scroll to a specific find result."""
        if index < 0 or index >= len(self.find_matches):
            return

        line, col, _ = self.find_matches[index]
        editor = self.query_one("#editor", HeloWriteTextArea)
        editor.cursor_location = (line, col)
        editor.scroll_cursor_visible()
        self.show_message(f"Match {index + 1}/{len(self.find_matches)}")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update find matches while typing in the find input."""
        if event.input.id == "find-input":
            find_bar = self.query_one("#find-bar", FindBar)
            find_bar.set_query(event.value)
            self.apply_find_query(event.value)

    def on_key(self, event) -> None:
        """Handle find-bar key controls while focus is in the find input."""
        try:
            focused = self.screen.focused
        except Exception:
            focused = None

        if isinstance(focused, Input) and focused.id == "find-input":
            if event.key == "escape":
                event.prevent_default()
                event.stop()
                self.close_find_bar(clear_query=True)
                return
            if event.key == "down":
                event.prevent_default()
                event.stop()
                self.action_find_next()
                return
            if event.key == "up":
                event.prevent_default()
                event.stop()
                self.action_find_previous()
                return
            if event.key in ("enter", "return"):
                event.prevent_default()
                event.stop()
                self.action_find_next()
                self.close_find_bar(clear_query=True)
                return

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
                self.write_text_file(Path(file_path), "")
            except Exception as e:
                self.show_message(f"Error creating daily note: {e}")
                return

        # Open the file
        file_path_obj = Path(file_path)
        self.file_path = file_path_obj
        self.language = detect_language(file_path_obj)
        try:
            content = self.read_text_file(file_path_obj, show_encoding_notice=True)
            editor = self.query_one("#editor", HeloWriteTextArea)
            editor.language = None if self.language == "text" else self.language
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
        """Show help screen in a modal."""
        self.push_screen(HelpScreen())

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

    def action_toggle_typewriter_mode(self):
        """Toggle typewriter mode (Ctrl+Shift+T / Alt+T)."""
        self.typewriter_mode = not self.typewriter_mode
        try:
            self.config.set_typewriter_mode(self.typewriter_mode)
        except Exception:
            pass
        if self.typewriter_mode:
            self._feedback(
                "Typewriter mode enabled (Ctrl+Shift+T or Alt+T to disable)",
                distraction_free_message="Typewriter on",
            )
        else:
            self._feedback(
                "Typewriter mode disabled (Ctrl+Shift+T or Alt+T to enable)",
                distraction_free_message="Typewriter off",
            )
        try:
            centered = self.query_one(CenteredEditor)
            centered.styles.padding_top = 0
        except Exception:
            pass
        try:
            editor = self.query_one("#editor", HeloWriteTextArea)
            editor._refresh_size()
            editor.scroll_cursor_visible()
        except Exception:
            pass

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

    def action_toggle_insert_newline(self):
        """Toggle insert newline (space between paragraphs) on Enter key."""
        self.space_between_paragraphs = not self.space_between_paragraphs
        self.config.set_space_between_paragraphs(self.space_between_paragraphs)
        status = "enabled" if self.space_between_paragraphs else "disabled"
        self.show_message(f"Insert newline: {status}")

    def action_command_palette(self) -> None:
        """Show the custom command palette with nerd font icon."""
        if self.use_command_palette and not HeloWriteCommandPalette.is_open(self):
            self.push_screen(HeloWriteCommandPalette(id="--command-palette"))

    def search_themes(self) -> None:
        """Show a fuzzy search command palette containing all registered themes."""
        from textual.theme import ThemeProvider

        self.push_screen(
            HeloWriteCommandPalette(
                providers=[ThemeProvider],
                placeholder="Search for themes…",
            )
        )

    def action_pomodoro_timer(self):
        """Launch the Pomodoro timer modal (Ctrl+T)."""
        self.push_screen(PomodoroTimerScreen())

    def start_timer(self, minutes: int):
        """Start the countdown timer."""

        total_seconds = minutes * 60
        self.show_message(f"Timer set for {minutes} minutes")

        def on_timer_complete():
            try:
                import shutil
                import subprocess
                from pathlib import Path

                sound_root = Path(__file__).parent / "audio"
                sound_path = sound_root / "bell.wav"
                if not sound_path.exists():
                    self.push_screen(TimerCompleteScreen())
                    return

                # Prioritize native backend first to avoid cross-platform binaries
                # shadowing each other (e.g., paplay installed on macOS).
                system = platform.system().lower()
                if system == "darwin":
                    backends = [["afplay"], ["paplay"], ["aplay"]]
                elif system == "windows":
                    backends = [
                        [
                            "powershell",
                            "-c",
                            "(New-Object System.Media.SoundPlayer).PlaySync()",
                        ]
                    ]
                else:
                    backends = [["paplay"], ["aplay"], ["afplay"]]

                for backend in backends:
                    if shutil.which(backend[0]):
                        if backend[0] == "powershell":
                            # Windows - use .NET to play
                            subprocess.run(
                                [
                                    "powershell",
                                    "-c",
                                    f"(New-Object System.Media.SoundPlayer '{sound_path}').PlaySync()",
                                ],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                        else:
                            subprocess.Popen(
                                backend + [str(sound_path)],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                        break
            except Exception:
                pass
            self.push_screen(TimerCompleteScreen())

        def tick(remaining: int) -> None:
            if remaining > 0:
                self.set_timer(1.0, lambda r=remaining - 1: tick(r))
            else:
                on_timer_complete()

        tick(total_seconds)

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

    def play_sound(self, sound_name: str) -> None:
        """Play a sound file using the same audio pipeline as the bell."""
        try:
            import random
            import shutil
            import subprocess
            from pathlib import Path

            sound_root = Path(__file__).parent / "audio"
            if sound_name in ("newline", "ratchet"):
                sound_path = sound_root / f"{sound_name}{random.randint(1, 3)}.wav"
            else:
                sound_path = sound_root / f"{sound_name}.wav"
            if not sound_path.exists():
                return

            system = platform.system().lower()
            if system == "darwin":
                backends = [["afplay"], ["paplay"], ["aplay"]]
            elif system == "windows":
                backends = [
                    [
                        "powershell",
                        "-c",
                        "(New-Object System.Media.SoundPlayer).PlaySync()",
                    ]
                ]
            else:
                backends = [["paplay"], ["aplay"], ["afplay"]]

            for backend in backends:
                if shutil.which(backend[0]):
                    if backend[0] == "powershell":
                        subprocess.run(
                            [
                                "powershell",
                                "-c",
                                f"(New-Object System.Media.SoundPlayer '{sound_path}').PlaySync()",
                            ],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    else:
                        subprocess.Popen(
                            backend + [str(sound_path)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    break
        except Exception:
            pass

    def perform_auto_save(self):
        """Perform auto-save if file is dirty and has a path."""
        if not self.is_dirty or not self.file_path:
            return
        try:
            editor = self.query_one("#editor", TextArea)
            text = editor.text
            self.write_text_file(self.file_path, text)
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

    def action_git_pull_vault(self):
        """Pull remote changes to vault repository (Alt+J)."""
        vault_path = self.config.get_obsidian_vault_path()
        if not vault_path:
            self.show_message("Please set Obsidian vault path in settings (F3)")
            return

        if not os.path.exists(vault_path):
            self.show_message("Vault path does not exist")
            return

        self.run_worker(self._async_git_pull_vault(vault_path))

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
        if self.file_path:
            self._apply_git_sync_result(await run_git_push(self.file_path))

    async def _async_git_pull(self):
        """Async part of git pull."""
        if self.file_path:
            self._apply_git_sync_result(await run_git_pull(self.file_path))

    async def _async_git_pull_vault(self, vault_path: str):
        """Async part of git pull for vault."""
        result = await run_git_pull_vault(Path(vault_path))
        if self.file_path:
            self.file_path = Path(str(self.file_path))
            if not str(self.file_path).startswith(vault_path):
                result.reload_current_file = False
        self._apply_git_sync_result(result)

    def _apply_git_sync_result(self, result: GitSyncResult) -> None:
        """Apply git sync side effects and show user feedback."""
        if result.refresh_file_panel:
            try:
                panel = self.query_one("#file-open-panel")
                tree = panel.query_one("#file-tree-panel")
                tree.reload()
            except Exception:
                pass

        if result.reload_current_file:
            self.reload_file_content()

        self._feedback(
            result.message,
            severity=result.severity,
            timeout=result.timeout,
        )

    def reload_file_content(self):
        """Reload the current file content into the editor after git pull."""
        if not self.file_path or not self.file_path.exists():
            return
        try:
            content = self.read_text_file(self.file_path)
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
