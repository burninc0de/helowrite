"""Tests for editor search state."""

from search import (
    SearchState,
    find_matches,
    next_match_index,
    previous_match_index,
)


def test_find_matches_is_case_insensitive_and_tracks_lines() -> None:
    """Search should return line and column positions for all matches."""
    matches = find_matches("Alpha\nbeta alpha\nALPHA", "alpha")

    assert matches == [(0, 0, 5), (1, 5, 10), (2, 0, 5)]


def test_find_matches_returns_non_overlapping_matches() -> None:
    """Search should advance past the current match."""
    assert find_matches("aaaa", "aa") == [(0, 0, 2), (0, 2, 4)]


def test_next_and_previous_match_index_wrap() -> None:
    """Match navigation should wrap at both ends."""
    assert next_match_index(-1, 3) == 0
    assert next_match_index(2, 3) == 0
    assert previous_match_index(-1, 3) == 2
    assert previous_match_index(0, 3) == 2


def test_empty_match_navigation_returns_negative_one() -> None:
    """Navigation without matches should not select an index."""
    assert next_match_index(0, 0) == -1
    assert previous_match_index(0, 0) == -1


def test_search_state_applies_and_clears_query() -> None:
    """SearchState should own query, matches, and active index together."""
    state = SearchState()

    state.apply_query("one two one", "one")

    assert state.query == "one"
    assert state.matches == [(0, 0, 3), (0, 8, 11)]
    assert state.active_match_index == 0

    state.clear()

    assert state.query == ""
    assert state.matches == []
    assert state.active_match_index == -1
