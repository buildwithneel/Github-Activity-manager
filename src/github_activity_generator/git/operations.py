"""Single text-file workflow and confirmation-gated current-time Git operations."""

import difflib
from datetime import datetime, timezone
from pathlib import Path

from github_activity_generator.constants import (
    ACTIVITY_FILENAME,
    ACTIVITY_SECTION_END,
    ACTIVITY_SECTION_START,
)
from github_activity_generator.exceptions import GitOperationError
from github_activity_generator.git.safety import ensure_only_allowed_staged, run_git


def prepare_activity_entry(
    repo_path: Path,
    note: str,
    *,
    filename: str = ACTIVITY_FILENAME,
) -> tuple[bool, str]:
    """Update only the application's delimited section in activity.txt, preserving all other text."""
    cleaned_note = note.strip()
    if not cleaned_note:
        return False, ""

    target = repo_path / filename
    existing_text = target.read_text(encoding="utf-8") if target.exists() else ""

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry_line = f"[{timestamp}] {cleaned_note}"

    new_text = _insert_into_managed_section(existing_text, entry_line)
    if new_text == existing_text:
        return False, ""

    target.write_text(new_text, encoding="utf-8")

    diff = "".join(
        difflib.unified_diff(
            existing_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )
    return True, diff


def _insert_into_managed_section(existing_text: str, entry_line: str) -> str:
    if ACTIVITY_SECTION_START in existing_text and ACTIVITY_SECTION_END in existing_text:
        before, rest = existing_text.split(ACTIVITY_SECTION_START, 1)
        section_body, after = rest.split(ACTIVITY_SECTION_END, 1)
        lines = [ln for ln in section_body.splitlines() if ln.strip()]
        if entry_line in lines:
            return existing_text
        lines.append(entry_line)
        body = "\n".join(lines)
        return f"{before}{ACTIVITY_SECTION_START}\n{body}\n{ACTIVITY_SECTION_END}{after}"

    prefix = existing_text
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    if prefix:
        prefix += "\n"
    return (
        f"{prefix}{ACTIVITY_SECTION_START}\n"
        f"{entry_line}\n"
        f"{ACTIVITY_SECTION_END}\n"
    )


def commit_activity_change(
    repo_path: Path,
    commit_message: str,
    *,
    filename: str = ACTIVITY_FILENAME,
    dry_run: bool = False,
) -> str:
    """Stage only the activity file and create a genuine current-time commit."""
    if not commit_message.strip():
        raise GitOperationError("Commit message cannot be empty.")

    if dry_run:
        return f"[DRY RUN] Would stage '{filename}' and commit with message: {commit_message}"

    run_git(["add", "--", filename], cwd=repo_path)
    ensure_only_allowed_staged(repo_path, allowed_filename=filename)
    # Strictly current system time; no --date backdating
    return run_git(["commit", "-m", commit_message.strip()], cwd=repo_path)


def push_to_remote(
    repo_path: Path,
    *,
    remote: str = "origin",
    branch: str = "main",
    confirmed: bool = False,
    dry_run: bool = False,
) -> str:
    """Push commits to remote only after explicit user confirmation (never force-push)."""
    if not confirmed:
        raise GitOperationError(
            "Push cancelled: explicit user confirmation is required before pushing."
        )
    if dry_run:
        return f"[DRY RUN] Would push branch '{branch}' to remote '{remote}'."
    return run_git(["push", "-u", remote, branch], cwd=repo_path)
