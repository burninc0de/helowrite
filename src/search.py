"""Search state and matching helpers for HeloWrite."""

from bisect import bisect_right
from dataclasses import dataclass, field

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
