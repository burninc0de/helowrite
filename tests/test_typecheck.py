"""Test type checking with mypy."""

import subprocess


def test_mypy():
    """Run mypy type checking and ensure it passes."""
    import sys
    from pathlib import Path

    # Uninstall the editable package first to avoid duplicate module errors
    subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "helowrite", "-y"],
        capture_output=True,
    )

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "src",
                "--disable-error-code=attr-defined",
                "--disable-error-code=name-defined",
                "--disable-error-code=var-annotated",
                "--disable-error-code=arg-type",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0, f"MyPy failed:\n{result.stdout}\n{result.stderr}"
    finally:
        # Reinstall the package for other tests
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", ".", "-q"],
            capture_output=True,
        )
