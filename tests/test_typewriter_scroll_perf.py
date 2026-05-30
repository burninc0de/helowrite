"""Typewriter-mode scroll latency regression and profiling tests."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict

import pytest

from app import HeloWrite
from widgets import HeloWriteTextArea


def _large_text(line_count: int = 6000) -> str:
    return "\n".join(f"line {index:05d}" for index in range(line_count))


async def _measure_manual_scroll_path(
    app: HeloWrite,
    pilot,
    *,
    typewriter_enabled: bool,
    iterations: int,
) -> Dict[str, Any]:
    editor = app.query_one("#editor", HeloWriteTextArea)

    if app.typewriter_mode != typewriter_enabled:
        app.action_toggle_typewriter_mode()
        await pilot.pause()

    total_lines = max(1, editor.text.count("\n") + 1)
    anchor_row = total_lines // 2
    editor.cursor_location = (anchor_row, 0)
    await pilot.pause()

    editor._last_typewriter_center_state = {
        "cursor": editor.cursor_location,
        "scroll_y": float(editor.scroll_y),
        "target": float(editor.scroll_y),
        "max_scroll_y": float(editor.max_scroll_y),
        "view_height": int(editor.scrollable_content_region.height),
    }

    stats: Dict[str, Any] = {
        "scroll_calls": 0,
        "scroll_total_seconds": 0.0,
        "center_calls": 0,
        "center_total_seconds": 0.0,
        "iterations": iterations,
    }

    original_scroll_cursor_visible = editor.scroll_cursor_visible
    original_center_cursor_typewriter = editor._center_cursor_typewriter

    def timed_scroll_cursor_visible(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_scroll_cursor_visible(*args, **kwargs)
        finally:
            stats["scroll_calls"] += 1
            stats["scroll_total_seconds"] += time.perf_counter() - started

    def timed_center_cursor_typewriter(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_center_cursor_typewriter(*args, **kwargs)
        finally:
            stats["center_calls"] += 1
            stats["center_total_seconds"] += time.perf_counter() - started

    editor.scroll_cursor_visible = timed_scroll_cursor_visible  # type: ignore[method-assign]
    editor._center_cursor_typewriter = timed_center_cursor_typewriter  # type: ignore[method-assign]

    try:
        for _ in range(iterations):
            editor.scroll_y = min(
                float(editor.max_scroll_y), float(editor.scroll_y) + 1.0
            )
            editor.scroll_cursor_visible()
        await pilot.pause()
    finally:
        editor.scroll_cursor_visible = original_scroll_cursor_visible  # type: ignore[method-assign]
        editor._center_cursor_typewriter = original_center_cursor_typewriter  # type: ignore[method-assign]

    if stats["scroll_calls"]:
        stats["scroll_avg_us"] = (
            stats["scroll_total_seconds"] / stats["scroll_calls"]
        ) * 1_000_000
    else:
        stats["scroll_avg_us"] = 0.0

    if stats["center_calls"]:
        stats["center_avg_us"] = (
            stats["center_total_seconds"] / stats["center_calls"]
        ) * 1_000_000
    else:
        stats["center_avg_us"] = 0.0

    return stats


async def _measure_cursor_move_path(
    app: HeloWrite,
    pilot,
    *,
    typewriter_enabled: bool,
    steps: int,
) -> Dict[str, Any]:
    editor = app.query_one("#editor", HeloWriteTextArea)

    if app.typewriter_mode != typewriter_enabled:
        app.action_toggle_typewriter_mode()
        await pilot.pause()

    total_lines = max(1, editor.text.count("\n") + 1)
    anchor_row = min(max(5, total_lines // 2), total_lines - 2)
    editor.cursor_location = (anchor_row, 0)
    await pilot.pause()

    stats: Dict[str, Any] = {
        "steps": steps,
        "elapsed_seconds": 0.0,
        "center_calls": 0,
        "center_total_seconds": 0.0,
    }

    original_center_cursor_typewriter = editor._center_cursor_typewriter

    def timed_center_cursor_typewriter(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_center_cursor_typewriter(*args, **kwargs)
        finally:
            stats["center_calls"] += 1
            stats["center_total_seconds"] += time.perf_counter() - started

    editor._center_cursor_typewriter = timed_center_cursor_typewriter  # type: ignore[method-assign]

    started = time.perf_counter()
    try:
        for _ in range(steps):
            await pilot.press("down")
    finally:
        stats["elapsed_seconds"] = time.perf_counter() - started
        editor._center_cursor_typewriter = original_center_cursor_typewriter  # type: ignore[method-assign]

    if steps:
        stats["avg_step_ms"] = (stats["elapsed_seconds"] / steps) * 1000
    else:
        stats["avg_step_ms"] = 0.0

    if stats["center_calls"]:
        stats["center_avg_us"] = (
            stats["center_total_seconds"] / stats["center_calls"]
        ) * 1_000_000
    else:
        stats["center_avg_us"] = 0.0

    return stats


@pytest.mark.asyncio
async def test_typewriter_manual_scroll_path_avoids_recentering(temp_config_dir: Path):
    """Manual scroll with stationary cursor should not invoke typewriter recentering."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor", HeloWriteTextArea)
        editor.load_text(_large_text())
        await pilot.pause()

        stats = await _measure_manual_scroll_path(
            app,
            pilot,
            typewriter_enabled=True,
            iterations=250,
        )

        assert stats["scroll_calls"] == 250
        assert stats["center_calls"] == 0


@pytest.mark.asyncio
@pytest.mark.performance
@pytest.mark.skipif(
    os.environ.get("HELOWRITE_RUN_PERF") != "1",
    reason="Set HELOWRITE_RUN_PERF=1 to run latency profiling test",
)
async def test_profile_manual_scroll_speed_typewriter_on_off(temp_config_dir: Path):
    """Profile manual scroll path timing with typewriter mode off vs on."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor", HeloWriteTextArea)
        editor.load_text(_large_text())
        await pilot.pause()

        stats_off = await _measure_manual_scroll_path(
            app,
            pilot,
            typewriter_enabled=False,
            iterations=800,
        )
        stats_on = await _measure_manual_scroll_path(
            app,
            pilot,
            typewriter_enabled=True,
            iterations=800,
        )

        # This profile output helps compare on/off behavior and identify
        # whether recentering calls contribute to manual-scroll latency.
        print(
            "\nmanual-scroll profile "
            f"off_avg_us={stats_off['scroll_avg_us']:.2f} "
            f"on_avg_us={stats_on['scroll_avg_us']:.2f} "
            f"off_center_calls={stats_off['center_calls']} "
            f"on_center_calls={stats_on['center_calls']}"
        )

        assert stats_off["scroll_calls"] == 800
        assert stats_on["scroll_calls"] == 800
        assert stats_on["center_calls"] == 0


@pytest.mark.asyncio
@pytest.mark.performance
@pytest.mark.skipif(
    os.environ.get("HELOWRITE_RUN_PERF") != "1",
    reason="Set HELOWRITE_RUN_PERF=1 to run latency profiling test",
)
async def test_profile_cursor_move_speed_typewriter_on_off(temp_config_dir: Path):
    """Profile down-arrow movement timing with typewriter mode off vs on."""
    app = HeloWrite()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor", HeloWriteTextArea)
        editor.load_text(_large_text())
        await pilot.pause()

        stats_off = await _measure_cursor_move_path(
            app,
            pilot,
            typewriter_enabled=False,
            steps=220,
        )
        stats_on = await _measure_cursor_move_path(
            app,
            pilot,
            typewriter_enabled=True,
            steps=220,
        )

        print(
            "\ncursor-move profile "
            f"off_avg_step_ms={stats_off['avg_step_ms']:.3f} "
            f"on_avg_step_ms={stats_on['avg_step_ms']:.3f} "
            f"off_center_calls={stats_off['center_calls']} "
            f"on_center_calls={stats_on['center_calls']} "
            f"on_center_avg_us={stats_on['center_avg_us']:.2f}"
        )

        assert stats_off["steps"] == 220
        assert stats_on["steps"] == 220
        assert stats_on["center_calls"] >= 1
