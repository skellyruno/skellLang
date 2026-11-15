"""Ephemeral actual Windows Credential Manager backup/recovery smoke test."""
import sys
import unittest
import uuid
from skelllang.windows_keys import SERVICE, WindowsCredentialVault
from skelllang.recovery import create_backup, restore_backup

PASSWORD = "only-for-public-CI-dummy-recovery-2026-test!"


@unittest.skipUnless(sys.platform == "win32", "Windows only")
class WindowsIntegrationTests(unittest.TestCase):
    def test_windows_credential_manager_loss_and_recovery(self):
        vault = WindowsCredentialVault()
        key_id = "ci-" + uuid.uuid4().hex
        try:
            vault.create(key_id)
            original = vault.resolve(key_id)
            backup = create_backup(key_id, original, PASSWORD)
            with self.assertRaises(Exception):
                vault.create(key_id)
            vault._backend.delete_password(SERVICE, key_id)
            restored_id, recovered = restore_backup(backup, PASSWORD)
            vault.import_key(restored_id, recovered)
            self.assertEqual(vault.resolve(key_id), original)
        finally:
            try:
                vault._backend.delete_password(SERVICE, key_id)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
