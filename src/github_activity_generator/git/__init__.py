"""Safe local Git operations, repository initialization, and single-file workflow."""

from github_activity_generator.git.operations import (
    commit_activity_change,
    prepare_activity_entry,
    push_to_remote,
)
from github_activity_generator.git.repository import clone_repository, initialize_local_repository
from github_activity_generator.git.safety import (
    RepoSafetyStatus,
    ensure_git_installed,
    inspect_repo_safety,
    run_git,
    validate_safe_to_operate,
)

__all__ = [
    "RepoSafetyStatus",
    "clone_repository",
    "commit_activity_change",
    "ensure_git_installed",
    "initialize_local_repository",
    "inspect_repo_safety",
    "prepare_activity_entry",
    "push_to_remote",
    "run_git",
    "validate_safe_to_operate",
]
