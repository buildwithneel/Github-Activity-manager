"""GitHub OAuth 2.0 Device Flow authentication (no client secret embedded)."""

import time
import webbrowser
from dataclasses import dataclass
from typing import Callable

import requests

from github_activity_generator.auth.session import SessionManager
from github_activity_generator.constants import (
    GITHUB_DEVICE_CODE_URL,
    GITHUB_OAUTH_SCOPES,
    GITHUB_OAUTH_TOKEN_URL,
)
from github_activity_generator.exceptions import AuthenticationError, NetworkError
from github_activity_generator.github.client import GitHubClient
from github_activity_generator.github.profile import UserProfile, fetch_user_profile


@dataclass
class DeviceFlowChallenge:
    """Device authorization response returned by GitHub."""

    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


class OAuthDeviceFlowAuthenticator:
    """Implements GitHub OAuth Device Flow without any embedded client secret."""

    def __init__(
        self,
        session_manager: SessionManager,
        client_id: str,
        scopes: str = GITHUB_OAUTH_SCOPES,
        timeout: int = 20,
    ) -> None:
        self.session_manager = session_manager
        self.client_id = client_id.strip()
        self.scopes = scopes
        self.timeout = timeout

    def request_device_code(self) -> DeviceFlowChallenge:
        """Request a device and user verification code from GitHub."""
        if not self.client_id:
            raise AuthenticationError(
                "GitHub OAuth Client ID is required. Configure your OAuth App Client ID in Settings or provide it now."
            )
        try:
            response = requests.post(
                GITHUB_DEVICE_CODE_URL,
                data={"client_id": self.client_id, "scope": self.scopes},
                headers={"Accept": "application/json"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise NetworkError(f"Failed to contact GitHub OAuth endpoint: {exc}") from exc

        if response.status_code != 200:
            raise AuthenticationError(
                f"GitHub rejected OAuth device code request (HTTP {response.status_code})."
            )

        payload = response.json()
        if "error" in payload:
            raise AuthenticationError(
                payload.get("error_description") or payload.get("error") or "OAuth initialization failed."
            )

        return DeviceFlowChallenge(
            device_code=str(payload["device_code"]),
            user_code=str(payload["user_code"]),
            verification_uri=str(payload["verification_uri"]),
            expires_in=int(payload.get("expires_in", 900)),
            interval=int(payload.get("interval", 5)),
        )

    def open_browser(self, verification_uri: str) -> bool:
        """Attempt to open the verification URI in the user's default browser."""
        try:
            return bool(webbrowser.open(verification_uri))
        except Exception:
            return False

    def poll_for_token(
        self,
        challenge: DeviceFlowChallenge,
        *,
        on_poll: Callable[[], None] | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> UserProfile:
        """Poll GitHub until the user completes authorization or the code expires."""
        interval = max(1, challenge.interval)
        deadline = time.monotonic() + challenge.expires_in

        while time.monotonic() < deadline:
            sleep_fn(interval)
            if on_poll:
                on_poll()

            try:
                response = requests.post(
                    GITHUB_OAUTH_TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "device_code": challenge.device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    headers={"Accept": "application/json"},
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise NetworkError(f"Network error while polling OAuth token: {exc}") from exc

            payload = response.json()
            if "access_token" in payload:
                token = str(payload["access_token"])
                client = GitHubClient(token=token)
                profile = fetch_user_profile(client)
                self.session_manager.save_session(token, "oauth", profile)
                return profile

            error = payload.get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval += 5
                continue
            if error == "expired_token":
                raise AuthenticationError("OAuth device code expired. Please try logging in again.")
            if error == "access_denied":
                raise AuthenticationError("OAuth authorization was cancelled by the user.")
            raise AuthenticationError(
                payload.get("error_description") or f"OAuth error: {error or 'unknown'}"
            )

        raise AuthenticationError("OAuth authorization timed out before completion.")
