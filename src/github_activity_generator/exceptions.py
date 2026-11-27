"""Structured domain exceptions for GitHub Activity Generator."""


class AppError(Exception):
    """Base exception for all application errors."""


class AuthenticationError(AppError):
    """Raised when authentication fails, expires, or is missing."""


class PermissionError_(AppError):
    """Raised when the GitHub token lacks required permissions."""


class RateLimitError(AppError):
    """Raised when the GitHub API rate limit is exceeded."""

    def __init__(self, message: str, reset_timestamp: int | None = None) -> None:
        super().__init__(message)
        self.reset_timestamp = reset_timestamp


class NetworkError(AppError):
    """Raised when a network request cannot reach GitHub."""


class GitHubAPIError(AppError):
    """Raised when GitHub returns an unexpected API or GraphQL error."""


class ValidationError(AppError):
    """Raised when user configuration or date range validation fails."""


class ImpossibleTargetError(ValidationError):
    """Raised when a requested commit distribution target cannot be satisfied."""


class GitOperationError(AppError):
    """Raised when a local Git command fails or violates safety checks."""


class RepositoryConflictError(GitOperationError):
    """Raised when a repository has uncommitted changes or file conflicts."""


class StorageError(AppError):
    """Raised when local storage or credential persistence fails."""
