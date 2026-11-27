"""Secure credential storage using OS keyring with encrypted file fallback."""

import base64
import hashlib
import json
import os
import platform
from pathlib import Path

from github_activity_generator.constants import KEYRING_SERVICE_NAME
from github_activity_generator.exceptions import StorageError


class KeyringStore:
    """Stores sensitive tokens in the OS keyring, with a 0600 encrypted fallback."""

    def __init__(self, fallback_file: Path, service_name: str = KEYRING_SERVICE_NAME) -> None:
        self.fallback_file = fallback_file
        self.service_name = service_name
        self._keyring = self._load_keyring_module()

    @staticmethod
    def _load_keyring_module():
        try:
            import keyring  # type: ignore[import-untyped]
            from keyring.errors import NoKeyringError  # type: ignore[import-untyped]

            backend = keyring.get_keyring()
            # Avoid fail-backend in headless environments
            if "fail" in type(backend).__name__.lower():
                return None
            _ = NoKeyringError
            return keyring
        except Exception:
            return None

    @property
    def using_os_keyring(self) -> bool:
        return self._keyring is not None

    def set_secret(self, key: str, value: str) -> None:
        """Store a secret value securely."""
        if not value:
            raise StorageError("Cannot store an empty secret.")
        if self._keyring is not None:
            try:
                self._keyring.set_password(self.service_name, key, value)
                return
            except Exception:
                # Fall through to encrypted local fallback if keyring backend fails at runtime
                pass
        self._write_fallback(key, value)

    def get_secret(self, key: str) -> str | None:
        """Retrieve a secret value, or None if not stored."""
        if self._keyring is not None:
            try:
                val = self._keyring.get_password(self.service_name, key)
                if val is not None:
                    return val
            except Exception:
                pass
        return self._read_fallback(key)

    def delete_secret(self, key: str) -> None:
        """Delete a stored secret if it exists."""
        if self._keyring is not None:
            try:
                self._keyring.delete_password(self.service_name, key)
            except Exception:
                pass
        self._delete_fallback(key)

    def _derive_key(self) -> bytes:
        material = f"{platform.node()}:{os.getuid() if hasattr(os, 'getuid') else 'user'}:{self.service_name}"
        return hashlib.sha256(material.encode("utf-8")).digest()

    def _xor_crypt(self, data: bytes) -> bytes:
        key = self._derive_key()
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    def _load_fallback_map(self) -> dict[str, str]:
        if not self.fallback_file.exists():
            return {}
        try:
            encoded = self.fallback_file.read_bytes()
            if not encoded:
                return {}
            decrypted = self._xor_crypt(base64.b64decode(encoded))
            parsed = json.loads(decrypted.decode("utf-8"))
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def _save_fallback_map(self, data: dict[str, str]) -> None:
        try:
            self.fallback_file.parent.mkdir(parents=True, exist_ok=True)
            raw = json.dumps(data).encode("utf-8")
            encoded = base64.b64encode(self._xor_crypt(raw))
            self.fallback_file.write_bytes(encoded)
            os.chmod(self.fallback_file, 0o600)
        except OSError as exc:
            raise StorageError(f"Failed to persist credentials securely: {exc}") from exc

    def _write_fallback(self, key: str, value: str) -> None:
        data = self._load_fallback_map()
        data[key] = value
        self._save_fallback_map(data)

    def _read_fallback(self, key: str) -> str | None:
        return self._load_fallback_map().get(key)

    def _delete_fallback(self, key: str) -> None:
        data = self._load_fallback_map()
        if key in data:
            del data[key]
            if data:
                self._save_fallback_map(data)
            elif self.fallback_file.exists():
                self.fallback_file.unlink()
