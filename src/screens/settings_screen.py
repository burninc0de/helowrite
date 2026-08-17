"""Settings screen for adjusting editor settings."""

import os
from typing import Any, cast

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Checkbox,
    Input,
    Static,
    TabbedContent,
    TabPane,
)


class SettingsScreen(ModalScreen):
    """Screen for adjusting editor settings - TUI native design."""

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
    }

    #settings-frame {
        width: 80;
        height: 85%;
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
        width: 28;
        color: $text;
    }

    .setting-value {
        color: $primary;
    }

    .setting-input {
        width: 14;
        height: 1;
    }

    .setting-input-wide {
        width: 50;
        height: 1;
    }

    .smart-quote-label {
        width: 13;
        color: $text;
    }

    .smart-quote-close-label {
        margin-left: 2;
        margin-right:1;

    }

    .smart-quote-input {
        width: 7;
        height: 1;
    }

    #settings-footer {
        text-align: center;
        color: $text-muted;
        text-style: dim;
        margin-top: 1;
    }

    SettingsScreen TabbedContent {
        height: 1fr;
    }

    SettingsScreen TabbedContent ContentSwitcher {
        height: 1fr;
    }

    SettingsScreen TabPane {
        height: 1fr;
        overflow-y: auto;
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

    SettingsScreen Checkbox:disabled {
        color: #555555;
    }

    SettingsScreen Checkbox:disabled .checkbox--label {
        color: #555555;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-frame"):
            yield Static(" Settings ", id="settings-title")
            with TabbedContent():
                with TabPane("Editor"):
                    with Vertical():
                        with Horizontal(classes="setting-row"):
                            yield Static("Editor width:", classes="setting-label")
                            yield Input(id="width-input", classes="setting-input")
                            yield Static(" %", classes="setting-value")
                        with Horizontal(classes="setting-row"):
                            yield Static("Cursor color:", classes="setting-label")
                            yield Input(
                                id="cursor-color-input", classes="setting-input"
                            )
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(
                                " Show scrollbar", id="show-scrollbar-checkbox"
                            )
                        with Horizontal(classes="setting-row"):
                            yield Static("Indent width:", classes="setting-label")
                            yield Input(
                                id="indent-width-input", classes="setting-input"
                            )
                            yield Static(" spaces", classes="setting-value")
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(
                                "Space between paragraphs",
                                id="space-between-paragraphs-checkbox",
                            )
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(
                                "Typewriter Mode sounds",
                                id="typewriter-sounds-checkbox",
                            )
                with TabPane("Content"):
                    with Vertical():
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(
                                " Show word count in distraction-free mode",
                                id="show-word-count-checkbox",
                            )
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(
                                " Enable snippet coloring",
                                id="snippet-coloring-checkbox",
                            )
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(
                                " Enable markdown coloring",
                                id="markdown-coloring-checkbox",
                            )
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(
                                " Markdown auto-pair",
                                id="auto-pair-checkbox",
                            )
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(
                                " Typographic quotes",
                                id="smart-quotes-checkbox",
                            )
                        with Horizontal(
                            classes="setting-row", id="smart-quote-row-single"
                        ):
                            yield Static("Open single:", classes="smart-quote-label")
                            yield Input(
                                id="smart-quote-open-single-input",
                                classes="smart-quote-input",
                            )
                            yield Static(
                                "Close single:",
                                classes="smart-quote-label smart-quote-close-label",
                            )
                            yield Input(
                                id="smart-quote-close-single-input",
                                classes="smart-quote-input",
                            )
                        with Horizontal(
                            classes="setting-row", id="smart-quote-row-double"
                        ):
                            yield Static("Open double:", classes="smart-quote-label")
                            yield Input(
                                id="smart-quote-open-double-input",
                                classes="smart-quote-input",
                            )
                            yield Static(
                                "Close double:",
                                classes="smart-quote-label smart-quote-close-label",
                            )
                            yield Input(
                                id="smart-quote-close-double-input",
                                classes="smart-quote-input",
                            )
                with TabPane("Behavior"):
                    with Vertical():
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(
                                " Open last file on startup",
                                id="open-last-file-checkbox",
                            )
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(" Enable auto-save", id="auto-save-checkbox")
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(
                                " Enable hot reload", id="hot-reload-checkbox"
                            )
                        with Horizontal(classes="setting-row"):
                            yield Static("Auto-save interval:", classes="setting-label")
                            yield Input(
                                id="auto-save-interval-input", classes="setting-input"
                            )
                            yield Static(" min (1, 5, 10)", classes="setting-value")
                with TabPane("Files"):
                    with Vertical():
                        with Horizontal(classes="setting-row"):
                            yield Static("Working directory:", classes="setting-label")
                            yield Input(
                                id="working-dir-input", classes="setting-input-wide"
                            )
                        with Horizontal(classes="setting-row"):
                            yield Static("Obsidian vault:", classes="setting-label")
                            yield Input(
                                id="vault-path-input", classes="setting-input-wide"
                            )
                        with Horizontal(classes="setting-row"):
                            yield Checkbox(
                                " Git pull vault on load",
                                id="git-pull-on-load-checkbox",
                            )
            yield Static(
                "Enter: save | Space: toggle | Tab: navigate | ESC: cancel",
                id="settings-footer",
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
            "#snippet-coloring-checkbox", Checkbox
        ).value = app.config.get_snippet_highlighting_enabled()
        self.query_one(
            "#markdown-coloring-checkbox", Checkbox
        ).value = app.config.get_markdown_highlighting_enabled()
        self.query_one(
            "#auto-pair-checkbox", Checkbox
        ).value = app.config.get_auto_pair_enabled()
        self.query_one(
            "#smart-quotes-checkbox", Checkbox
        ).value = app.config.get_smart_quotes()
        self.query_one(
            "#smart-quote-open-single-input", Input
        ).value = app.config.get_smart_quote_open_single()
        self.query_one(
            "#smart-quote-close-single-input", Input
        ).value = app.config.get_smart_quote_close_single()
        self.query_one(
            "#smart-quote-open-double-input", Input
        ).value = app.config.get_smart_quote_open_double()
        self.query_one(
            "#smart-quote-close-double-input", Input
        ).value = app.config.get_smart_quote_close_double()
        self.query_one(
            "#auto-save-checkbox", Checkbox
        ).value = app.config.get_auto_save_enabled()
        self.query_one(
            "#hot-reload-checkbox", Checkbox
        ).value = app.config.get_hot_reload_enabled()
        self.query_one(
            "#show-scrollbar-checkbox", Checkbox
        ).value = app.config.get_scrollbar_enabled()
        self.query_one("#width-input", Input).value = str(app.editor_width)
        self.query_one("#indent-width-input", Input).value = str(
            app.config.get_indent_width()
        )
        self.query_one(
            "#space-between-paragraphs-checkbox", Checkbox
        ).value = app.config.get_space_between_paragraphs()
        typewriter_sounds_box = self.query_one("#typewriter-sounds-checkbox", Checkbox)
        typewriter_sounds_box.value = app.config.get_typewriter_sounds()
        typewriter_sounds_box.disabled = not app.typewriter_mode
        self.query_one("#cursor-color-input", Input).value = app.cursor_color
        self.query_one(
            "#vault-path-input", Input
        ).value = app.config.get_obsidian_vault_path()
        self.query_one(
            "#git-pull-on-load-checkbox", Checkbox
        ).value = app.config.get_obsidian_git_pull_on_load()
        self.query_one("#auto-save-interval-input", Input).value = str(
            app.config.get_auto_save_interval()
        )
        self.query_one(
            "#working-dir-input", Input
        ).value = app.config.get_default_working_directory()

        self._set_smart_quote_rows_visible(
            self.query_one("#smart-quotes-checkbox", Checkbox).value
        )

    def on_key(self, event):
        """Handle key presses."""
        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "enter":
            self.save_settings()

    def _set_smart_quote_rows_visible(self, visible: bool) -> None:
        self.query_one("#smart-quote-row-single", Horizontal).display = visible
        self.query_one("#smart-quote-row-double", Horizontal).display = visible

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "smart-quotes-checkbox":
            self._set_smart_quote_rows_visible(event.value)

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
            hot_reload_enabled = self.query_one("#hot-reload-checkbox", Checkbox).value
            width_str = self.query_one("#width-input", Input).value.strip()
            indent_width_str = self.query_one(
                "#indent-width-input", Input
            ).value.strip()
            space_between_paragraphs = self.query_one(
                "#space-between-paragraphs-checkbox", Checkbox
            ).value
            cursor_color = self.query_one("#cursor-color-input", Input).value.strip()
            vault_path = self.query_one("#vault-path-input", Input).value.strip()
            git_pull_on_load = self.query_one(
                "#git-pull-on-load-checkbox", Checkbox
            ).value
            auto_save_interval_str = self.query_one(
                "#auto-save-interval-input", Input
            ).value.strip()
            scrollbar_enabled = self.query_one(
                "#show-scrollbar-checkbox", Checkbox
            ).value
            working_dir = self.query_one("#working-dir-input", Input).value.strip()
            typewriter_sounds = self.query_one(
                "#typewriter-sounds-checkbox", Checkbox
            ).value
            smart_quote_open_single = self.query_one(
                "#smart-quote-open-single-input", Input
            ).value
            smart_quote_close_single = self.query_one(
                "#smart-quote-close-single-input", Input
            ).value
            smart_quote_open_double = self.query_one(
                "#smart-quote-open-double-input", Input
            ).value
            smart_quote_close_double = self.query_one(
                "#smart-quote-close-double-input", Input
            ).value

            # Parse values
            width = int(width_str) if width_str else app.editor_width
            indent_width = int(indent_width_str) if indent_width_str else 4
            auto_save_interval = (
                int(auto_save_interval_str) if auto_save_interval_str else 5
            )

            # Validate ranges
            if not (10 <= width <= 90):
                app.show_message("Width must be between 10-90%")
                return
            if not (1 <= indent_width <= 16):
                app.show_message("Indent width must be between 1-16")
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

            # Validate working directory if provided
            if working_dir and not (
                os.path.exists(working_dir) and os.path.isdir(working_dir)
            ):
                app.show_message("Working directory must be an existing directory")
                return

            smart_quote_open_single = smart_quote_open_single.strip() or "\u2018"
            smart_quote_close_single = smart_quote_close_single.strip() or "\u2019"
            smart_quote_open_double = smart_quote_open_double.strip() or "\u201c"
            smart_quote_close_double = smart_quote_close_double.strip() or "\u201d"

            if any(
                len(value) != 1
                for value in (
                    smart_quote_open_single,
                    smart_quote_close_single,
                    smart_quote_open_double,
                    smart_quote_close_double,
                )
            ):
                app.show_message("Each smart quote replacement must be exactly 1 char")
                return

            # Save to config
            app.config.set_open_last_file(open_last_file)
            app.config.set_show_word_count_distraction_free(show_word_count)
            app.config.set_snippet_highlighting_enabled(
                self.query_one("#snippet-coloring-checkbox", Checkbox).value
            )
            app.config.set_markdown_highlighting_enabled(
                self.query_one("#markdown-coloring-checkbox", Checkbox).value
            )
            app.config.set_auto_pair_enabled(
                self.query_one("#auto-pair-checkbox", Checkbox).value
            )
            app.config.set_smart_quotes(
                self.query_one("#smart-quotes-checkbox", Checkbox).value
            )
            app.config.set_auto_save_enabled(auto_save_enabled)
            app.config.set_hot_reload_enabled(hot_reload_enabled)
            app.config.set_editor_width(width)
            app.config.set_indent_width(indent_width)
            app.config.set_space_between_paragraphs(space_between_paragraphs)
            app.config.set_cursor_color(cursor_color)
            app.config.set_obsidian_vault_path(vault_path)
            app.config.set_obsidian_git_pull_on_load(git_pull_on_load)
            app.config.set_auto_save_interval(auto_save_interval)
            app.config.set_scrollbar_enabled(scrollbar_enabled)
            app.config.set_default_working_directory(working_dir)
            app.config.set_typewriter_sounds(typewriter_sounds)
            app.config.set_smart_quote_open_single(smart_quote_open_single)
            app.config.set_smart_quote_close_single(smart_quote_close_single)
            app.config.set_smart_quote_open_double(smart_quote_open_double)
            app.config.set_smart_quote_close_double(smart_quote_close_double)

            # Update app settings
            app.editor_width = width
            app.indent_width = indent_width
            app.space_between_paragraphs = space_between_paragraphs
            app.cursor_color = cursor_color
            app.snippet_highlighting_enabled = self.query_one(
                "#snippet-coloring-checkbox", Checkbox
            ).value
            app.markdown_highlighting_enabled = self.query_one(
                "#markdown-coloring-checkbox", Checkbox
            ).value
            app.auto_pair_enabled = self.query_one(
                "#auto-pair-checkbox", Checkbox
            ).value
            app.smart_quotes = self.query_one("#smart-quotes-checkbox", Checkbox).value
            app.smart_quote_open_single = smart_quote_open_single
            app.smart_quote_close_single = smart_quote_close_single
            app.smart_quote_open_double = smart_quote_open_double
            app.smart_quote_close_double = smart_quote_close_double

            # Apply auto-save
            app.auto_save_enabled = auto_save_enabled
            app.auto_save_interval = auto_save_interval
            if auto_save_enabled:
                app.start_auto_save()
            else:
                app.stop_auto_save()

            app.hot_reload_enabled = hot_reload_enabled
            app._update_file_watcher()

            # Update scrollbar setting
            app.scrollbar_enabled = scrollbar_enabled

            # Update typewriter sounds setting
            app.typewriter_sounds = typewriter_sounds

            # Apply settings
            app.apply_editor_settings()
            app.apply_cursor_color()

            app.show_message("Settings saved!")
            self.app.pop_screen()

        except ValueError:
            app.show_message("Please enter valid numbers")
