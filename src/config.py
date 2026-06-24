"""Configuration management for HeloWrite."""

import os
from pathlib import Path
from typing import Optional, Union


class Config:
    """Configuration management for HeloWrite.

    The config directory defaults to ``~/.config/helowrite`` but can be
    overridden via the ``HELOWWRITE_CONFIG_DIR`` environment variable or by
    passing a custom path. This makes the class simpler to test.
    """

    def __init__(self, config_dir: Optional[Union[Path, str]] = None):
        custom_dir = config_dir or os.environ.get("HELOWWRITE_CONFIG_DIR")
        if custom_dir:
            self.config_dir = Path(custom_dir)
        else:
            self.config_dir = Path.home() / ".config" / "helowrite"
        self.config_file = self.config_dir / "config.conf"
        self.keybindings_file = self.config_dir / "keybindings.conf"
        self.snippets_file = self.config_dir / "snippets.conf"
        self.config_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _read_text_with_fallback(path: Path) -> str:
        """Read text as UTF-8, falling back to cp1252 for legacy files."""
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="cp1252")

    def get_theme(self) -> str:
        """Get the saved theme, defaulting to 'helowrite-dark'."""
        config = self._load_config()
        return config.get("theme", "helowrite-dark")

    def has_theme_preference(self) -> bool:
        """Return whether a theme has been explicitly saved."""
        config = self._load_config()
        return "theme" in config

    def set_theme(self, theme: str):
        """Save the theme to config file."""
        config = self._load_config()
        config["theme"] = theme
        self._save_config(config)

    def get_editor_width(self) -> int:
        """Get editor width percentage, defaulting to 70."""
        config = self._load_config()
        return int(config.get("editor_width", 70))

    def set_editor_width(self, width: int):
        """Save editor width."""
        config = self._load_config()
        config["editor_width"] = str(width)
        self._save_config(config)

    def get_indent_width(self) -> int:
        """Get indent width in spaces, defaulting to 4."""
        config = self._load_config()
        return int(config.get("indent_width", 4))

    def set_indent_width(self, width: int):
        """Save indent width."""
        config = self._load_config()
        config["indent_width"] = str(width)
        self._save_config(config)

    def get_bottom_padding(self) -> int:
        """Get bottom padding, defaulting to 0."""
        config = self._load_config()
        return int(config.get("bottom_padding", 0))

    def set_bottom_padding(self, padding: int):
        """Save bottom padding."""
        config = self._load_config()
        config["bottom_padding"] = str(padding)
        self._save_config(config)

    def get_distraction_top_padding(self) -> int:
        """Get distraction-free top padding, defaulting to 2."""
        config = self._load_config()
        return int(config.get("distraction_top_padding", 2))

    def set_distraction_top_padding(self, padding: int):
        """Save distraction-free top padding."""
        config = self._load_config()
        config["distraction_top_padding"] = str(padding)
        self._save_config(config)

    def get_distraction_free(self) -> bool:
        """Return whether distraction-free mode should be enabled on startup."""
        config = self._load_config()
        return config.get("distraction_free", "0") == "1"

    def set_distraction_free(self, enabled: bool):
        """Persist distraction-free preference."""
        config = self._load_config()
        config["distraction_free"] = "1" if enabled else "0"
        self._save_config(config)

    def get_show_welcome(self) -> bool:
        """Return whether to show the welcome screen."""
        config = self._load_config()
        return config.get("show_welcome", "1") == "1"

    def set_show_welcome(self, show: bool):
        """Persist welcome screen preference."""
        config = self._load_config()
        config["show_welcome"] = "1" if show else "0"
        self._save_config(config)

    def get_show_word_count_distraction_free(self) -> bool:
        """Return whether to show word count in distraction-free mode."""
        config = self._load_config()
        return config.get("show_word_count_distraction_free", "1") == "1"

    def set_show_word_count_distraction_free(self, enabled: bool):
        """Persist word count in distraction-free mode preference."""
        config = self._load_config()
        config["show_word_count_distraction_free"] = "1" if enabled else "0"
        self._save_config(config)

    def get_cursor_color(self) -> str:
        """Get cursor color, defaulting to 'theme' to use theme color."""
        config = self._load_config()
        return config.get("cursor_color", "theme")

    def set_cursor_color(self, color: str):
        """Save cursor color. Use 'theme' to use the theme's primary color."""
        config = self._load_config()
        config["cursor_color"] = color
        self._save_config(config)

    def get_space_between_paragraphs(self) -> bool:
        """Return whether to insert space between paragraphs on Enter."""
        config = self._load_config()
        return config.get("space_between_paragraphs", "1") == "1"

    def set_space_between_paragraphs(self, enabled: bool):
        """Persist space between paragraphs preference."""
        config = self._load_config()
        config["space_between_paragraphs"] = "1" if enabled else "0"
        self._save_config(config)

    def get_smart_quotes(self) -> bool:
        """Return whether to use smart/curly quotes."""
        config = self._load_config()
        return config.get("smart_quotes", "0") == "1"

    def set_smart_quotes(self, enabled: bool):
        """Persist smart quotes preference."""
        config = self._load_config()
        config["smart_quotes"] = "1" if enabled else "0"
        self._save_config(config)

    def get_smart_quote_open_single(self) -> str:
        """Return opening replacement character for single quote."""
        config = self._load_config()
        return config.get("smart_quote_open_single", "\u2018")

    def set_smart_quote_open_single(self, value: str):
        """Persist opening replacement character for single quote."""
        config = self._load_config()
        config["smart_quote_open_single"] = value
        self._save_config(config)

    def get_smart_quote_close_single(self) -> str:
        """Return closing replacement character for single quote."""
        config = self._load_config()
        return config.get("smart_quote_close_single", "\u2019")

    def set_smart_quote_close_single(self, value: str):
        """Persist closing replacement character for single quote."""
        config = self._load_config()
        config["smart_quote_close_single"] = value
        self._save_config(config)

    def get_smart_quote_open_double(self) -> str:
        """Return opening replacement character for double quote."""
        config = self._load_config()
        return config.get("smart_quote_open_double", "\u201c")

    def set_smart_quote_open_double(self, value: str):
        """Persist opening replacement character for double quote."""
        config = self._load_config()
        config["smart_quote_open_double"] = value
        self._save_config(config)

    def get_smart_quote_close_double(self) -> str:
        """Return closing replacement character for double quote."""
        config = self._load_config()
        return config.get("smart_quote_close_double", "\u201d")

    def set_smart_quote_close_double(self, value: str):
        """Persist closing replacement character for double quote."""
        config = self._load_config()
        config["smart_quote_close_double"] = value
        self._save_config(config)

    def get_open_last_file(self) -> bool:
        """Return whether to open the last file on startup."""
        config = self._load_config()
        return config.get("open_last_file", "0") == "1"

    def set_open_last_file(self, enabled: bool):
        """Persist open last file preference."""
        config = self._load_config()
        config["open_last_file"] = "1" if enabled else "0"
        self._save_config(config)

    def get_last_file_path(self) -> str:
        """Get the last opened file path."""
        config = self._load_config()
        return config.get("last_file_path", "")

    def set_last_file_path(self, path: str):
        """Save the last opened file path."""
        config = self._load_config()
        config["last_file_path"] = path
        self._save_config(config)

    def get_last_cursor_position(self) -> tuple[int, int]:
        """Get the last cursor position as (line, column)."""
        config = self._load_config()
        pos_str = config.get("last_cursor_position", "0,0")
        try:
            line, col = map(int, pos_str.split(","))
            return (line, col)
        except ValueError:
            return (0, 0)

    def set_last_cursor_position(self, position: tuple[int, int]):
        """Save the last cursor position."""
        config = self._load_config()
        config["last_cursor_position"] = f"{position[0]},{position[1]}"
        self._save_config(config)

    def get_recent_files(self) -> list[str]:
        """Get list of recent files (up to 5)."""
        config = self._load_config()
        recent = config.get("recent_files", "")
        if recent:
            return [f for f in recent.split("|") if f]
        return []

    def add_recent_file(self, path: str):
        """Add a file to recent files list (max 5, no duplicates)."""
        config = self._load_config()
        recent = self.get_recent_files()

        # Remove if already exists (to move to front)
        if path in recent:
            recent.remove(path)

        # Add to front
        recent.insert(0, path)

        # Keep only last 5
        recent = recent[:5]

        # Save
        config["recent_files"] = "|".join(recent)
        self._save_config(config)

    def get_obsidian_vault_path(self) -> str:
        """Get the Obsidian vault path."""
        config = self._load_config()
        return config.get("obsidian_vault_path", "")

    def set_obsidian_vault_path(self, path: str):
        """Save the Obsidian vault path. Path must exist and be a directory."""
        if path and not (os.path.exists(path) and os.path.isdir(path)):
            raise ValueError("Vault path must be an existing directory")

        config = self._load_config()
        config["obsidian_vault_path"] = path
        self._save_config(config)

    def get_obsidian_git_pull_on_load(self) -> bool:
        """Return whether to git pull on load when vault is configured."""
        config = self._load_config()
        return config.get("obsidian_git_pull_on_load", "0") == "1"

    def set_obsidian_git_pull_on_load(self, enabled: bool):
        """Persist git pull on load preference."""
        config = self._load_config()
        config["obsidian_git_pull_on_load"] = "1" if enabled else "0"
        self._save_config(config)

    def get_auto_save_enabled(self) -> bool:
        """Return whether auto-save is enabled."""
        config = self._load_config()
        return config.get("auto_save_enabled", "0") == "1"

    def set_auto_save_enabled(self, enabled: bool):
        """Persist auto-save enabled preference."""
        config = self._load_config()
        config["auto_save_enabled"] = "1" if enabled else "0"
        self._save_config(config)

    def get_auto_save_interval(self) -> int:
        """Get auto-save interval in minutes, defaulting to 5."""
        config = self._load_config()
        return int(config.get("auto_save_interval", 5))

    def set_auto_save_interval(self, interval: int):
        """Save auto-save interval in minutes."""
        config = self._load_config()
        config["auto_save_interval"] = str(interval)
        self._save_config(config)

    def get_scrollbar_enabled(self) -> bool:
        """Return whether scrollbar is enabled."""
        config = self._load_config()
        return config.get("scrollbar_enabled", "0") == "1"

    def set_scrollbar_enabled(self, enabled: bool):
        """Persist scrollbar enabled preference."""
        config = self._load_config()
        config["scrollbar_enabled"] = "1" if enabled else "0"
        self._save_config(config)

    def get_snippet_highlighting_enabled(self) -> bool:
        """Return whether snippet coloring/highlighting is enabled."""
        config = self._load_config()
        return config.get("snippet_highlighting_enabled", "1") == "1"

    def set_snippet_highlighting_enabled(self, enabled: bool):
        """Persist snippet coloring/highlighting preference."""
        config = self._load_config()
        config["snippet_highlighting_enabled"] = "1" if enabled else "0"
        self._save_config(config)

    def get_markdown_highlighting_enabled(self) -> bool:
        """Return whether lightweight markdown accent highlighting is enabled."""
        config = self._load_config()
        return config.get("markdown_highlighting_enabled", "1") == "1"

    def set_markdown_highlighting_enabled(self, enabled: bool):
        """Persist markdown accent highlighting preference."""
        config = self._load_config()
        config["markdown_highlighting_enabled"] = "1" if enabled else "0"
        self._save_config(config)

    def get_default_working_directory(self) -> str:
        """Get the default working directory, defaulting to empty (current dir)."""
        config = self._load_config()
        return config.get("default_working_directory", "")

    def set_default_working_directory(self, path: str):
        """Save the default working directory. Path must exist and be a directory."""
        if path and not (os.path.exists(path) and os.path.isdir(path)):
            raise ValueError("Working directory must be an existing directory")

        config = self._load_config()
        config["default_working_directory"] = path
        self._save_config(config)

    def get_typewriter_mode(self) -> bool:
        """Return whether typewriter mode is enabled."""
        config = self._load_config()
        return config.get("typewriter_mode", "0") == "1"

    def set_typewriter_mode(self, enabled: bool):
        """Persist typewriter mode preference."""
        config = self._load_config()
        config["typewriter_mode"] = "1" if enabled else "0"
        self._save_config(config)

    def get_typewriter_sounds(self) -> bool:
        """Return whether typewriter sounds are enabled."""
        config = self._load_config()
        return config.get("typewriter_sounds", "0") == "1"

    def set_typewriter_sounds(self, enabled: bool):
        """Persist typewriter sounds preference."""
        config = self._load_config()
        config["typewriter_sounds"] = "1" if enabled else "0"
        self._save_config(config)

    def get_keybindings(self) -> dict[str, str]:
        """Load keybindings from the user keybindings file."""
        if not self.keybindings_file.exists():
            return {}

        try:
            content = self._read_text_with_fallback(self.keybindings_file)
            keybindings: dict[str, str] = {}
            for line in content.strip().split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                action, key = line.split("=", 1)
                action = action.strip()
                key = key.strip()
                if action and key:
                    keybindings[action] = key
            return keybindings
        except Exception:
            return {}

    def save_default_keybindings(self, keybindings: dict[str, str]) -> None:
        """Write the default keybindings file if it does not already exist."""
        if self.keybindings_file.exists():
            return

        try:
            lines = [
                "# HeloWrite keybindings",
                "# Edit this file to customize hotkeys.",
                "# Format: action=key",
                "# Example: save=ctrl+s",
                "",
            ]
            lines.extend(f"{action}={key}" for action, key in keybindings.items())
            self.keybindings_file.write_text("\n".join(lines), encoding="utf-8")
        except Exception:
            pass

    def get_snippets(self) -> dict[str, str]:
        """Load snippets from file."""
        if not self.snippets_file.exists():
            return {}

        try:
            content = self.snippets_file.read_text(encoding="utf-8")
            snippets: dict[str, str] = {}
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key:
                    snippets[key] = value
            return snippets
        except Exception:
            return {}

    def save_snippets(self, snippets: dict[str, str]) -> None:
        """Persist snippets to file."""
        try:
            lines = [
                "# HeloWrite snippets",
                "# Format: trigger=replacement",
                "# Placeholders: %CURRENTTIME, %DATE, %DATETIME, %CLIPBOARD, %CLIPBOARD_TRIMMED",
                "# Use %% for a literal percent sign",
                "# Escape sequences: \\n (newline), \\t (tab), \\\\n (literal backslash+n)",
                "",
            ]
            for trigger, replacement in sorted(snippets.items()):
                lines.append(f"{trigger}={replacement}")
            self.snippets_file.write_text("\n".join(lines), encoding="utf-8")
        except Exception:
            pass

    def _load_config(self) -> dict[str, str]:
        """Load config from file."""
        if self.config_file.exists():
            try:
                content = self._read_text_with_fallback(self.config_file)
                config = {}
                for line in content.strip().split("\n"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
                return config
            except Exception:
                return {}
        return {}

    def _save_config(self, config: dict):
        """Save config to file."""
        try:
            content = "\n".join(f"{key}={value}" for key, value in config.items())
            self.config_file.write_text(content, encoding="utf-8")
        except Exception:
            pass
