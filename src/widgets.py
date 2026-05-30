"""Custom widgets for HeloWrite."""

import datetime
import os
import re
from pathlib import Path
from typing import Any, List, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.geometry import Size
from textual.widgets import DirectoryTree, Input, Static, TextArea

from snippets import PLACEHOLDER_PATTERN
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


class FindBar(Horizontal):
    """Top search bar for in-buffer find navigation."""

    DEFAULT_CSS = """
    FindBar {
        height: 1;
        padding: 0 1;
        background: $primary-darken-2;
        color: $text;
        display: none;
    }

    FindBar.visible {
        display: block;
    }

    #find-text {
        width: auto;
        color: $text;
    }

    #find-input {
        width: 0;
        min-width: 0;
        height: 1;
        border: none;
        background: transparent;
        color: transparent;
        padding: 0;
    }

    #find-meta {
        width: auto;
        padding-left: 1;
        color: $text-muted;
    }

    #find-arrows {
        width: auto;
        padding-left: 1;
        color: $primary;
        text-style: bold;
    }

    #find-spacer {
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Find:", id="find-text")
        yield Input(placeholder="Type to search...", id="find-input")
        yield Static("0 matches", id="find-meta")
        yield Static("", id="find-spacer")
        yield Static("ESC ↑ ↓", id="find-arrows")

    def set_query(self, query: str) -> None:
        """Render the query visibly in the top bar."""
        label = self.query_one("#find-text", Static)
        if query:
            label.update(f'Find: "{query}"')
        else:
            label.update("Find:")

    def set_match_count(self, count: int, current_index: int = -1) -> None:
        """Update the match counter in the find bar."""
        meta = self.query_one("#find-meta", Static)
        if count <= 0:
            meta.update("0 matches")
            return
        if 0 <= current_index < count:
            meta.update(f"{current_index + 1}/{count}")
            return
        meta.update(f"{count} matches")


class HeloWriteTextArea(TextArea):
    """Custom TextArea with additional commands and paragraph spacing."""

    BINDINGS = [
        binding
        for binding in TextArea.BINDINGS
        if getattr(binding, "key", "") != "ctrl+f"
    ]

    MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6}\s+.+)$")
    MARKDOWN_BLOCKQUOTE_RE = re.compile(r"^\s{0,3}(>\s?.+)$")
    MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^\)]+\)")
    MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\([^\)]+\)")
    MARKDOWN_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(?!\s).+?(?<!\s)(?<!\*)\*(?!\*)")
    MARKDOWN_BOLD_RE = re.compile(r"\*\*(?!\s).+?(?<!\s)\*\*")
    MARKDOWN_CODE_RE = re.compile(r"(`+)(.*?)\1")
    MARKDOWN_CODEBLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)

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

    .text-area--selection {
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
        self._typewriter_skip_scroll_visible_once = False
        self._last_typewriter_center_state = None
        self._typewriter_recently_preserved = False
        self._snippet_pattern_cache_key: tuple[str, ...] = ()
        self._snippet_pattern_cache: list[re.Pattern[str]] = []
        self._typewriter_debug_enabled = bool(
            os.environ.get("HELOWRITE_TYPEWRITER_DEBUG", "")
        )
        super().__init__(**kwargs)
        self.language = None

    def _is_opening_quote_position(self) -> bool:
        """Return True if cursor is at a position where an opening quote should be used."""
        cursor = self.cursor_location
        if cursor is None:
            return True
        row, col = cursor
        if col == 0:
            return True
        text_before = self.get_text_range((row, 0), (row, col))
        if not text_before:
            return True
        return text_before[-1] in " \t\n\r([{'\""

    def _insert_smart_quote(self, plain_quote: str) -> None:
        """Insert curly quote based on cursor context."""
        app = self.app
        open_single = getattr(app, "smart_quote_open_single", "\u2018")
        close_single = getattr(app, "smart_quote_close_single", "\u2019")
        open_double = getattr(app, "smart_quote_open_double", "\u201c")
        close_double = getattr(app, "smart_quote_close_double", "\u201d")
        if self._is_opening_quote_position():
            if plain_quote == '"':
                self.insert(open_double)
            else:
                self.insert(open_single)
        else:
            if plain_quote == '"':
                self.insert(close_double)
            else:
                self.insert(close_single)

    def _build_snippet_highlights(self) -> None:
        app = getattr(self, "app", None) or getattr(self, "_app", None)
        snippets: Any = getattr(app, "_snippets", None)
        if hasattr(snippets, "get_snippets"):
            snippets = snippets.get_snippets()
        if not isinstance(snippets, dict) or not snippets:
            return

        patterns = self._get_snippet_highlight_patterns(snippets)
        if not patterns:
            return

        for line_number, line in enumerate(self.text.splitlines()):
            for pattern in patterns:
                for match in pattern.finditer(line):
                    start = self._char_to_utf8_byte_index(line, match.start())
                    end = self._char_to_utf8_byte_index(line, match.end())
                    self._highlights[line_number].append((start, end, "snippet"))

    def _get_snippet_highlight_patterns(
        self, snippets: dict[str, str]
    ) -> list[re.Pattern[str]]:
        """Return cached compiled snippet highlight regexes for the current snippets."""
        replacement_values = tuple(
            sorted(
                (value for value in snippets.values() if value), key=len, reverse=True
            )
        )
        if replacement_values == self._snippet_pattern_cache_key:
            return self._snippet_pattern_cache

        patterns: list[re.Pattern[str]] = []
        for replacement in replacement_values:
            pattern = self._build_snippet_highlight_pattern(replacement)
            if pattern:
                patterns.append(re.compile(pattern))

        self._snippet_pattern_cache_key = replacement_values
        self._snippet_pattern_cache = patterns
        return patterns

    def _char_to_utf8_byte_index(self, line: str, index: int) -> int:
        """Convert a character offset into a UTF-8 byte offset for Textual highlights."""
        return len(line[: max(0, index)].encode("utf-8"))

    def _build_snippet_highlight_pattern(self, replacement: str) -> Optional[str]:
        """Build a regex that matches the expanded snippet text."""
        if not replacement:
            return None

        parts: List[str] = []
        index = 0
        while index < len(replacement):
            if replacement.startswith("\\\\", index):
                parts.append(re.escape("\\"))
                index += 2
                continue
            if replacement.startswith("\\n", index):
                parts.append(re.escape("\n"))
                index += 2
                continue
            if replacement.startswith("\\t", index):
                parts.append(re.escape("\t"))
                index += 2
                continue
            if replacement.startswith("%%", index):
                parts.append("%")
                index += 2
                continue

            placeholder = PLACEHOLDER_PATTERN.match(replacement, index)
            if placeholder:
                parts.append(self._placeholder_regex(placeholder.group(0)))
                index = placeholder.end()
                continue

            parts.append(re.escape(replacement[index]))
            index += 1

        pattern = "".join(parts)
        if re.fullmatch(r"[A-Za-z0-9_ ]+", replacement):
            return rf"(?<!\w){pattern}(?!\w)"
        return pattern

    def _placeholder_regex(self, placeholder: str) -> str:
        if placeholder == "%CURRENTTIME":
            return r"\d{2}:\d{2}"
        return re.escape(placeholder)

    def _build_highlight_map(self) -> None:
        super()._build_highlight_map()
        if getattr(self.app, "snippet_highlighting_enabled", True):
            self._build_snippet_highlights()
        if getattr(self.app, "markdown_highlighting_enabled", True):
            self._build_markdown_highlights()
        self._build_search_highlights()

    def refresh_search_highlights(self) -> None:
        """Refresh only search highlight tokens without rebuilding other highlights."""
        search_tokens = {"search_result", "search_result_current"}
        for line_number, highlights in self._highlights.items():
            self._highlights[line_number] = [
                highlight
                for highlight in highlights
                if highlight[2] not in search_tokens
            ]
        self._build_search_highlights()

    def _build_search_highlights(self) -> None:
        app = getattr(self, "app", None) or getattr(self, "_app", None)
        matches = getattr(app, "find_matches", [])
        current_index = getattr(app, "find_active_match_index", -1)
        if not matches:
            return

        lines = self.text.splitlines()

        for index, (line_number, start_col, end_col) in enumerate(matches):
            if line_number < 0 or line_number >= len(lines):
                continue
            line = lines[line_number]
            if start_col < 0 or end_col <= start_col or start_col > len(line):
                continue
            end_col = min(end_col, len(line))
            start = self._char_to_utf8_byte_index(line, start_col)
            end = self._char_to_utf8_byte_index(line, end_col)
            token = (
                "search_result_current" if index == current_index else "search_result"
            )
            self._highlights[line_number].append((start, end, token))

    def _build_markdown_highlights(self) -> None:
        app = getattr(self, "app", None) or getattr(self, "_app", None)
        if getattr(app, "language", "text") != "markdown":
            return

        for line_number, line in enumerate(self.text.splitlines()):
            heading_match = self.MARKDOWN_HEADING_RE.match(line)
            if heading_match:
                start = self._char_to_utf8_byte_index(line, heading_match.start(1))
                end = self._char_to_utf8_byte_index(line, heading_match.end(1))
                self._highlights[line_number].append((start, end, "markdown_heading"))

            quote_match = self.MARKDOWN_BLOCKQUOTE_RE.match(line)
            if quote_match:
                start = self._char_to_utf8_byte_index(line, quote_match.start(1))
                end = self._char_to_utf8_byte_index(line, quote_match.end(1))
                self._highlights[line_number].append(
                    (start, end, "markdown_blockquote")
                )

            for image_match in self.MARKDOWN_IMAGE_RE.finditer(line):
                start = self._char_to_utf8_byte_index(line, image_match.start())
                end = self._char_to_utf8_byte_index(line, image_match.end())
                self._highlights[line_number].append((start, end, "markdown_image"))

            for link_match in self.MARKDOWN_LINK_RE.finditer(line):
                start = self._char_to_utf8_byte_index(line, link_match.start())
                end = self._char_to_utf8_byte_index(line, link_match.end())
                self._highlights[line_number].append((start, end, "markdown_link"))

            for code_match in self.MARKDOWN_CODE_RE.finditer(line):
                start = self._char_to_utf8_byte_index(line, code_match.start())
                end = self._char_to_utf8_byte_index(line, code_match.end())
                self._highlights[line_number].append((start, end, "markdown_code"))

            for bold_match in self.MARKDOWN_BOLD_RE.finditer(line):
                start = self._char_to_utf8_byte_index(line, bold_match.start())
                end = self._char_to_utf8_byte_index(line, bold_match.end())
                self._highlights[line_number].append((start, end, "markdown_bold"))

            for italic_match in self.MARKDOWN_ITALIC_RE.finditer(line):
                start = self._char_to_utf8_byte_index(line, italic_match.start())
                end = self._char_to_utf8_byte_index(line, italic_match.end())
                self._highlights[line_number].append((start, end, "markdown_italic"))

        for match in self.MARKDOWN_CODEBLOCK_RE.finditer(self.text):
            start_offset = match.start()
            end_offset = match.end()
            line_start = self.text[:start_offset].count("\n")
            line_end = self.text[:end_offset].count("\n")
            lines = self.text.splitlines()
            for ln in range(line_start, line_end + 1):
                self._highlights.setdefault(ln, [])
                line_content = lines[ln]
                line_text_start = sum(len(line) + 1 for line in lines[:ln])
                rel_start = start_offset - line_text_start if ln == line_start else 0
                rel_end = (
                    end_offset - line_text_start
                    if ln == line_end
                    else len(line_content)
                )
                start = self._char_to_utf8_byte_index(line_content, max(0, rel_start))
                end = self._char_to_utf8_byte_index(
                    line_content, min(len(line_content), rel_end)
                )
                self._highlights[ln].append((start, end, "markdown_codeblock"))

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
        if self.has_class("typewriter-hidden"):
            self.remove_class("typewriter-hidden")

    def _set_typewriter_hidden(self) -> None:
        if not self.has_class("typewriter-hidden"):
            self.add_class("typewriter-hidden")

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
        if self._typewriter_skip_scroll_visible_once:
            self._typewriter_skip_scroll_visible_once = False
            self._clear_typewriter_hidden()
            return None
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
                    # User likely scrolled manually while cursor stayed on the same
                    # line. Respect that scroll position instead of forcing a recentre.
                    self._last_typewriter_center_state = {
                        "cursor": self.cursor_location,
                        "scroll_y": float(self.scroll_y),
                        "target": float(self.scroll_y),
                        "max_scroll_y": float(self.max_scroll_y),
                        "view_height": int(self.scrollable_content_region.height),
                    }
                    self._typewriter_recently_preserved = False
                    self._write_typewriter_debug("manual_scroll_preserved")
                    self._clear_typewriter_hidden()
                    return None
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
        self._set_typewriter_hidden()
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

    async def _on_key(self, event):
        """Handle key presses, adding paragraph break on Enter."""
        if event.key == "ctrl+f":
            action_find = getattr(self.app, "action_find", None)
            if callable(action_find):
                action_find()
            event.prevent_default()
            event.stop()
            return

        if getattr(self.app, "smart_quotes", False):
            if event.character == '"':
                self._insert_smart_quote('"')
                event.prevent_default()
                event.stop()
                return
            if event.character == "'":
                self._insert_smart_quote("'")
                event.prevent_default()
                event.stop()
                return

        app = getattr(self.app, "_snippets", None)
        if app and (
            event.key in ("space", "tab", "enter")
            or (len(event.key) == 1 and not event.key.isalnum())
        ):
            from snippets import expand_placeholders, find_trigger

            snippets = app
            if hasattr(snippets, "get_snippets"):
                snippets = snippets.get_snippets()

            if not snippets:
                await super()._on_key(event)
                return

            cursor_pos = self.cursor_location
            if cursor_pos is None:
                await super()._on_key(event)
                return

            current_line = cursor_pos[0]
            text_before = self.get_text_range((current_line, 0), cursor_pos)

            app_sorted_triggers = getattr(self.app, "_snippet_triggers_sorted", ())
            triggers = (
                app_sorted_triggers
                if app_sorted_triggers
                else tuple(sorted(snippets.keys(), key=len, reverse=True))
            )
            trigger, start_pos, end_pos = find_trigger(
                text_before,
                triggers,
                presorted=True,
            )

            if trigger is None:
                if event.key != "enter":
                    await super()._on_key(event)
                    return
            else:
                raw = snippets[trigger]
                replacement = expand_placeholders(raw)

                suffix = text_before[end_pos:]
                if suffix and all(
                    not ch.isalnum() and not ch.isspace() for ch in suffix
                ):
                    self.delete(
                        (current_line, start_pos), (current_line, len(text_before))
                    )
                    self.insert(replacement + suffix)
                else:
                    self.delete((current_line, start_pos), (current_line, end_pos))
                    self.insert(replacement)

                if event.key == "space":
                    self.insert(" ")
                elif event.key == "tab":
                    self.insert("\t")
                elif len(event.key) == 1 and not event.key.isalnum():
                    self.insert(event.key)

            if event.key == "enter":
                self.insert("\n\n" if self.app.space_between_paragraphs else "\n")
                if self.app.typewriter_mode:
                    self._set_typewriter_hidden()
                    self._write_typewriter_debug(
                        "snippet_enter" if trigger else "key_enter"
                    )
                    self._schedule_typewriter_center()
                    if self.app.typewriter_sounds:
                        self.app.play_sound("newline")
                else:
                    self.call_after_refresh(self.scroll_cursor_visible)
                event.prevent_default()
                event.stop()
                return

            event.prevent_default()
            event.stop()
            return

        if event.key == "enter":
            self.insert("\n\n" if self.app.space_between_paragraphs else "\n")
            event.prevent_default()
            event.stop()
            if self.app.typewriter_mode:
                self._set_typewriter_hidden()
                self._write_typewriter_debug("key_enter")
                self._schedule_typewriter_center()
                if self.app.typewriter_sounds:
                    self.app.play_sound("newline")
            else:
                self.call_after_refresh(self.scroll_cursor_visible)
            return

        if event.key == "backspace" and self.app.typewriter_mode:
            if self.app.typewriter_sounds:
                self.app.play_sound("ratchet")
            await super()._on_key(event)
            return

        if self.app.typewriter_mode and event.key in ("up", "down"):
            self._set_typewriter_hidden()
            self._write_typewriter_debug(f"hide_key_{event.key}")
            # Cursor-motion keys don't change document layout, so we can avoid
            # an extra call_after_refresh hop and recentre immediately after
            # the key action completes.
            self._typewriter_center_scheduled = True
            await super()._on_key(event)
            self._center_cursor_typewriter()
            self._typewriter_skip_scroll_visible_once = True
            return

        await super()._on_key(event)

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
                content = app.read_text_file(file_path, show_encoding_notice=True)
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
