"""Tests for Pomodoro timer helpers."""

from pomodoro import (
    parse_pomodoro_minutes,
    schedule_countdown,
    seconds_for_minutes,
)


def test_parse_pomodoro_minutes_accepts_valid_number() -> None:
    assert parse_pomodoro_minutes("25") == (25, None)


def test_parse_pomodoro_minutes_rejects_blank() -> None:
    assert parse_pomodoro_minutes("  ") == (None, "Please enter time in minutes")


def test_parse_pomodoro_minutes_rejects_non_numeric() -> None:
    assert parse_pomodoro_minutes("25m") == (
        None,
        "Please enter a valid number (e.g., 25)",
    )


def test_parse_pomodoro_minutes_rejects_out_of_range() -> None:
    assert parse_pomodoro_minutes("0") == (
        None,
        "Time must be between 1 and 1440 minutes",
    )
    assert parse_pomodoro_minutes("1441") == (
        None,
        "Time must be between 1 and 1440 minutes",
    )


def test_seconds_for_minutes() -> None:
    assert seconds_for_minutes(25) == 1500


def test_schedule_countdown_calls_complete_after_ticks() -> None:
    callbacks = []
    completed = {"value": False}

    def set_timer(delay: float, callback):
        callbacks.append((delay, callback))

    def on_complete() -> None:
        completed["value"] = True

    schedule_countdown(2, set_timer, on_complete)

    assert completed["value"] is False
    assert len(callbacks) == 1
    assert callbacks[0][0] == 1.0

    callbacks.pop(0)[1]()
    assert completed["value"] is False

    callbacks.pop(0)[1]()
    assert completed["value"] is True
