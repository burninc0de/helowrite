"""Search state and matching helpers for HeloWrite."""

from bisect import bisect_right
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from textual.widgets import Input

from widgets import FindBar, HeloWriteTextArea

if TYPE_CHECKING:
    from app import HeloWrite

SearchMatch = tuple[int, int, int]


@dataclass
class SearchState:
    """Mutable search state for the editor buffer."""

    query: str = ""
    matches: list[SearchMatch] = field(default_factory=list)
    active_match_index: int = -1

    def clear(self) -> None:
        """Clear the current query and all match state."""
        self.query = ""
        self.matches = []
        self.active_match_index = -1

    def apply_query(self, text: str, query: str) -> None:
        """Update state from a search query and editor text."""
        self.query = query
        self.matches = find_matches(text, query)
        self.active_match_index = 0 if self.matches else -1

    def select_next(self) -> int:
        """Select and return the next match index."""
        self.active_match_index = next_match_index(
            self.active_match_index, len(self.matches)
        )
        return self.active_match_index

    def select_previous(self) -> int:
        """Select and return the previous match index."""
        self.active_match_index = previous_match_index(
            self.active_match_index, len(self.matches)
        )
        return self.active_match_index


def find_matches(text: str, query: str) -> list[SearchMatch]:
    """Find all case-insensitive non-overlapping matches in text."""
    if not query:
        return []

    lower_text = text.lower()
    needle = query.lower()
    if not needle:
        return []

    line_starts = [0]
    for index, char in enumerate(text):
        if char == "\n":
            line_starts.append(index + 1)

    matches: list[SearchMatch] = []
    start = 0
    while True:
        pos = lower_text.find(needle, start)
        if pos == -1:
            break

        line = bisect_right(line_starts, pos) - 1
        col = pos - line_starts[line]
        matches.append((line, col, col + len(query)))
        start = pos + max(len(query), 1)

    return matches


def next_match_index(current_index: int, match_count: int) -> int:
    """Return the next active match index, wrapping at the end."""
    if match_count <= 0:
        return -1
    if current_index < 0:
        return 0
    return (current_index + 1) % match_count


def previous_match_index(current_index: int, match_count: int) -> int:
    """Return the previous active match index, wrapping at the beginning."""
    if match_count <= 0:
        return -1
    if current_index < 0:
        return match_count - 1
    return (current_index - 1) % match_count


def run_scheduled_find_refresh(app: "HeloWrite") -> None:
    """Apply the latest find query to current editor text."""
    app._find_refresh_timer = None
    if app.find_query:
        apply_find_query(app, app.find_query)


def schedule_find_refresh(app: "HeloWrite") -> None:
    """Debounce find/highlight recomputation while typing in the editor."""
    if app._find_refresh_timer is not None:
        app._find_refresh_timer.stop()
    app._find_refresh_timer = app.set_timer(
        app._find_refresh_debounce_seconds,
        lambda: run_scheduled_find_refresh(app),
    )


def cancel_find_refresh(app: "HeloWrite") -> None:
    """Stop any pending find refresh timer."""
    if app._find_refresh_timer is not None:
        app._find_refresh_timer.stop()
        app._find_refresh_timer = None


def close_find_bar(app: "HeloWrite", clear_query: bool = True) -> None:
    """Close the find bar and optionally clear search highlights."""
    cancel_find_refresh(app)
    find_bar = app.query_one("#find-bar", FindBar)
    find_bar.remove_class("visible")
    find_input = find_bar.query_one("#find-input", Input)
    find_input.value = ""
    find_bar.set_query("")

    if clear_query:
        app.search_state.clear()
        refresh_find_highlights(app)

    editor = app.query_one("#editor", HeloWriteTextArea)
    editor.focus()


def refresh_find_highlights(app: "HeloWrite") -> None:
    """Rebuild highlights and update find-bar metadata."""
    try:
        editor = app.query_one("#editor", HeloWriteTextArea)
        if hasattr(editor, "refresh_search_highlights"):
            editor.refresh_search_highlights()
        else:
            editor._build_highlight_map()
        editor.refresh()
    except Exception:
        pass

    try:
        find_bar = app.query_one("#find-bar", FindBar)
        find_bar.set_match_count(len(app.find_matches), app.find_active_match_index)
    except Exception:
        pass


def apply_find_query(app: "HeloWrite", query: str) -> None:
    """Compute all matches for the active query and update highlights."""
    editor = app.query_one("#editor", HeloWriteTextArea)
    app.search_state.apply_query(editor.text, query)
    refresh_find_highlights(app)


def jump_to_find_result(app: "HeloWrite", index: int) -> None:
    """Move cursor and scroll to a specific find result."""
    if index < 0 or index >= len(app.find_matches):
        return

    line, col, _ = app.find_matches[index]
    editor = app.query_one("#editor", HeloWriteTextArea)
    editor.cursor_location = (line, col)
    editor.scroll_cursor_visible()
    app.show_message(f"Match {index + 1}/{len(app.find_matches)}")


def handle_find_input(app: "HeloWrite", event: Input.Changed) -> None:
    """Update find matches while typing in the find input."""
    if event.input.id == "find-input":
        find_bar = app.query_one("#find-bar", FindBar)
        find_bar.set_query(event.value)
        apply_find_query(app, event.value)


def handle_find_key(app: "HeloWrite", event) -> None:
    """Handle find-bar key controls while focus is in the find input."""
    try:
        focused = app.screen.focused
    except Exception:
        focused = None

    if isinstance(focused, Input) and focused.id == "find-input":
        if getattr(event, "key", None) == "escape":
            event.prevent_default()
            event.stop()
            close_find_bar(app, clear_query=True)
            return
        if getattr(event, "key", None) == "down":
            event.prevent_default()
            event.stop()
            app.action_find_next()
            return
        if getattr(event, "key", None) == "up":
            event.prevent_default()
            event.stop()
            app.action_find_previous()
            return
        if getattr(event, "key", None) in ("enter", "return"):
            event.prevent_default()
            event.stop()
            app.action_find_next()
            close_find_bar(app, clear_query=True)
            return
