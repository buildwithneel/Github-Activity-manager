"""Personal Access Token (PAT) authentication handler."""

from github_activity_generator.auth.session import SessionManager
from github_activity_generator.exceptions import AuthenticationError
from github_activity_generator.github.client import GitHubClient
from github_activity_generator.github.profile import UserProfile, fetch_user_profile

RECOMMENDED_PAT_SCOPES = [
    "read:user (view your GitHub profile and contribution calendar)",
    "repo (optional: only needed if creating or pushing to repositories)",
]


class PATAuthenticator:
    """Authenticates a user via a GitHub Personal Access Token."""

    def __init__(self, session_manager: SessionManager) -> None:
        self.session_manager = session_manager

    def authenticate(self, token: str) -> UserProfile:
        """Verify the PAT with GitHub and store it securely."""
        cleaned = token.strip()
        if not cleaned:
            raise AuthenticationError("Personal Access Token cannot be empty.")
        if len(cleaned) < 10:
            raise AuthenticationError("Personal Access Token appears too short to be valid.")

        client = GitHubClient(token=cleaned)
        profile = fetch_user_profile(client)
        if not profile.login:
            raise AuthenticationError("Unable to verify GitHub username for this token.")

        self.session_manager.save_session(cleaned, "pat", profile)
        return profile
