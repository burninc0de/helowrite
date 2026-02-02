"""Linting and formatting tests."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_ruff_check():
    """Test that code passes ruff linting checks."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "src/"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"


def test_ruff_format():
    """Test that code is properly formatted."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", "src/"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, f"Ruff format check failed:\n{result.stdout}\n{result.stderr}"