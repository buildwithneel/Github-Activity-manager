"""Application-wide constants and defaults."""

from pathlib import Path

APP_NAME = "GITHUB ACTIVITY GENERATOR"
APP_VERSION = "1.0.0"
KEYRING_SERVICE_NAME = "github-activity-generator"
KEYRING_TOKEN_KEY = "github_access_token"
KEYRING_AUTH_METHOD_KEY = "github_auth_method"
KEYRING_OAUTH_CLIENT_ID_KEY = "github_oauth_client_id"

DEFAULT_DATA_DIR = Path.home() / ".github-activity-generator"
CONFIG_FILENAME = "config.json"
DB_FILENAME = "activity.db"
LOGS_DIRNAME = "logs"
EXPORTS_DIRNAME = "exports"
CACHE_DIRNAME = "cache"
CREDENTIALS_FILENAME = ".credentials"

GITHUB_API_URL = "https://api.github.com"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_OAUTH_SCOPES = "read:user repo"

ACTIVITY_FILENAME = "activity.txt"
ACTIVITY_SECTION_START = "# --- GITHUB ACTIVITY GENERATOR LOG ---"
ACTIVITY_SECTION_END = "# --- END GITHUB ACTIVITY GENERATOR LOG ---"

WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

ACTIVITY_PATTERNS = [
    "consistent",
    "random",
    "weekday_focused",
    "weekend_focused",
    "increasing",
    "decreasing",
    "sprint",
    "break_based",
    "custom",
]

GITHUB_GREEN_PALETTE = [
    "#161b22",  # level 0 (empty)
    "#0e4429",  # level 1
    "#006d32",  # level 2
    "#26a641",  # level 3
    "#39d353",  # level 4
]
