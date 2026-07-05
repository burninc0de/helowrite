"""Markdown highlighting latency comparison tests."""

from __future__ import annotations

import os
import statistics
import time
from collections import defaultdict
from pathlib import Path

import pytest
import textual.message_pump as mp

from tests.test_widgets import _SnippetApp
from widgets import HeloWriteTextArea


def _markdown_perf_text(blocks: int = 1500) -> str:
    return "\n".join(
        "\n".join(
            [
                f"# Heading {index}",
                f"> Quote {index}",
                f"- Unordered item {index}",
                f"- [ ] Task item {index}",
                f"1. Ordered item {index}",
                f"1. [x] Ordered task {index}",
                f"[site](https://example.com/{index}) ![img](a.png)",
                f"plain **bold {index}** and *italic {index}*",
                f"`code {index}` and ~~strike {index}~~",
            ]
        )
        for index in range(blocks)
    )


def _build_legacy_markdown_highlights(widget: HeloWriteTextArea) -> None:
    highlights: defaultdict[int, list[tuple[int, int, str]]] = defaultdict(list)
    lines = widget.text.splitlines()

    for line_number, line in enumerate(lines):
        heading_match = widget.MARKDOWN_HEADING_RE.match(line)
        if heading_match:
            highlights[line_number].append(
                (heading_match.start(1), heading_match.end(1), "markdown_heading")
            )

        quote_match = widget.MARKDOWN_BLOCKQUOTE_RE.match(line)
        if quote_match:
            highlights[line_number].append(
                (quote_match.start(1), quote_match.end(1), "markdown_blockquote")
            )

        for regex, token in (
            (widget.MARKDOWN_IMAGE_RE, "markdown_image"),
            (widget.MARKDOWN_LINK_RE, "markdown_link"),
            (widget.MARKDOWN_CODE_RE, "markdown_code"),
            (widget.MARKDOWN_BOLD_RE, "markdown_bold"),
            (widget.MARKDOWN_ITALIC_RE, "markdown_italic"),
            (widget.MARKDOWN_STRIKETHROUGH_RE, "markdown_strikethrough"),
        ):
            for match in regex.finditer(line):
                highlights[line_number].append((match.start(), match.end(), token))

    widget._highlights = highlights


def _measure(callable_under_test, iterations: int = 6) -> list[float]:
    timings = []
    for _ in range(iterations):
        started = time.perf_counter()
        callable_under_test()
        timings.append(time.perf_counter() - started)
    return timings


@pytest.mark.performance
@pytest.mark.skipif(
    os.environ.get("HELOWRITE_RUN_PERF") != "1",
    reason="Set HELOWRITE_RUN_PERF=1 to run markdown highlighting latency test",
)
def test_profile_markdown_highlighting_before_after(temp_config_dir: Path) -> None:
    """Compare list and task marker coloring against the previous rule set."""
    app = _SnippetApp()
    app.language = "markdown"
    token = mp.active_app.set(app)
    try:
        widget = HeloWriteTextArea()
        widget.text = _markdown_perf_text()

        def measure_legacy() -> None:
            widget._highlights.clear()
            _build_legacy_markdown_highlights(widget)

        def measure_expanded() -> None:
            widget._highlights.clear()
            widget._build_markdown_highlights()

        legacy_timings = _measure(measure_legacy)
        expanded_timings = _measure(measure_expanded)
        legacy_avg_ms = statistics.mean(legacy_timings) * 1000
        expanded_avg_ms = statistics.mean(expanded_timings) * 1000
        ratio = expanded_avg_ms / legacy_avg_ms

        print(
            "\nmarkdown-highlight profile "
            f"legacy_avg_ms={legacy_avg_ms:.3f} "
            f"expanded_avg_ms={expanded_avg_ms:.3f} "
            f"ratio={ratio:.2f}"
        )

        assert ratio <= 1.75
    finally:
        mp.active_app.reset(token)
