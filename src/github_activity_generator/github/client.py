"""Centralized GitHub REST and GraphQL HTTP client with safe error handling."""

from typing import Any

import requests

from github_activity_generator.constants import GITHUB_API_URL, GITHUB_GRAPHQL_URL
from github_activity_generator.exceptions import (
    AuthenticationError,
    GitHubAPIError,
    NetworkError,
    PermissionError_,
    RateLimitError,
)


class GitHubClient:
    """HTTP client for GitHub REST and GraphQL APIs."""

    def __init__(
        self,
        token: str | None = None,
        api_url: str = GITHUB_API_URL,
        graphql_url: str = GITHUB_GRAPHQL_URL,
        timeout: int = 20,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.graphql_url = graphql_url
        self.timeout = timeout
        self._session = requests.Session()
        self._session.verify = True  # Never disable SSL verification
        self._session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "GitHub-Activity-Generator/1.0.0",
            }
        )
        if token:
            self.set_token(token)

    def set_token(self, token: str | None) -> None:
        """Update or clear the bearer token on the HTTP session."""
        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"
        else:
            self._session.headers.pop("Authorization", None)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[Any, dict[str, str]]:
        """Execute a GitHub REST API request and return parsed JSON + headers."""
        url = path if path.startswith("https://") else f"{self.api_url}/{path.lstrip('/')}"
        try:
            response = self._session.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_body,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise NetworkError(f"Network error communicating with GitHub: {exc}") from exc

        self._raise_for_status(response)
        headers = {k.lower(): v for k, v in response.headers.items()}
        if response.status_code == 204 or not response.text.strip():
            return {}, headers
        try:
            return response.json(), headers
        except ValueError as exc:
            raise GitHubAPIError("GitHub returned an invalid JSON response.") from exc

    def get(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> tuple[Any, dict[str, str]]:
        return self.request("GET", path, params=params)

    def post(
        self, path: str, *, json_body: dict[str, Any] | None = None
    ) -> tuple[Any, dict[str, str]]:
        return self.request("POST", path, json_body=json_body)

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GitHub GraphQL query and return the 'data' payload."""
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        try:
            response = self._session.post(
                self.graphql_url,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise NetworkError(f"Network error communicating with GitHub GraphQL: {exc}") from exc

        self._raise_for_status(response)
        try:
            body = response.json()
        except ValueError as exc:
            raise GitHubAPIError("GitHub GraphQL returned invalid JSON.") from exc

        if "errors" in body and body["errors"]:
            messages = "; ".join(
                str(err.get("message", "Unknown GraphQL error")) for err in body["errors"]
            )
            raise GitHubAPIError(f"GitHub GraphQL error: {messages}")

        data = body.get("data")
        if not isinstance(data, dict):
            raise GitHubAPIError("GitHub GraphQL response missing 'data' field.")
        return data

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        if 200 <= response.status_code < 300:
            return

        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_raw = response.headers.get("X-RateLimit-Reset")
        reset_ts = int(reset_raw) if reset_raw and reset_raw.isdigit() else None

        message = ""
        try:
            err_json = response.json()
            if isinstance(err_json, dict):
                message = str(err_json.get("message", ""))
        except ValueError:
            message = response.text[:200]

        if response.status_code == 401:
            raise AuthenticationError(
                message or "Authentication failed or token has expired. Please log in again."
            )
        if response.status_code == 403 and remaining == "0":
            raise RateLimitError(
                "GitHub API rate limit exceeded. Please wait before retrying.",
                reset_timestamp=reset_ts,
            )
        if response.status_code == 403:
            raise PermissionError_(
                message or "Insufficient GitHub token permissions for this operation."
            )
        if response.status_code == 404:
            raise GitHubAPIError(message or "Requested GitHub resource was not found.")
        if response.status_code == 422:
            raise GitHubAPIError(message or "GitHub rejected the request parameters (422).")
        raise GitHubAPIError(
            f"GitHub API error ({response.status_code}): {message or 'Unknown error'}"
        )
