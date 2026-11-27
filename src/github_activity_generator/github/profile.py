"""GitHub user profile retrieval."""

from dataclasses import dataclass

from github_activity_generator.github.client import GitHubClient


@dataclass
class UserProfile:
    """Authenticated GitHub user profile summary."""

    login: str
    name: str | None
    email: str | None
    bio: str | None
    public_repos: int
    followers: int
    following: int
    created_at: str
    html_url: str
    scopes: list[str]


def fetch_user_profile(client: GitHubClient) -> UserProfile:
    """Fetch the authenticated user's profile and granted token scopes."""
    data, headers = client.get("/user")
    scopes_raw = headers.get("x-oauth-scopes", "")
    scopes = [s.strip() for s in scopes_raw.split(",") if s.strip()]
    return UserProfile(
        login=str(data.get("login", "")),
        name=data.get("name"),
        email=data.get("email"),
        bio=data.get("bio"),
        public_repos=int(data.get("public_repos", 0)),
        followers=int(data.get("followers", 0)),
        following=int(data.get("following", 0)),
        created_at=str(data.get("created_at", "")),
        html_url=str(data.get("html_url", "")),
        scopes=scopes,
    )
