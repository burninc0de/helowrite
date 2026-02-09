"""Test type checking with mypy."""

import subprocess


def test_mypy():
    """Run mypy type checking and ensure it passes."""
    import sys
    from pathlib import Path

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "src",
            "--disable-error-code=attr-defined",
            "--disable-error-code=name-defined",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, f"MyPy failed:\n{result.stdout}\n{result.stderr}"
