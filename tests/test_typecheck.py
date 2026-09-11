"""Test type checking with ty."""

import subprocess
import sys
from pathlib import Path


def test_ty():
    """Run ty type checking and ensure it passes."""
    root = Path(__file__).parent.parent
    cmd = [sys.executable, "-m", "ty", "check"]
    # In local dev `venv` exists (ty needs --python venv to find deps),
    # in CI deps are in the system env and no venv dir exists.
    if (root / "venv").is_dir():
        cmd += ["--python", "venv"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=root,
    )
    assert result.returncode == 0, f"ty failed:\n{result.stdout}\n{result.stderr}"


# Keep alias for backwards compatibility until CI is updated
test_mypy = test_ty
