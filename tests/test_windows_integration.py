"""Ephemeral Windows Credential Manager CI smoke; no real production secrets."""
import sys
import unittest
import uuid
from skelllang.windows_keys import SERVICE, WindowsCredentialVault


@unittest.skipUnless(sys.platform == "win32", "Windows only")
class WindowsIntegrationTests(unittest.TestCase):
    def test_windows_credential_manager_roundtrip(self):
        vault = WindowsCredentialVault()
        key_id = "ci-" + uuid.uuid4().hex
        try:
            vault.create(key_id)
            self.assertEqual(len(vault.resolve(key_id)), 32)
            with self.assertRaises(Exception):
                vault.create(key_id)
        finally:
            vault._backend.delete_password(SERVICE, key_id)


if __name__ == "__main__":
    unittest.main()
