"""Offline SkellCipher recovery tests: published dummy key material only."""
import json
import struct
import tempfile
import unittest
from pathlib import Path

from skelllang.cipher import CipherError
from skelllang.recovery import (MAGIC, backup_to_file, create_backup,
                                restore_backup, restore_from_file)

TEST_KEY = bytes(range(32))
SECRET = "example-only-random-seed-text-no-real-secret-2026!"
BAD_SECRET = "wrong-example-only-random-text-recovery-key-2026"


class RecoveryTests(unittest.TestCase):
    def test_recovery_roundtrip(self):
        blob = create_backup("example1", TEST_KEY, SECRET)
        self.assertEqual(restore_backup(blob, SECRET), ("example1", TEST_KEY))
        self.assertNotIn(TEST_KEY, blob)
        self.assertNotIn(SECRET.encode(), blob)

    def test_wrong_passphrase_and_modified_ciphertext_reject(self):
        blob = create_backup("example1", TEST_KEY, SECRET)
        with self.assertRaises(CipherError):
            restore_backup(blob, BAD_SECRET)
        changed = bytearray(blob)
        changed[-1] ^= 0x10
        with self.assertRaises(CipherError):
            restore_backup(bytes(changed), SECRET)

    def test_authenticated_header_prevents_key_id_change(self):
        blob = create_backup("example1", TEST_KEY, SECRET)
        length = struct.unpack(">H", blob[len(MAGIC):len(MAGIC) + 2])[0]
        start = len(MAGIC) + 2
        header = json.loads(blob[start:start + length])
        header["kid"] = "example2"
        raw = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
        changed = MAGIC + struct.pack(">H", len(raw)) + raw + blob[start + length:]
        with self.assertRaises(CipherError):
            restore_backup(changed, SECRET)

    def test_kdf_cost_version_and_truncation_rejected_before_work(self):
        blob = create_backup("example1", TEST_KEY, SECRET)
        length = struct.unpack(">H", blob[len(MAGIC):len(MAGIC) + 2])[0]
        start = len(MAGIC) + 2
        header = json.loads(blob[start:start + length])
        header["n"] = 1 << 28
        raw = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
        for value in (b"", blob[:-1], MAGIC,
                      MAGIC + struct.pack(">H", len(raw)) + raw + blob[start + length:]):
            with self.subTest(length=len(value)), self.assertRaises(CipherError):
                restore_backup(value, SECRET)

    def test_passphrase_constraints_and_key_length(self):
        with self.assertRaises(CipherError):
            create_backup("example1", TEST_KEY, "short")
        with self.assertRaises(CipherError):
            create_backup("example1", TEST_KEY[:16], SECRET)

    def test_exclusive_backup_creation_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backup.skellbackup"
            backup_to_file(path, "example1", TEST_KEY, SECRET)
            self.assertEqual(restore_from_file(path, SECRET), ("example1", TEST_KEY))
            with self.assertRaises(CipherError):
                backup_to_file(path, "example1", TEST_KEY, SECRET)
            self.assertEqual({p.name for p in Path(directory).iterdir()}, {"backup.skellbackup"})


if __name__ == "__main__":
    unittest.main()
