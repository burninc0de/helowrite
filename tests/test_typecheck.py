"""Test type checking with ty."""

import subprocess
import sys
from pathlib import Path


def test_ty():
    """Run ty type checking and ensure it passes."""
    result = subprocess.run(
        [sys.executable, "-m", "ty", "check"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, f"ty failed:\n{result.stdout}\n{result.stderr}"


# Keep alias for backwards compatibility until CI is updated
test_mypy = test_ty
