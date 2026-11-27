"""JSON configuration persistence without storing secrets."""

import json
from pathlib import Path
from typing import Any

from github_activity_generator.config import AppPaths, AppSettings, GenerationConfig
from github_activity_generator.exceptions import StorageError

FORBIDDEN_SECRET_KEYS = {"token", "access_token", "pat", "password", "secret", "client_secret"}


class ConfigStore:
    """Manages reading and writing non-sensitive application configuration."""

    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def load(self) -> AppSettings:
        """Load settings from config.json, returning defaults if absent."""
        self.paths.ensure_dirs()
        if not self.paths.config_file.exists():
            settings = AppSettings()
            self.save(settings)
            return settings
        try:
            raw = self.paths.config_file.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                return AppSettings()
            return AppSettings.from_dict(data)
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"Failed to load configuration: {exc}") from exc

    def save(self, settings: AppSettings) -> None:
        """Persist settings to config.json, ensuring no secrets are written."""
        self.paths.ensure_dirs()
        payload = self._strip_secrets(settings.to_dict())
        try:
            self.paths.config_file.write_text(
                json.dumps(payload, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError as exc:
            raise StorageError(f"Failed to save configuration: {exc}") from exc

    def export_generation_config(self, config: GenerationConfig, target: Path) -> Path:
        """Export activity generation configuration to a JSON file."""
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = self._strip_secrets(config.to_dict())
            target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return target
        except OSError as exc:
            raise StorageError(f"Failed to export configuration: {exc}") from exc

    def import_generation_config(self, source: Path) -> GenerationConfig:
        """Import activity generation configuration from a JSON file."""
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise StorageError("Configuration file must contain a JSON object.")
            return GenerationConfig.from_dict(self._strip_secrets(data))
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"Failed to import configuration: {exc}") from exc

    @classmethod
    def _strip_secrets(cls, data: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for key, value in data.items():
            if key.lower() in FORBIDDEN_SECRET_KEYS:
                continue
            if isinstance(value, dict):
                cleaned[key] = cls._strip_secrets(value)
            else:
                cleaned[key] = value
        return cleaned
