"""Windows Credential Manager: root key storage for SkellCipher.

Never allows plaintext keyrings, file backends or unverified providers.
No production key values appear in compiler code, tests, logs or command args.
"""
from __future__ import annotations

import base64
import hmac
import os
import sys

from .cipher import CipherError, KEY_BYTES, _key, _key_id

SERVICE = "Skelly.SkellCipher.SourceKey.v1"


class KeyStoreError(CipherError):
    """Credential failures intentionally omit all private key contents."""


class WindowsCredentialVault:
    """Windows Credential Manager backend. No fallback to plaintext storage."""

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise KeyStoreError("Windows Credential Manager is required")
        try:
            import keyring
            from keyring.backends.Windows import WinVaultKeyring
            backend = keyring.get_keyring()
            if not isinstance(backend, WinVaultKeyring):
                raise KeyStoreError("A verified Windows Credential Manager backend is required")
            self._backend = backend
        except KeyStoreError:
            raise
        except Exception:
            raise KeyStoreError("Windows Credential Manager is unavailable") from None

    def resolve(self, key_id: str) -> bytes:
        _key_id(key_id)
        try:
            value = self._backend.get_password(SERVICE, key_id)
            if not isinstance(value, str):
                raise KeyStoreError("Authorized encryption key is unavailable")
            return _key(base64.b64decode(value, validate=True))
        except Exception:
            raise KeyStoreError("Authorized encryption key is unavailable") from None

    def create(self, key_id: str) -> None:
        """Create an OS-vault key with no printing or implicit export.

        Immediately create and verify an offline recovery backup before use.
        """
        _key_id(key_id)
        try:
            if self._backend.get_password(SERVICE, key_id) is not None:
                raise KeyStoreError("Key identifier already exists")
            secret = os.urandom(KEY_BYTES)
            self._backend.set_password(SERVICE, key_id,
                                       base64.b64encode(secret).decode("ascii"))
            if not hmac.compare_digest(self.resolve(key_id), secret):
                raise KeyStoreError("Key-store verification failed")
        except KeyStoreError:
            raise
        except Exception:
            raise KeyStoreError("Windows Credential Manager key creation failed") from None

    def import_key(self, key_id: str, master_key: bytes) -> None:
        """Restore an authenticated offline backup to a previously unused ID."""
        try:
            _key_id(key_id)
            _key(master_key)
        except CipherError:
            raise KeyStoreError("Invalid restored key") from None
        try:
            if self._backend.get_password(SERVICE, key_id) is not None:
                raise KeyStoreError("Key identifier already exists")
            self._backend.set_password(SERVICE, key_id,
                                       base64.b64encode(master_key).decode("ascii"))
            if not hmac.compare_digest(self.resolve(key_id), master_key):
                raise KeyStoreError("Restored key verification failed")
        except KeyStoreError:
            raise
        except Exception:
            raise KeyStoreError("Windows Credential Manager restore failed") from None
