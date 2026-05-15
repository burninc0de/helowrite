"""Tests for git synchronization helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import git_sync


def completed(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Create a successful subprocess result for a fake git command."""
    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


@pytest.mark.asyncio
async def test_git_push_returns_no_changes_when_commit_is_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An empty commit should skip push and report that nothing changed."""
    commands: list[list[str]] = []
    file_path = tmp_path / "note.md"

    async def fake_run_subprocess(cmd: list[str], cwd: Path):
        commands.append(cmd)
        if cmd[:2] == ["git", "commit"]:
            raise subprocess.CalledProcessError(1, cmd, output="nothing to commit")
        return completed(cmd)

    monkeypatch.setattr(git_sync, "_run_subprocess", fake_run_subprocess)

    result = await git_sync.run_git_push(file_path)

    assert result.message == "No changes to commit"
    assert ["git", "push"] not in commands


@pytest.mark.asyncio
async def test_git_pull_marks_current_file_for_reload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A successful pull should tell the app to reload the current file."""
    file_path = tmp_path / "note.md"

    async def fake_run_subprocess(cmd: list[str], cwd: Path):
        return completed(cmd)

    monkeypatch.setattr(git_sync, "_run_subprocess", fake_run_subprocess)

    result = await git_sync.run_git_pull(file_path)

    assert result.message == "Git pull completed for note.md"
    assert result.reload_current_file
    assert result.severity == "information"


@pytest.mark.asyncio
async def test_git_pull_vault_reports_stash_conflicts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A stash-pop conflict should return an error result."""

    async def fake_run_subprocess(cmd: list[str], cwd: Path):
        if cmd == ["git", "stash", "pop"]:
            raise subprocess.CalledProcessError(1, cmd, stderr="conflict")
        return completed(cmd)

    monkeypatch.setattr(git_sync, "_run_subprocess", fake_run_subprocess)

    result = await git_sync.run_git_pull_vault(tmp_path)

    assert result.severity == "error"
    assert result.timeout == 10
    assert result.message.startswith("Git pull vault aborted")
