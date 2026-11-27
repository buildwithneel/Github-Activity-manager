"""Application configuration dataclasses and path management."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from github_activity_generator.constants import (
    CACHE_DIRNAME,
    CONFIG_FILENAME,
    CREDENTIALS_FILENAME,
    DB_FILENAME,
    DEFAULT_DATA_DIR,
    EXPORTS_DIRNAME,
    LOGS_DIRNAME,
)


@dataclass
class AppPaths:
    """Resolved local filesystem paths for application data."""

    root: Path = field(default_factory=lambda: DEFAULT_DATA_DIR)

    @property
    def config_file(self) -> Path:
        return self.root / CONFIG_FILENAME

    @property
    def db_file(self) -> Path:
        return self.root / DB_FILENAME

    @property
    def logs_dir(self) -> Path:
        return self.root / LOGS_DIRNAME

    @property
    def exports_dir(self) -> Path:
        return self.root / EXPORTS_DIRNAME

    @property
    def cache_dir(self) -> Path:
        return self.root / CACHE_DIRNAME

    @property
    def credentials_file(self) -> Path:
        return self.root / CREDENTIALS_FILENAME

    def ensure_dirs(self) -> None:
        """Create required local directories if they do not exist."""
        self.root.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class GenerationConfig:
    """Configuration for activity planning and distribution."""

    start_date: str | None = None
    end_date: str | None = None
    min_commits_per_day: int = 1
    max_commits_per_day: int = 5
    exact_daily_target: int | None = None
    average_daily_target: float | None = None
    weekly_target: int | None = None
    monthly_target: int | None = None
    total_target: int | None = None
    pattern: str = "consistent"
    exclude_weekends: bool = False
    enabled_weekdays: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])
    excluded_dates: list[str] = field(default_factory=list)
    random_seed: int | None = 42
    custom_weights: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GenerationConfig":
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class AppSettings:
    """User preferences stored in local config.json (never secrets)."""

    theme: str = "dark"
    timezone: str = "UTC"
    default_date_range_days: int = 365
    default_pattern: str = "consistent"
    exclude_weekends_default: bool = False
    selected_repo_full_name: str | None = None
    selected_repo_local_path: str | None = None
    oauth_client_id: str | None = None
    log_level: str = "INFO"
    default_export_format: str = "json"
    generation: GenerationConfig = field(default_factory=GenerationConfig)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        gen_data = data.get("generation", {})
        generation = (
            GenerationConfig.from_dict(gen_data)
            if isinstance(gen_data, dict)
            else GenerationConfig()
        )
        valid_keys = {
            f.name for f in cls.__dataclass_fields__.values() if f.name != "generation"
        }
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered, generation=generation)
