"""Modal screens for HeloWrite."""

import os
from pathlib import Path
from typing import Any, cast

import pyfiglet
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Checkbox, DirectoryTree, Input, Static

from src.utils import detect_language
from src.widgets import HeloWriteTextArea


class FileOpenScreen(ModalScreen):
    """Modal panel for opening files using a directory tree.

    This appears as a right-side panel so it doesn't block the whole UI.
    """

    DEFAULT_CSS = """
    FileOpenScreen {
        width: 40%;
        height: 100%;
        dock: right;
        align: center middle;
        background: $surface;
        padding: 1 1;
    }

    #file-open-header {
        padding-bottom: 1;
    }

    #file-tree {
        height: 1fr;
        overflow: auto;
        scrollbar-size: 1 1;
        scrollbar-color: $surface-lighten-2;
        scrollbar-color-hover: $surface-lighten-1;
        scrollbar-background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(
                "Select a file to open (press Escape to cancel)", id="file-open-header"
            )
            yield DirectoryTree("./", id="file-tree")

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Handle file selection and close the panel."""
        file_path = Path(event.path)
        if file_path.is_file():
            app = self.app
            app.file_path = file_path  # type: ignore
            app.language = detect_language(file_path)  # type: ignore
            try:
                content = file_path.read_text()
                editor = app.query_one("#editor", HeloWriteTextArea)
                editor.language = app.language
                editor.load_text(content)
                app._original_text = content  # type: ignore
                app.show_message(f"Loaded: {file_path}")  # type: ignore
                app.is_dirty = False  # type: ignore
                app.update_status()  # type: ignore
                # Save as last file if setting is enabled
                if app.config.get_open_last_file():  # type: ignore
                    app.config.set_last_file_path(str(file_path))  # type: ignore
                # Add to recent files
                app.config.add_recent_file(str(file_path))  # type: ignore
            except Exception as e:
                app.show_message(f"Error loading file: {e}")  # type: ignore
        self.app.pop_screen()

    def on_key(self, event) -> None:
        """Allow closing the file-open panel with Escape."""
        if getattr(event, "key", None) == "escape":
            self.app.pop_screen()


class SettingsScreen(ModalScreen):
    """Screen for adjusting editor settings - TUI native design."""

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
    }

    #settings-frame {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #settings-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .setting-row {
        height: 1;
        margin-bottom: 1;
    }

    .setting-label {
        width: 35;
        color: $text;
    }

    .setting-value {
        color: $primary;
    }

    .setting-input {
        width: 12;
        height: 1;
    }

    #settings-footer {
        text-align: center;
        color: $text-muted;
        text-style: dim;
        margin-top: 1;
    }

    SettingsScreen Input {
        border: none;
        background: $surface-darken-1;
        padding: 0 1;
        height: 1;
        color: $text;
    }

    SettingsScreen Input:focus {
        border: none;
        padding: 0 1;
        height: 1;
    }

    SettingsScreen Checkbox {
        height: 1;
        margin: 0;
        border: none;
        padding: 0;
    }

    SettingsScreen Checkbox:focus {
        border: none;
        padding: 0;
        height: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-frame"):
            yield Static(" Settings ", id="settings-title")
            with Horizontal(classes="setting-row"):
                yield Checkbox(
                    " Open last file on startup", id="open-last-file-checkbox"
                )
            with Horizontal(classes="setting-row"):
                yield Checkbox(
                    " Show word count in distraction-free mode",
                    id="show-word-count-checkbox",
                )
            with Horizontal(classes="setting-row"):
                yield Checkbox(" Enable auto-save", id="auto-save-checkbox")
            with Horizontal(classes="setting-row"):
                yield Checkbox(" Show scrollbar", id="show-scrollbar-checkbox")
            with Horizontal(classes="setting-row"):
                yield Static("Auto-save interval:", classes="setting-label")
                yield Input(id="auto-save-interval-input", classes="setting-input")
                yield Static(" minutes (1, 5, or 10)", classes="setting-value")
            with Horizontal(classes="setting-row"):
                yield Static("Editor width:", classes="setting-label")
                yield Input(id="width-input", classes="setting-input")
                yield Static(" %", classes="setting-value")
            with Horizontal(classes="setting-row"):
                yield Static("Line height:", classes="setting-label")
                yield Input(id="line-height-input", classes="setting-input")
                yield Static(" em", classes="setting-value")
            with Horizontal(classes="setting-row"):
                yield Static("Cursor color:", classes="setting-label")
                yield Input(id="cursor-color-input", classes="setting-input")
                yield Static(" (hex #RRGGBB or 't')", classes="setting-value")
            with Horizontal(classes="setting-row"):
                yield Static("Obsidian vault path:", classes="setting-label")
                yield Input(id="vault-path-input", classes="setting-input")
                yield Static(" (path to vault)", classes="setting-value")
            yield Static(
                "Enter: save | Esc: cancel | Tab: navigate", id="settings-footer"
            )

    def on_mount(self):
        """Pre-fill inputs with current settings."""
        app = cast(Any, self.app)
        self.query_one(
            "#open-last-file-checkbox", Checkbox
        ).value = app.config.get_open_last_file()
        self.query_one(
            "#show-word-count-checkbox", Checkbox
        ).value = app.config.get_show_word_count_distraction_free()
        self.query_one(
            "#auto-save-checkbox", Checkbox
        ).value = app.config.get_auto_save_enabled()
        self.query_one(
            "#show-scrollbar-checkbox", Checkbox
        ).value = app.scrollbar_enabled
        self.query_one("#width-input", Input).value = str(app.editor_width)
        self.query_one("#line-height-input", Input).value = str(app.line_height)
        self.query_one("#cursor-color-input", Input).value = app.cursor_color
        self.query_one(
            "#vault-path-input", Input
        ).value = app.config.get_obsidian_vault_path()
        self.query_one("#auto-save-interval-input", Input).value = str(
            app.config.get_auto_save_interval()
        )

        # Focus first focusable widget
        self.query_one("#open-last-file-checkbox", Checkbox).focus()

    def on_key(self, event):
        """Handle key presses."""
        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "enter":
            self.save_settings()

    def _is_typing_in_input(self) -> bool:
        """Check if currently focused on an input field."""
        try:
            focused = self.screen.focused
            return isinstance(focused, Input)
        except Exception:
            return False

    def save_settings(self):
        """Save settings and apply them."""
        try:
            app = cast(Any, self.app)
            open_last_file = self.query_one("#open-last-file-checkbox", Checkbox).value
            show_word_count = self.query_one(
                "#show-word-count-checkbox", Checkbox
            ).value
            auto_save_enabled = self.query_one("#auto-save-checkbox", Checkbox).value
            width_str = self.query_one("#width-input", Input).value.strip()
            line_height_str = self.query_one("#line-height-input", Input).value.strip()
            cursor_color = self.query_one("#cursor-color-input", Input).value.strip()
            vault_path = self.query_one("#vault-path-input", Input).value.strip()
            auto_save_interval_str = self.query_one(
                "#auto-save-interval-input", Input
            ).value.strip()
            scrollbar_enabled = self.query_one(
                "#show-scrollbar-checkbox", Checkbox
            ).value

            # Parse values
            width = int(width_str) if width_str else app.editor_width
            line_height = float(line_height_str) if line_height_str else app.line_height
            auto_save_interval = (
                int(auto_save_interval_str) if auto_save_interval_str else 5
            )

            # Validate ranges
            if not (10 <= width <= 90):
                app.show_message("Width must be between 10-90%")
                return
            if not (1.0 <= line_height <= 2.0):
                app.show_message("Line height must be between 1.0-2.0")
                return
            if auto_save_interval not in [1, 5, 10]:
                app.show_message("Auto-save interval must be 1, 5, or 10 minutes")
                return

            # Validate cursor color format (hex or 'theme')
            if cursor_color.lower() != "theme" and (
                not cursor_color.startswith("#") or len(cursor_color) not in [4, 7]
            ):
                app.show_message("Cursor color must be hex like #4a9eff or 'theme'")
                return

            # Validate vault path if provided
            if vault_path and not (
                os.path.exists(vault_path) and os.path.isdir(vault_path)
            ):
                app.show_message("Vault path must be an existing directory")
                return

            # Save to config
            app.config.set_open_last_file(open_last_file)
            app.config.set_show_word_count_distraction_free(show_word_count)
            app.config.set_auto_save_enabled(auto_save_enabled)
            app.config.set_editor_width(width)
            app.config.set_line_height(line_height)
            app.config.set_cursor_color(cursor_color)
            app.config.set_obsidian_vault_path(vault_path)
            app.config.set_auto_save_interval(auto_save_interval)
            app.config.set_scrollbar_enabled(scrollbar_enabled)

            # Update app settings
            app.editor_width = width
            app.line_height = line_height
            app.cursor_color = cursor_color

            # Apply auto-save
            app.auto_save_enabled = auto_save_enabled
            app.auto_save_interval = auto_save_interval
            if auto_save_enabled:
                app.start_auto_save()
            else:
                app.stop_auto_save()

            # Update scrollbar setting
            app.scrollbar_enabled = scrollbar_enabled

            # Apply settings
            app.apply_editor_settings()

            app.show_message("Settings saved!")
            self.app.pop_screen()

        except ValueError:
            app.show_message("Please enter valid numbers")


class AboutScreen(ModalScreen):
    """Screen showing about information with ASCII art."""

    DEFAULT_CSS = """
    AboutScreen {
        align: center middle;
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

Version: 1.0

Press Escape to close"""
        with Vertical(id="about-container"):
            yield Static(about_text, id="about-content")

    def on_key(self, event):
        """Handle key presses to close on Escape."""
        if event.key == "escape":
            self.app.pop_screen()


class SaveAsScreen(ModalScreen):
    """Modal screen for saving a new file with a filename."""

    DEFAULT_CSS = """
    SaveAsScreen {
        align: center middle;
    }

    #save-container {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #save-header {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #filename-input {
        margin-bottom: 1;
    }

    #save-footer {
        text-align: center;
        color: $text-muted;
        text-style: dim;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="save-container"):
            yield Static(" Save As ", id="save-header")
            yield Input(placeholder="Enter filename...", id="filename-input")
            yield Static("Enter: save | Esc: cancel", id="save-footer")

    def on_mount(self):
        """Focus the input field on mount."""
        self.query_one("#filename-input", Input).focus()

    def on_key(self, event):
        """Handle key presses to save on Enter or close on Escape."""
        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "enter":
            self.save_file()

    def save_file(self):
        """Save the file with the entered filename."""
        app = cast(Any, self.app)
        filename = self.query_one("#filename-input", Input).value.strip()

        if not filename:
            app.show_message("Please enter a filename")
            return

        # Ensure the filename has an extension
        if not Path(filename).suffix:
            filename += ".txt"

        # Create the full path in the current directory
        file_path = Path(filename)

        try:
            editor = app.query_one("#editor", HeloWriteTextArea)
            text = editor.text

            file_path.write_text(text)
            app.file_path = file_path
            app.language = detect_language(file_path)
            editor.language = app.language
            app.is_dirty = False
            app.update_status()
            app.show_message(f"Saved: {file_path}")
            self.app.pop_screen()
        except Exception as e:
            app.show_message(f"Error saving file: {e}")


class QuitConfirmScreen(ModalScreen):
    """Screen to confirm quitting with unsaved changes - TUI native design."""

    DEFAULT_CSS = """
    QuitConfirmScreen {
        align: center middle;
    }

    #quit-container {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $warning;
        padding: 1 2;
    }

    #quit-header {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #quit-message {
        text-align: center;
        margin-bottom: 1;
    }

    #quit-options {
        text-align: center;
        color: $primary;
        margin-bottom: 1;
    }

    #quit-footer {
        text-align: center;
        color: $text-muted;
        text-style: dim;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="quit-container"):
            yield Static(" Unsaved Changes ", id="quit-header")
            yield Static(
                "You have unsaved changes. What would you like to do?",
                id="quit-message",
            )
            yield Static(
                "S: Save & Quit | Q: Discard & Quit | Esc: Cancel", id="quit-footer"
            )

    def on_key(self, event) -> None:
        """Handle key presses."""
        app = cast(Any, self.app)
        if event.key == "escape" or event.key == "c":
            self.app.pop_screen()
        elif event.key == "s":
            app.action_save()
            app.exit()
        elif event.key == "q":
            app.exit()
        elif event.key == "q":
            app.exit()


class RecentFilesScreen(ModalScreen):
    """Modal screen showing recent files for quick access."""

    DEFAULT_CSS = """
    RecentFilesScreen {
        align: center middle;
    }

    #recent-container {
        width: 70;
        height: auto;
        max-height: 20;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #recent-header {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #recent-list {
        height: auto;
        max-height: 12;
        border: solid $primary;
    }

    #recent-empty {
        text-align: center;
        color: $text-muted;
        padding: 1;
    }

    #recent-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="recent-container"):
            yield Static("Recent Files", id="recent-header")
            app = cast(Any, self.app)
            recent_files = app.config.get_recent_files()
            if recent_files:
                from textual.widgets import OptionList

                options = [
                    f"{i + 1}. {Path(f).name}" for i, f in enumerate(recent_files)
                ]
                yield OptionList(*options, id="recent-list")
                yield Static(
                    "↑↓ to select, Enter to open, Esc to close", id="recent-hint"
                )
            else:
                yield Static("No recent files", id="recent-empty")
                yield Static("Press Escape to close", id="recent-hint")

    def on_key(self, event) -> None:
        """Handle key presses - Enter opens selected file, Esc closes."""
        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "enter":
            self.open_selected_file()

    def open_selected_file(self):
        """Open the currently selected file."""
        try:
            app = cast(Any, self.app)
            from textual.widgets import OptionList

            list_widget = self.query_one("#recent-list", OptionList)
            selected = list_widget.highlighted

            if selected is not None:
                recent_files = app.config.get_recent_files()
                if 0 <= selected < len(recent_files):
                    file_path = Path(recent_files[selected])
                    if file_path.exists():
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
                        except Exception as e:
                            app.show_message(f"Error loading file: {e}")
                    else:
                        app.show_message(f"File not found: {file_path}")
                        # Remove from recent files
                        app.config.add_recent_file(
                            str(file_path)
                        )  # This will remove it
            self.app.pop_screen()
        except Exception:
            pass
