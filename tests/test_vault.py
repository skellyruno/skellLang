"""Only Windows Credential Manager may persist SkellCipher master keys."""
import base64
import sys
import types
import unittest
from unittest.mock import patch

from skelllang.windows_keys import KeyStoreError, WindowsCredentialVault, SERVICE


class MockWindowsBackend:
    def __init__(self):
        self.entries = {}

    def get_password(self, service, name):
        return self.entries.get((service, name))

    def set_password(self, service, name, value):
        self.entries[(service, name)] = value


class VaultTests(unittest.TestCase):
    def test_unsupported_platform_rejects(self):
        with patch("skelllang.windows_keys.sys.platform", "linux"):
            with self.assertRaisesRegex(KeyStoreError, "Windows Credential Manager"):
                WindowsCredentialVault()

    def test_mock_windows_vault_generation_retrieval_and_duplicate_rejection(self):
        backend = MockWindowsBackend()
        windows = types.ModuleType("keyring.backends.Windows")
        windows.WinVaultKeyring = MockWindowsBackend
        library = types.ModuleType("keyring")
        library.get_keyring = lambda: backend
        parent = types.ModuleType("keyring.backends")
        parent.Windows = windows
        with patch("skelllang.windows_keys.sys.platform", "win32"), patch.dict(
                sys.modules, {"keyring": library, "keyring.backends": parent,
                              "keyring.backends.Windows": windows}):
            vault = WindowsCredentialVault()
            vault.create("test-001")
            secret = vault.resolve("test-001")
            self.assertEqual(len(secret), 32)
            self.assertEqual(base64.b64decode(backend.entries[(SERVICE, "test-001")]), secret)
            with self.assertRaisesRegex(KeyStoreError, "already exists"):
                vault.create("test-001")
            with self.assertRaises(KeyStoreError):
                vault.resolve("unknown")
            backend.entries[(SERVICE, "bad-key")] = "not base64!"
            with self.assertRaises(KeyStoreError):
                vault.resolve("bad-key")

    def test_unapproved_backend_denied(self):
        windows = types.ModuleType("keyring.backends.Windows")
        windows.WinVaultKeyring = MockWindowsBackend
        library = types.ModuleType("keyring")
        library.get_keyring = lambda: object()
        parent = types.ModuleType("keyring.backends")
        parent.Windows = windows
        with patch("skelllang.windows_keys.sys.platform", "win32"), patch.dict(
                sys.modules, {"keyring": library, "keyring.backends": parent,
                              "keyring.backends.Windows": windows}):
            with self.assertRaisesRegex(KeyStoreError, "verified"):
                WindowsCredentialVault()


if __name__ == "__main__":
    unittest.main()
