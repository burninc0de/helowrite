"""Pomodoro timer helpers."""

import re
from typing import Callable, Optional

MAX_POMODORO_MINUTES = 1440


def parse_pomodoro_minutes(value: str) -> tuple[Optional[int], Optional[str]]:
    """Parse and validate a Pomodoro duration in minutes."""
    time_str = value.strip()
    if not time_str:
        return None, "Please enter time in minutes"

    if not re.match(r"^(\d+)$", time_str):
        return None, "Please enter a valid number (e.g., 25)"

    minutes = int(time_str)
    if minutes <= 0 or minutes > MAX_POMODORO_MINUTES:
        return None, "Time must be between 1 and 1440 minutes"

    return minutes, None


def seconds_for_minutes(minutes: int) -> int:
    """Convert minutes to seconds for countdown scheduling."""
    return minutes * 60


def schedule_pomodoro_timer(
    minutes: int,
    set_timer: Callable[[float, Callable[[], None]], object],
    on_complete: Callable[[], None],
) -> None:
    """Schedule a Pomodoro countdown using Textual's timer callback API."""
    schedule_countdown(seconds_for_minutes(minutes), set_timer, on_complete)


def schedule_countdown(
    total_seconds: int,
    set_timer: Callable[[float, Callable[[], None]], object],
    on_complete: Callable[[], None],
) -> None:
    """Schedule a one-second ticking countdown."""

    def tick(remaining: int) -> None:
        if remaining > 0:
            next_remaining = remaining - 1

            def next_tick() -> None:
                tick(next_remaining)

            set_timer(1.0, next_tick)
            return
        on_complete()

    tick(total_seconds)
