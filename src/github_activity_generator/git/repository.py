"""Safe local Git repository initialization and remote configuration."""

from pathlib import Path

from github_activity_generator.exceptions import RepositoryConflictError
from github_activity_generator.git.safety import ensure_git_installed, inspect_repo_safety, run_git


def initialize_local_repository(
    repo_path: Path,
    *,
    remote_url: str | None = None,
    branch: str = "main",
) -> Path:
    """Initialize a local Git repository safely without overwriting existing remotes or files."""
    ensure_git_installed()
    repo_path.mkdir(parents=True, exist_ok=True)
    status = inspect_repo_safety(repo_path)

    if not status.is_git_repo:
        run_git(["init", "-b", branch], cwd=repo_path)

    if remote_url:
        current_remote = inspect_repo_safety(repo_path).remote_url
        if current_remote is None:
            run_git(["remote", "add", "origin", remote_url], cwd=repo_path)
        elif current_remote != remote_url:
            raise RepositoryConflictError(
                f"Existing 'origin' remote ({current_remote}) differs from '{remote_url}'."
            )

    return repo_path


def clone_repository(remote_url: str, target_dir: Path) -> Path:
    """Clone a GitHub repository into target_dir if it does not already exist."""
    ensure_git_installed()
    if target_dir.exists() and any(target_dir.iterdir()):
        raise RepositoryConflictError(
            f"Target directory '{target_dir}' already exists and is not empty."
        )
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    run_git(["clone", remote_url, str(target_dir)], cwd=target_dir.parent)
    return target_dir
