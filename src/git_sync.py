"""Git synchronization helpers for HeloWrite."""

import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

LOG_FILE = Path(__file__).with_name("git_sync_errors.log")


@dataclass
class GitSyncResult:
    """Result of a git synchronization action."""

    message: str
    severity: str = "information"
    timeout: int = 2
    reload_current_file: bool = False
    refresh_file_panel: bool = False


async def run_git_push(file_path: Path) -> GitSyncResult:
    """Stage, commit, and push the current file."""
    file_dir = file_path.parent
    file_name = file_path.name
    current_cmd: Optional[str] = None

    try:
        current_cmd = "git stash push"
        try:
            await _run_subprocess(
                ["git", "stash", "push", "-m", "auto-stash before sync"], file_dir
            )
        except subprocess.CalledProcessError as e:
            if not _has_no_local_changes(e):
                raise

        current_cmd = "git stash pop"
        try:
            await _run_subprocess(["git", "stash", "pop"], file_dir)
        except subprocess.CalledProcessError as e:
            if _has_no_stash_entries(e):
                pass
            else:
                await _abort_merge_or_rebase(file_dir)
                return GitSyncResult(
                    "Git push aborted: conflicts detected when restoring stashed changes. Please resolve manually.",
                    severity="error",
                    timeout=10,
                )

        current_cmd = "git add"
        await _run_subprocess(["git", "add", file_name], file_dir)

        current_cmd = "git commit"
        try:
            await _run_subprocess(
                ["git", "commit", "-m", f"Update {file_name}"], file_dir
            )
        except subprocess.CalledProcessError as e:
            if _has_nothing_to_commit(e):
                return GitSyncResult("No changes to commit")
            raise

        current_cmd = "git push"
        try:
            await _run_subprocess(["git", "push"], file_dir)
        except subprocess.CalledProcessError as e:
            if not _is_up_to_date(e):
                raise

        return GitSyncResult(f"Git push completed for {file_name}")
    except subprocess.CalledProcessError as e:
        error_details = _error_details(e)
        if "up to date" in error_details:
            return GitSyncResult("Git push completed (already up to date)")

        if "Updates were rejected because the remote contains work" in error_details:
            error_msg = "Git push failed: remote has changes you don't have. Try pulling first with Alt+H, then push again."
        elif "no upstream branch" in error_details:
            error_msg = "Git push failed: no upstream branch set. Try pulling first with Alt+H to set it up."
        else:
            error_msg = "Git push failed - check git_sync_errors.log for details. You may need to resolve conflicts manually."
        _write_log(f"Command '{current_cmd}' failed: {error_details}")
        return GitSyncResult(error_msg, severity="error", timeout=10)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        _write_log(error_msg)
        return GitSyncResult(error_msg, severity="error", timeout=10)


async def run_git_pull(file_path: Path) -> GitSyncResult:
    """Pull remote changes for the current file's repository."""
    file_dir = file_path.parent
    file_name = file_path.name
    result = await _run_git_pull_in_directory(
        file_dir,
        stash_message="auto-stash before pull",
        conflict_message="Git pull aborted: conflicts detected when restoring stashed changes. Please resolve manually.",
        failure_message="Git pull failed - check git_sync_errors.log for details. You may need to resolve conflicts manually.",
        already_current_message="Git pull completed (already up to date)",
        success_message=f"Git pull completed for {file_name}",
    )
    if result.severity != "error":
        result.reload_current_file = True
    return result


async def run_git_pull_vault(vault_path: Path) -> GitSyncResult:
    """Pull remote changes for the configured vault repository."""
    return await _run_git_pull_in_directory(
        vault_path,
        stash_message="auto-stash before pull",
        conflict_message="Git pull vault aborted: conflicts detected when restoring stashed changes. Please resolve manually.",
        failure_message="Git pull vault failed - check git_sync_errors.log for details. You may need to resolve conflicts manually.",
        already_current_message="Git pull vault completed (already up to date)",
        success_message="Git pull completed for vault",
        reload_current_file=True,
        refresh_file_panel=True,
    )


async def _run_git_pull_in_directory(
    repo_dir: Path,
    stash_message: str,
    conflict_message: str,
    failure_message: str,
    already_current_message: str,
    success_message: str,
    reload_current_file: bool = False,
    refresh_file_panel: bool = False,
) -> GitSyncResult:
    current_cmd: Optional[str] = None

    try:
        current_cmd = "git stash push"
        try:
            await _run_subprocess(
                ["git", "stash", "push", "-m", stash_message], repo_dir
            )
        except subprocess.CalledProcessError as e:
            if not _has_no_local_changes(e):
                raise

        current_cmd = "git pull"
        try:
            await _run_subprocess(["git", "pull"], repo_dir)
        except subprocess.CalledProcessError as e:
            if _is_up_to_date(e):
                pass
            elif "There is no tracking information" in e.stderr:
                await _set_upstream_and_pull(repo_dir)
            else:
                raise

        current_cmd = "git stash pop"
        try:
            await _run_subprocess(["git", "stash", "pop"], repo_dir)
        except subprocess.CalledProcessError as e:
            if _has_no_stash_entries(e):
                pass
            else:
                await _abort_merge_or_rebase(repo_dir)
                return GitSyncResult(conflict_message, severity="error", timeout=10)

        return GitSyncResult(
            success_message,
            reload_current_file=reload_current_file,
            refresh_file_panel=refresh_file_panel,
        )
    except subprocess.CalledProcessError as e:
        error_details = _error_details(e)
        if "up to date" in error_details:
            return GitSyncResult(
                already_current_message,
                reload_current_file=reload_current_file,
                refresh_file_panel=refresh_file_panel,
            )

        _write_log(f"Command '{current_cmd}' failed: {error_details}")
        return GitSyncResult(failure_message, severity="error", timeout=10)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        _write_log(error_msg)
        return GitSyncResult(error_msg, severity="error", timeout=10)


async def _set_upstream_and_pull(repo_dir: Path) -> None:
    branch_result = await _run_subprocess(["git", "branch", "--show-current"], repo_dir)
    current_branch = branch_result.stdout.strip()

    remote_result = await _run_subprocess(["git", "remote"], repo_dir)
    remotes = remote_result.stdout.strip().split("\n")

    if "origin" not in remotes:
        raise subprocess.CalledProcessError(
            1, ["git", "remote"], stderr="No origin remote found"
        )

    await _run_subprocess(
        [
            "git",
            "branch",
            "--set-upstream-to",
            f"origin/{current_branch}",
            current_branch,
        ],
        repo_dir,
    )
    await _run_subprocess(["git", "pull"], repo_dir)


async def _abort_merge_or_rebase(repo_dir: Path) -> None:
    for cmd in (["git", "rebase", "--abort"], ["git", "merge", "--abort"]):
        try:
            await _run_subprocess(cmd, repo_dir)
        except subprocess.CalledProcessError:
            pass


async def _run_subprocess(
    cmd: list[str], cwd: Path
) -> subprocess.CompletedProcess[str]:
    return await asyncio.to_thread(
        subprocess.run,
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )


def _error_details(error: subprocess.CalledProcessError) -> str:
    return (
        error.stderr.strip()
        or error.stdout.strip()
        or f"Command failed with return code {error.returncode}"
    )


def _has_no_local_changes(error: subprocess.CalledProcessError) -> bool:
    return (
        "No local changes to save" in error.stdout
        or "No local changes to save" in error.stderr
    )


def _has_no_stash_entries(error: subprocess.CalledProcessError) -> bool:
    return "No stash entries found" in error.stderr


def _has_nothing_to_commit(error: subprocess.CalledProcessError) -> bool:
    return "nothing to commit" in error.stdout or "nothing to commit" in error.stderr


def _is_up_to_date(error: subprocess.CalledProcessError) -> bool:
    return (
        "Everything up-to-date" in error.stdout
        or "Everything up-to-date" in error.stderr
        or "Already up to date" in error.stdout
        or "Already up to date" in error.stderr
        or "up to date" in error.stdout
        or "up to date" in error.stderr
    )


def _write_log(message: str) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")
