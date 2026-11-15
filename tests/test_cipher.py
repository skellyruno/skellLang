"""SkellCipher 0.1: authenticated encryption regression tests."""
import json
import struct
import unittest

from skelllang.cipher import (
    ALGORITHM, MAGIC, MAX_ENVELOPE, MAX_SOURCE, CipherError, _unpack,
    decrypt_source, encrypt_source, rotate_source,
)

SOURCE = b"skell 1\nfx saturate warmth 2.5 off\n"
KEY1 = bytes(range(32))  # published dummy test material only
KEY2 = bytes(range(32, 64))


def provider(**keys):
    return lambda key_id: keys[key_id]


class CipherTests(unittest.TestCase):
    def setUp(self):
        self.blob = encrypt_source(SOURCE, "version-one", KEY1)

    def test_roundtrip_and_authenticated_metadata(self):
        self.assertEqual(decrypt_source(self.blob, provider(**{"version-one": KEY1})), SOURCE)
        meta, aad, ciphertext = _unpack(self.blob)
        self.assertEqual(meta["v"], 1)
        self.assertEqual(meta["alg"], ALGORITHM)
        self.assertEqual(meta["kid"], "version-one")
        self.assertTrue(aad.startswith(MAGIC))
        self.assertNotIn(SOURCE, self.blob)
        self.assertNotIn(KEY1, self.blob)
        self.assertNotEqual(ciphertext, SOURCE)

    def test_random_file_key_salts_and_nonces(self):
        second = encrypt_source(SOURCE, "version-one", KEY1)
        a, _, _ = _unpack(self.blob)
        b, _, _ = _unpack(second)
        self.assertNotEqual(self.blob, second)
        self.assertNotEqual(a["nonce"], b["nonce"])
        self.assertNotEqual(a["salt"], b["salt"])

    def test_mutated_metadata_and_ciphertext_rejected(self):
        original, aad, ciphertext = _unpack(self.blob)
        for field, value in (("kid", "version-two"), ("alg", "AES-256-GCM"),
                             ("v", 2), ("nonce", "0" * 24),
                             ("salt", "0" * 64), ("ctype", "text/plain")):
            header = dict(original)
            header[field] = value
            raw = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
            forged = MAGIC + struct.pack(">H", len(raw)) + raw + ciphertext
            with self.subTest(field=field), self.assertRaises(CipherError):
                decrypt_source(forged, provider(**{"version-one": KEY1, "version-two": KEY1}))
        altered = bytearray(self.blob)
        altered[-1] ^= 0x80
        with self.assertRaises(CipherError):
            decrypt_source(bytes(altered), provider(**{"version-one": KEY1}))

    def test_wrong_missing_invalid_keys_redacted(self):
        for resolver in (provider(**{"version-one": KEY2}), provider(),
                         lambda kid: b"short", lambda kid: None,
                         lambda kid: (_ for _ in ()).throw(RuntimeError("PRIVATE PASSWORD"))):
            with self.subTest(resolver=resolver), self.assertRaises(CipherError) as context:
                decrypt_source(self.blob, resolver)
            self.assertNotIn("PRIVATE PASSWORD", str(context.exception))
            self.assertNotIn("version-one", str(context.exception))

    def test_noncanonical_duplicate_header_and_truncation(self):
        header, aad, ciphertext = _unpack(self.blob)
        damaged = [b"", b"skell 1", MAGIC, self.blob[:-1], self.blob[:-16],
                   self.blob + b"padding" * 6000, self.blob.replace(MAGIC, b"BADMAGIC\x00", 1)]
        dup = aad[len(MAGIC) + 2:-1] + b',"v":1}'
        damaged.append(MAGIC + struct.pack(">H", len(dup)) + dup + ciphertext)
        damaged.append(MAGIC + b"\xff\xff" + aad[len(MAGIC) + 2:] + ciphertext)
        for blob in damaged:
            with self.subTest(size=len(blob)), self.assertRaises(CipherError):
                decrypt_source(blob, provider(**{"version-one": KEY1}))

    def test_invalid_identifiers_non_utf8_oversize(self):
        for kid in ("", "../../etc/passwd", "space here", "a" * 65, "ö"):
            with self.subTest(kid=kid), self.assertRaises(CipherError):
                encrypt_source(SOURCE, kid, KEY1)
        for bad in (b"skell 1\n\xff", b"x" * (MAX_SOURCE + 1)):
            with self.assertRaises(CipherError):
                encrypt_source(bad, "safe", KEY1)
        with self.assertRaises(CipherError):
            encrypt_source(SOURCE, "safe", KEY1[:-1])

    def test_key_rotation_preserves_original_and_new_key_required(self):
        before = self.blob
        rotated = rotate_source(before, provider(**{"version-one": KEY1}),
                                "version-two", KEY2)
        self.assertEqual(self.blob, before)
        self.assertNotEqual(before, rotated)
        self.assertEqual(decrypt_source(rotated, provider(**{"version-two": KEY2})), SOURCE)
        with self.assertRaises(CipherError):
            decrypt_source(rotated, provider(**{"version-two": KEY1}))
        with self.assertRaises(CipherError):
            rotate_source(before, provider(**{"version-one": KEY1}), "version-one", KEY2)
        with self.assertRaises(CipherError):
            rotate_source(before, provider(**{"version-one": KEY2}), "version-two", KEY2)

    def test_invalid_binary_types_and_size(self):
        for invalid in (None, "plain text", b"x" * (MAX_ENVELOPE + 1)):
            with self.assertRaises(CipherError):
                decrypt_source(invalid, provider(**{"version-one": KEY1}))


if __name__ == "__main__":
    unittest.main()
