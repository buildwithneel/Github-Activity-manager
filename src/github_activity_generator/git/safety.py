"""Git safety checks to protect existing repositories, history, and unrelated files."""

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from github_activity_generator.constants import ACTIVITY_FILENAME
from github_activity_generator.exceptions import GitOperationError, RepositoryConflictError


@dataclass
class RepoSafetyStatus:
    """Snapshot of a local repository's safety state."""

    is_git_repo: bool
    has_uncommitted_changes: bool
    modified_files: list[str]
    untracked_files: list[str]
    current_branch: str | None
    remote_url: str | None
    has_activity_file: bool


def ensure_git_installed() -> str:
    """Verify git binary is available on PATH."""
    git_path = shutil.which("git")
    if not git_path:
        raise GitOperationError("Git is not installed or not found on PATH.")
    return git_path


def run_git(args: list[str], cwd: Path) -> str:
    """Execute a git command safely without shell=True and return stdout."""
    ensure_git_installed()
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise GitOperationError(f"Failed to run git {' '.join(args)}: {exc}") from exc

    if proc.returncode != 0:
        err = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
        raise GitOperationError(f"Git command 'git {' '.join(args)}' failed: {err}")
    return proc.stdout.rstrip("\r\n")


def inspect_repo_safety(repo_path: Path) -> RepoSafetyStatus:
    """Inspect a directory for Git status, uncommitted changes, branch, and remote."""
    if not repo_path.exists() or not (repo_path / ".git").exists():
        return RepoSafetyStatus(
            is_git_repo=False,
            has_uncommitted_changes=False,
            modified_files=[],
            untracked_files=[],
            current_branch=None,
            remote_url=None,
            has_activity_file=(repo_path / ACTIVITY_FILENAME).exists(),
        )

    status_out = run_git(["status", "--porcelain"], cwd=repo_path)
    modified: list[str] = []
    untracked: list[str] = []
    for line in status_out.splitlines():
        if not line.strip():
            continue
        code = line[:2]
        filename = line[3:].strip()
        if code == "??":
            untracked.append(filename)
        else:
            modified.append(filename)

    branch: str | None = None
    try:
        branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    except GitOperationError:
        branch = None

    remote_url: str | None = None
    try:
        remote_url = run_git(["remote", "get-url", "origin"], cwd=repo_path)
    except GitOperationError:
        remote_url = None

    return RepoSafetyStatus(
        is_git_repo=True,
        has_uncommitted_changes=bool(modified or untracked),
        modified_files=modified,
        untracked_files=untracked,
        current_branch=branch,
        remote_url=remote_url,
        has_activity_file=(repo_path / ACTIVITY_FILENAME).exists(),
    )


def validate_safe_to_operate(repo_path: Path) -> RepoSafetyStatus:
    """Ensure an existing repository has no uncommitted changes before automated edits."""
    status = inspect_repo_safety(repo_path)
    if not status.is_git_repo:
        raise GitOperationError(f"'{repo_path}' is not an initialized Git repository.")
    if status.has_uncommitted_changes:
        changed = ", ".join(status.modified_files + status.untracked_files)
        raise RepositoryConflictError(
            f"Repository has uncommitted changes ({changed}). "
            "Please commit or stash your work before continuing."
        )
    return status


def ensure_only_allowed_staged(repo_path: Path, allowed_filename: str = ACTIVITY_FILENAME) -> None:
    """Verify that only the dedicated activity file is staged for commit."""
    staged = run_git(["diff", "--cached", "--name-only"], cwd=repo_path)
    files = [f.strip() for f in staged.splitlines() if f.strip()]
    unexpected = [f for f in files if f != allowed_filename]
    if unexpected:
        raise RepositoryConflictError(
            f"Refusing to commit unrelated staged files: {', '.join(unexpected)}"
        )
