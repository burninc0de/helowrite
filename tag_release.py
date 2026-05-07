#!/usr/bin/env python3
"""Tag and push a release based on pyproject.toml version."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYPROJECT_PATH = ROOT / "pyproject.toml"
TAG_PREFIX = "v"


def read_version_from_pyproject(pyproject_path: Path) -> str:
    try:
        text = pyproject_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"Error: {pyproject_path} not found")

    match = re.search(r"^\s*version\s*=\s*[\"']([^\"']+)[\"']", text, re.MULTILINE)
    if not match:
        raise SystemExit("Error: Could not find version in pyproject.toml")

    return match.group(1).strip()


def check_tag_exists(tag: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def run_command(command: list[str], dry_run: bool = False) -> None:
    print("+", " ".join(command))
    if dry_run:
        return

    result = subprocess.run(command)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create and push a release tag from pyproject.toml.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    version = read_version_from_pyproject(PYPROJECT_PATH)
    tag = version if version.startswith(TAG_PREFIX) else f"{TAG_PREFIX}{version}"

    if check_tag_exists(tag):
        raise SystemExit(f"Error: tag '{tag}' already exists locally. Delete it first or bump the version.")

    run_command(["git", "tag", "-a", tag, "-m", tag], dry_run=args.dry_run)
    run_command(["git", "push", "origin", tag], dry_run=args.dry_run)


if __name__ == "__main__":
    main()
