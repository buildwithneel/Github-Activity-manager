"""Secure session management using OS keyring / encrypted local credential store."""

from dataclasses import dataclass

from github_activity_generator.constants import (
    KEYRING_AUTH_METHOD_KEY,
    KEYRING_TOKEN_KEY,
)
from github_activity_generator.exceptions import AuthenticationError
from github_activity_generator.github.client import GitHubClient
from github_activity_generator.github.profile import UserProfile, fetch_user_profile
from github_activity_generator.storage.keyring_store import KeyringStore


@dataclass
class AuthStatus:
    """Represents the current authentication state without exposing secrets."""

    authenticated: bool
    auth_method: str | None = None
    username: str | None = None
    scopes: list[str] | None = None
    storage_backend: str = "os_keyring"


class SessionManager:
    """Manages GitHub authentication sessions and token validation."""

    def __init__(self, keyring_store: KeyringStore) -> None:
        self.keyring_store = keyring_store
        self._cached_profile: UserProfile | None = None

    def save_session(self, token: str, auth_method: str, profile: UserProfile) -> None:
        """Persist token and auth method securely in the credential store."""
        self.keyring_store.set_secret(KEYRING_TOKEN_KEY, token.strip())
        self.keyring_store.set_secret(KEYRING_AUTH_METHOD_KEY, auth_method)
        self._cached_profile = profile

    def get_token(self) -> str | None:
        """Retrieve the stored GitHub token if present."""
        return self.keyring_store.get_secret(KEYRING_TOKEN_KEY)

    def get_auth_method(self) -> str | None:
        """Retrieve the stored authentication method ('oauth' or 'pat')."""
        return self.keyring_store.get_secret(KEYRING_AUTH_METHOD_KEY)

    def has_stored_credentials(self) -> bool:
        """Return True if a token is currently stored."""
        return bool(self.get_token())

    def get_authenticated_client(self) -> GitHubClient:
        """Return a GitHubClient configured with the stored token."""
        token = self.get_token()
        if not token:
            raise AuthenticationError("Not authenticated. Please log in with OAuth or a PAT.")
        return GitHubClient(token=token)

    def validate_session(self, force_refresh: bool = False) -> AuthStatus:
        """Validate stored credentials against GitHub and return AuthStatus."""
        backend = "os_keyring" if self.keyring_store.using_os_keyring else "encrypted_local_file"
        token = self.get_token()
        auth_method = self.get_auth_method()
        if not token:
            self._cached_profile = None
            return AuthStatus(authenticated=False, storage_backend=backend)

        if self._cached_profile is not None and not force_refresh:
            return AuthStatus(
                authenticated=True,
                auth_method=auth_method,
                username=self._cached_profile.login,
                scopes=self._cached_profile.scopes,
                storage_backend=backend,
            )

        client = GitHubClient(token=token)
        profile = fetch_user_profile(client)
        self._cached_profile = profile
        return AuthStatus(
            authenticated=True,
            auth_method=auth_method,
            username=profile.login,
            scopes=profile.scopes,
            storage_backend=backend,
        )

    def get_cached_profile(self) -> UserProfile | None:
        return self._cached_profile

    def logout(self) -> None:
        """Clear stored credentials and cached session state."""
        self.keyring_store.delete_secret(KEYRING_TOKEN_KEY)
        self.keyring_store.delete_secret(KEYRING_AUTH_METHOD_KEY)
        self._cached_profile = None
