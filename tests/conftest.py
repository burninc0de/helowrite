"""Shared pytest fixtures to keep tests isolated."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture()
def temp_config_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide an isolated config directory with automatic cleanup."""

    config_dir = tmp_path / "helowrite-config"
    config_dir.mkdir()
    previous = os.environ.get("ELOSCRIBE_CONFIG_DIR")
    os.environ["ELOSCRIBE_CONFIG_DIR"] = str(config_dir)
    try:
        yield config_dir
    finally:
        if previous is None:
            os.environ.pop("ELOSCRIBE_CONFIG_DIR", None)
        else:
            os.environ["ELOSCRIBE_CONFIG_DIR"] = previous
