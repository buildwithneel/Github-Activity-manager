"""GitHub repository listing and creation via REST API."""

from dataclasses import dataclass

from github_activity_generator.github.client import GitHubClient


@dataclass
class GitHubRepository:
    """Metadata for a GitHub repository."""

    name: str
    full_name: str
    owner: str
    private: bool
    description: str
    html_url: str
    clone_url: str
    ssh_url: str
    default_branch: str


class RepositoryAPI:
    """Manages GitHub repositories via authenticated REST API calls."""

    def __init__(self, client: GitHubClient) -> None:
        self.client = client

    def list_repositories(self, per_page: int = 50) -> list[GitHubRepository]:
        """List repositories accessible to the authenticated user."""
        data, _ = self.client.get(
            "/user/repos",
            params={"sort": "updated", "per_page": min(100, max(1, per_page))},
        )
        if not isinstance(data, list):
            return []
        return [self._to_repo(item) for item in data]

    def create_repository(
        self,
        name: str,
        *,
        description: str = "",
        private: bool = False,
        auto_init: bool = False,
    ) -> GitHubRepository:
        """Create a new GitHub repository under the authenticated user's account."""
        payload = {
            "name": name.strip(),
            "description": description.strip(),
            "private": private,
            "auto_init": auto_init,
        }
        data, _ = self.client.post("/user/repos", json_body=payload)
        return self._to_repo(data)

    @staticmethod
    def _to_repo(item: dict) -> GitHubRepository:
        owner_obj = item.get("owner") or {}
        return GitHubRepository(
            name=str(item.get("name", "")),
            full_name=str(item.get("full_name", "")),
            owner=str(owner_obj.get("login", "")),
            private=bool(item.get("private", False)),
            description=str(item.get("description") or ""),
            html_url=str(item.get("html_url", "")),
            clone_url=str(item.get("clone_url", "")),
            ssh_url=str(item.get("ssh_url", "")),
            default_branch=str(item.get("default_branch") or "main"),
        )
