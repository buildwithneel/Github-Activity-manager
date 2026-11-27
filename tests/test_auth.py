"""Tests for authentication (PAT, OAuth Device Flow, SessionManager, error handling)."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from github_activity_generator.auth.oauth import DeviceFlowChallenge, OAuthDeviceFlowAuthenticator
from github_activity_generator.auth.pat import PATAuthenticator
from github_activity_generator.auth.session import SessionManager
from github_activity_generator.exceptions import AuthenticationError, RateLimitError
from github_activity_generator.github.client import GitHubClient
from github_activity_generator.storage.keyring_store import KeyringStore


def _mock_response(status_code: int, payload: dict, headers: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    resp.text = str(payload)
    resp.headers = headers or {}
    return resp


class TestAuth(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.cred_file = Path(self.tmp.name) / ".credentials"
        self.keyring = KeyringStore(fallback_file=self.cred_file, service_name="test-auth")
        self.keyring._keyring = None
        self.session = SessionManager(self.keyring)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_pat_empty_or_short_rejected(self) -> None:
        auth = PATAuthenticator(self.session)
        with self.assertRaises(AuthenticationError):
            auth.authenticate("")
        with self.assertRaises(AuthenticationError):
            auth.authenticate("short")

    @patch("github_activity_generator.github.client.requests.Session.request")
    def test_pat_success_and_logout(self, mock_req: MagicMock) -> None:
        mock_req.return_value = _mock_response(
            200,
            {
                "login": "octocat",
                "name": "The Octocat",
                "email": None,
                "bio": "Mascot",
                "public_repos": 8,
                "followers": 100,
                "following": 5,
                "created_at": "2011-01-25T18:44:36Z",
                "html_url": "https://github.com/octocat",
            },
            headers={"X-OAuth-Scopes": "read:user, repo"},
        )
        auth = PATAuthenticator(self.session)
        profile = auth.authenticate("ghp_validtoken123456789")
        self.assertEqual(profile.login, "octocat")
        self.assertEqual(profile.scopes, ["read:user", "repo"])
        self.assertTrue(self.session.has_stored_credentials())

        status = self.session.validate_session()
        self.assertTrue(status.authenticated)
        self.assertEqual(status.username, "octocat")
        self.assertEqual(status.auth_method, "pat")

        self.session.logout()
        self.assertFalse(self.session.has_stored_credentials())
        self.assertFalse(self.session.validate_session().authenticated)

    @patch("github_activity_generator.github.client.requests.Session.request")
    def test_invalid_token_and_rate_limit(self, mock_req: MagicMock) -> None:
        client = GitHubClient(token="ghp_expired123456")
        mock_req.return_value = _mock_response(401, {"message": "Bad credentials"})
        with self.assertRaises(AuthenticationError):
            client.get("/user")

        mock_req.return_value = _mock_response(
            403,
            {"message": "API rate limit exceeded"},
            headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000000"},
        )
        with self.assertRaises(RateLimitError) as ctx:
            client.get("/user")
        self.assertEqual(ctx.exception.reset_timestamp, 1700000000)

    @patch("github_activity_generator.github.client.requests.Session.request")
    @patch("github_activity_generator.auth.oauth.requests.post")
    def test_oauth_device_flow_success(
        self, mock_post: MagicMock, mock_api_req: MagicMock
    ) -> None:
        mock_post.side_effect = [
            _mock_response(
                200,
                {
                    "device_code": "dev123",
                    "user_code": "ABCD-1234",
                    "verification_uri": "https://github.com/login/device",
                    "expires_in": 60,
                    "interval": 1,
                },
            ),
            _mock_response(200, {"error": "authorization_pending"}),
            _mock_response(200, {"access_token": "gho_oauth_token_123456"}),
        ]
        mock_api_req.return_value = _mock_response(
            200,
            {"login": "oauth_user", "public_repos": 2, "followers": 1, "following": 1},
            headers={"X-OAuth-Scopes": "read:user"},
        )

        oauth = OAuthDeviceFlowAuthenticator(self.session, client_id="Iv1.1234567890")
        challenge = oauth.request_device_code()
        self.assertIsInstance(challenge, DeviceFlowChallenge)
        self.assertEqual(challenge.user_code, "ABCD-1234")

        profile = oauth.poll_for_token(challenge, sleep_fn=lambda _: None)
        self.assertEqual(profile.login, "oauth_user")
        self.assertEqual(self.session.get_auth_method(), "oauth")


if __name__ == "__main__":
    unittest.main()
