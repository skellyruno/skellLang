"""Authorized in-memory compile and safe encrypted-file workflow."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from skelllang import compile_source
from skelllang.cipher import (CipherError, compile_encrypted, compile_encrypted_file,
                             encrypt_file, encrypt_source, rotate_file)

SOURCE = b"skell 1\ncanvas 440 310\nfx saturate warmth 2.5 off\n"
OLD = bytes(range(32))
NEW = bytes(range(32, 64))


class CompilerIntegrationTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.source = self.root / "secret.skell"
        self.source.write_bytes(SOURCE)
        self.resolver = lambda key_id: {"old": OLD, "new": NEW}[key_id]

    def test_encrypted_compile_same_as_existing_plaintext_model(self):
        blob = encrypt_source(SOURCE, "old", OLD)
        self.assertEqual(compile_encrypted(blob, self.resolver),
                         compile_source(SOURCE.decode()))

    def test_file_workflow_is_exclusive_and_has_no_plaintext_staging(self):
        protected = self.root / "secret.skellenc"
        encrypt_file(self.source, protected, "old", OLD)
        self.assertEqual(compile_encrypted_file(protected, self.resolver),
                         compile_source(SOURCE.decode()))
        self.assertEqual(self.source.read_bytes(), SOURCE)
        self.assertNotIn(SOURCE, protected.read_bytes())
        self.assertEqual(set(x.name for x in self.root.iterdir()),
                         {"secret.skell", "secret.skellenc"})
        with self.assertRaisesRegex(CipherError, "overwrite"):
            encrypt_file(self.source, protected, "old", OLD)
        rotated = self.root / "rotated.skellenc"
        rotate_file(protected, rotated, self.resolver, "new", NEW)
        self.assertEqual(compile_encrypted_file(rotated, self.resolver),
                         compile_source(SOURCE.decode()))
        self.assertNotEqual(protected.read_bytes(), rotated.read_bytes())

    def test_source_diagnostic_cannot_echo_invalid_secret(self):
        blob = encrypt_source(b"skell 1\nvery-private-internal-token\n", "old", OLD)
        with self.assertRaises(CipherError) as err:
            compile_encrypted(blob, self.resolver)
        self.assertNotIn("very-private-internal-token", str(err.exception))
        self.assertIn("withheld", str(err.exception))

    def test_invalid_plaintext_rejected_before_creating_output(self):
        self.source.write_bytes(b"skell 1\nvery-private-internal-token\n")
        target = self.root / "not-written.skellenc"
        with self.assertRaises(CipherError) as err:
            encrypt_file(self.source, target, "old", OLD)
        self.assertFalse(target.exists())
        self.assertNotIn("very-private-internal-token", str(err.exception))

    def test_symlinks_fail_closed(self):
        link = self.root / "linked.skell"
        try:
            link.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable")
        with self.assertRaises(CipherError):
            encrypt_file(link, self.root / "blocked.skellenc", "old", OLD)


if __name__ == "__main__":
    unittest.main()
