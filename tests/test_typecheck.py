"""Test type checking with mypy."""

import subprocess


def test_mypy():
    """Run mypy type checking and ensure it passes."""
    result = subprocess.run(
        ["mypy", "src", "--disable-error-code=attr-defined", "--disable-error-code=name-defined"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"MyPy failed:\n{result.stdout}\n{result.stderr}"