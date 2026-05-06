"""Snippet auto-replacement engine for HeloWrite."""

import datetime
import re
import unicodedata
from pathlib import Path


PLACEHOLDER_PATTERN = re.compile(r"%[A-Z_]+")


def expand_placeholders(text: str) -> str:
    """Expand placeholders and escape sequences in snippet replacement text.

    Supported placeholders:
    - %CURRENTTIME: Current time (HH:MM)
    - %%: Literal % character

    Supported escape sequences:
    - \\n: Newline
    - \\t: Tab
    - \\\\n: Literal backslash+n
    """
    text = text.replace("\\\\", "\x00BS\x00")
    text = text.replace("\\n", "\n")
    text = text.replace("\\t", "\t")
    text = text.replace("\x00BS\x00", "\\")

    text = text.replace("%%", "\x00PERCENT\x00")

    def replace_placeholder(match: re.Match) -> str:
        name = match.group(0)[1:]

        if name == "CURRENTTIME":
            return datetime.datetime.now().strftime("%H:%M")
        return match.group(0)

    result = PLACEHOLDER_PATTERN.sub(replace_placeholder, text)
    result = result.replace("\x00PERCENT\x00", "%")
    return result


def _is_word_char(char: str) -> bool:
    """Check if a character is considered part of a word."""
    if not char:
        return False
    category = unicodedata.category(char)
    return category in ("Ll", "Lv", "Lm", "Lo", "Lt", "Lu", "Nd")


def find_trigger(
    text_before_cursor: str, triggers: list[str]
) -> tuple[Optional[str], int, int]:
    """Find a matching trigger in text before cursor.

    Args:
        text_before_cursor: Text from the start up to (but not including) the cursor.
        triggers: List of trigger strings to match.

    Returns:
        Tuple of (trigger, start_pos, end_pos) if found, or (None, -1, -1) if not found.
        The trigger must be preceded by a non-word character or be at position 0.
    """
    if not text_before_cursor or not triggers:
        return None, -1, -1

    for trigger in sorted(triggers, key=len, reverse=True):
        if not trigger:
            continue
        text_len = len(text_before_cursor)
        trigger_len = len(trigger)
        for pos in range(text_len - trigger_len + 1):
            if text_before_cursor[pos : pos + trigger_len] != trigger:
                continue
            if pos == 0:
                return trigger, 0, trigger_len
            char_before = text_before_cursor[pos - 1]
            if not _is_word_char(char_before):
                return trigger, pos, pos + trigger_len

    return None, -1, -1


class SnippetEngine:
    """Manages snippet auto-replacement."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.snippets_file: Optional[Path] = None
        self._snippets: dict[str, str] = {}
        if config_dir:
            self.snippets_file = config_dir / "snippets.conf"
            self._load_snippets()

    def _load_snippets(self) -> None:
        """Load snippets from file."""
        self._snippets.clear()
        if not self.snippets_file or not self.snippets_file.exists():
            return

        try:
            content = self.snippets_file.read_text(encoding="utf-8")
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
                    self._snippets[key] = value
        except Exception:
            pass

    def save_snippets(self) -> None:
        """Persist snippets to file."""
        if not self.snippets_file:
            return
        try:
            self.snippets_file.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                "# HeloWrite snippets",
                "# Format: trigger=replacement",
                "# Placeholders: %CURRENTTIME, %DATE, %DATETIME, %CLIPBOARD, %CLIPBOARD_TRIMMED",
                "# Use %% for a literal percent sign",
                "",
            ]
            for trigger, replacement in sorted(self._snippets.items()):
                lines.append(f"{trigger}={replacement}")
            self.snippets_file.write_text("\n".join(lines), encoding="utf-8")
        except Exception:
            pass

    def get_snippets(self) -> dict[str, str]:
        """Return a copy of loaded snippets."""
        return dict(self._snippets)

    def set_snippets(self, snippets: dict[str, str]) -> None:
        """Replace all snippets."""
        self._snippets = dict(snippets)

    def add_snippet(self, trigger: str, replacement: str) -> bool:
        """Add or update a snippet. Returns False if trigger is invalid."""
        trigger = trigger.strip()
        if not trigger or "=" in trigger or "\n" in trigger:
            return False
        self._snippets[trigger] = replacement
        return True

    def remove_snippet(self, trigger: str) -> bool:
        """Remove a snippet by trigger. Returns True if found and removed."""
        if trigger in self._snippets:
            del self._snippets[trigger]
            return True
        return False

    def try_expand(
        self, text_before_cursor: str
    ) -> tuple[bool, Optional[str], int, int]:
        """Check for and expand a snippet trigger.

        Args:
            text_before_cursor: Text from start up to cursor position.

        Returns:
            Tuple of (expanded, replacement_text, start_pos, end_pos).
            expanded is True if a replacement was made.
        """
        triggers = list(self._snippets.keys())
        trigger, start_pos, end_pos = find_trigger(text_before_cursor, triggers)

        if trigger is None:
            return False, None, -1, -1

        raw_replacement = self._snippets[trigger]
        replacement = expand_placeholders(raw_replacement)
        return True, replacement, start_pos, end_pos
