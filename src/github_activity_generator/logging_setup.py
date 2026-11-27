"""Safe local logging setup that redacts sensitive tokens."""

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path


class TokenRedactingFilter(logging.Filter):
    """Redact GitHub tokens and Authorization headers from log records."""

    TOKEN_PATTERN = re.compile(
        r"(gh[pousr]_[A-Za-z0-9_]{10,}|github_pat_[A-Za-z0-9_]{10,}|Bearer\s+[A-Za-z0-9\-._~+/]+=*)"
    )

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.TOKEN_PATTERN.sub("[REDACTED]", record.msg)
        if record.args:
            sanitized = []
            for arg in record.args if isinstance(record.args, tuple) else (record.args,):
                if isinstance(arg, str):
                    sanitized.append(self.TOKEN_PATTERN.sub("[REDACTED]", arg))
                else:
                    sanitized.append(arg)
            record.args = tuple(sanitized)
        return True


def setup_logging(logs_dir: Path, level: str = "INFO") -> logging.Logger:
    """Configure rotating file logging without leaking secrets."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("github_activity_generator")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    if not logger.handlers:
        log_file = logs_dir / "app.log"
        handler = RotatingFileHandler(
            log_file, maxBytes=1_048_576, backupCount=3, encoding="utf-8"
        )
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        handler.addFilter(TokenRedactingFilter())
        logger.addHandler(handler)

    return logger
