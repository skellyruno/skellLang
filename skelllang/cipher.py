"""SkellCipher 0.1: versioned, authenticated SkellLang source encryption.

This module implements authenticated encryption, NOT durable key management.
Keys are passed by an explicit authorized caller; no environment variables,
implicit fallbacks, key files, command-line key strings, or plaintext temp files.

Format: MAGIC | u16be header_length | canonical JSON header | AES-GCM body.
The complete prefix and header are authenticated as associated data.
"""
from __future__ import annotations

import json
import os
import re
import struct
from pathlib import Path
from typing import Callable

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

MAGIC = b"SKELLENC\x00"
VERSION = 1
ALGORITHM = "AES-256-GCM+HKDF-SHA256"
CONTENT_TYPE = "skell-source-utf8"
MAX_SOURCE = 32768
MAX_HEADER = 512
TAG_BYTES = 16
MAX_ENVELOPE = len(MAGIC) + 2 + MAX_HEADER + MAX_SOURCE + TAG_BYTES
KEY_BYTES = 32
NONCE_BYTES = 12
SALT_BYTES = 32
KEY_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z", re.ASCII)
FIELDS = frozenset(("v", "alg", "kid", "nonce", "salt", "ctype"))
BAD_ENVELOPE = "Invalid, corrupted, or unauthorized SkellCipher source"


class CipherError(ValueError):
    """Never includes keys, source text, or ciphertext in messages."""


def _key(value: bytes) -> bytes:
    if not isinstance(value, bytes) or len(value) != KEY_BYTES:
        raise CipherError("A 256-bit key is required")
    return value


def _key_id(value: str) -> str:
    if not isinstance(value, str) or not KEY_ID_RE.fullmatch(value):
        raise CipherError("Invalid key identifier")
    return value


def _canonical(header: dict) -> bytes:
    return json.dumps(header, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False).encode("ascii")


def _derive(master: bytes, salt: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=KEY_BYTES, salt=salt,
                info=b"SkellCipher/source/v1/aes-256-gcm").derive(master)


def _unpack(blob: bytes) -> tuple[dict, bytes, bytes]:
    if not isinstance(blob, bytes) or len(blob) > MAX_ENVELOPE:
        raise CipherError(BAD_ENVELOPE)
    prefix = len(MAGIC) + 2
    if len(blob) < prefix + TAG_BYTES or not blob.startswith(MAGIC):
        raise CipherError(BAD_ENVELOPE)
    length = struct.unpack(">H", blob[len(MAGIC):prefix])[0]
    if not (1 <= length <= MAX_HEADER) or len(blob) < prefix + length + TAG_BYTES:
        raise CipherError(BAD_ENVELOPE)
    aad = blob[:prefix + length]
    header_bytes = blob[prefix:prefix + length]
    try:
        header = json.loads(header_bytes)
        if not isinstance(header, dict) or frozenset(header) != FIELDS:
            raise ValueError("header shape")
        if header_bytes != _canonical(header):
            raise ValueError("non-canonical header")
        if type(header["v"]) is not int or header["v"] != VERSION:
            raise ValueError("version")
        if header["alg"] != ALGORITHM or header["ctype"] != CONTENT_TYPE:
            raise ValueError("algorithm")
        _key_id(header["kid"])
        nonce_text, salt_text = header["nonce"], header["salt"]
        if not (isinstance(nonce_text, str) and len(nonce_text) == NONCE_BYTES * 2
                and re.fullmatch("[0-9a-f]+", nonce_text)):
            raise ValueError("nonce")
        if not (isinstance(salt_text, str) and len(salt_text) == SALT_BYTES * 2
                and re.fullmatch("[0-9a-f]+", salt_text)):
            raise ValueError("salt")
    except (ValueError, TypeError, UnicodeError, CipherError, KeyError, OverflowError):
        raise CipherError(BAD_ENVELOPE) from None
    return header, aad, blob[prefix + length:]


def encrypt_source(source: bytes, key_id: str, master_key: bytes) -> bytes:
    """Encrypt bounded UTF-8 source in memory using a fresh derived file key.

    The 256-bit random salt derives a new AES key via HKDF-SHA256; a separate
    96-bit random AES-GCM nonce adds defense in depth against salt collision.
    """
    _key(master_key)
    _key_id(key_id)
    if not isinstance(source, bytes) or len(source) > MAX_SOURCE:
        raise CipherError("SkellLang source must be at most 32 KiB")
    try:
        source.decode("utf-8-sig", errors="strict")
    except UnicodeError:
        raise CipherError("SkellLang source must be UTF-8") from None
    salt = os.urandom(SALT_BYTES)
    nonce = os.urandom(NONCE_BYTES)
    header = {"v": VERSION, "alg": ALGORITHM, "kid": key_id,
              "nonce": nonce.hex(), "salt": salt.hex(), "ctype": CONTENT_TYPE}
    header_bytes = _canonical(header)
    if len(header_bytes) > MAX_HEADER:
        raise CipherError("Encrypted source header is too long")
    aad = MAGIC + struct.pack(">H", len(header_bytes)) + header_bytes
    ciphertext = AESGCM(_derive(master_key, salt)).encrypt(nonce, source, aad)
    return aad + ciphertext


def decrypt_source(blob: bytes, key_resolver: Callable[[str], bytes]) -> bytes:
    """Authenticated decryption; unauthenticated header selects a candidate key.

    The resolver must authorize access to its requested key. No plaintext
    fallback is ever attempted after resolver or authentication failure.
    """
    header, aad, ciphertext = _unpack(blob)
    try:
        if not callable(key_resolver):
            raise CipherError(BAD_ENVELOPE)
        master = _key(key_resolver(header["kid"]))
        raw = AESGCM(_derive(master, bytes.fromhex(header["salt"]))).decrypt(
            bytes.fromhex(header["nonce"]), ciphertext, aad)
        if len(raw) > MAX_SOURCE:
            raise CipherError(BAD_ENVELOPE)
        return raw
    except Exception:
        raise CipherError(BAD_ENVELOPE) from None


def rotate_source(blob: bytes, old_key_resolver: Callable[[str], bytes],
                  new_key_id: str, new_master_key: bytes) -> bytes:
    """Re-encrypt with a different key ID; preserve the original ciphertext."""
    _key_id(new_key_id)
    _key(new_master_key)
    header, _, _ = _unpack(blob)
    if new_key_id == header["kid"]:
        raise CipherError("Rotation requires a different key identifier")
    raw = decrypt_source(blob, old_key_resolver)
    return encrypt_source(raw, new_key_id, new_master_key)


def compile_encrypted(blob: bytes, key_resolver: Callable[[str], bytes]) -> dict:
    """Compile authenticated source in memory; redact unsafe parser diagnostics."""
    raw = decrypt_source(blob, key_resolver)
    try:
        source = raw.decode("utf-8-sig")
    except UnicodeError:
        raise CipherError(BAD_ENVELOPE) from None
    from .v0_1 import compile_source
    try:
        return compile_source(source)
    except Exception:
        # Legacy diagnostics may echo untrusted source tokens.
        raise CipherError("Authenticated source failed validation; diagnostics withheld") from None


def _read(path: Path, suffix: str, limit: int) -> bytes:
    path = Path(path).expanduser()
    if path.suffix.lower() != suffix or path.is_symlink() or not path.is_file():
        raise CipherError("Invalid source path or file type")
    if path.stat().st_size > limit:
        raise CipherError("Input exceeds permitted file size")
    raw = path.read_bytes()
    if len(raw) > limit:
        raise CipherError("Input exceeds permitted file size")
    return raw


def _write_new(path: Path, data: bytes) -> Path:
    """Exclusive 0600 create on POSIX; Windows ACLs inherited from directory."""
    path = Path(path).expanduser()
    if path.suffix.lower() != ".skellenc" or not path.parent.is_dir():
        raise CipherError("Destination must be .skellenc in an existing directory")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        raise CipherError("Refusing to overwrite existing encrypted file") from None
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def encrypt_file(source_path: Path, destination: Path, key_id: str,
                 master_key: bytes) -> Path:
    """Validate v0.1 plaintext before encrypting; retain input unchanged."""
    raw = _read(source_path, ".skell", MAX_SOURCE)
    from .v0_1 import compile_source
    try:
        compile_source(raw.decode("utf-8-sig"))
    except Exception:
        raise CipherError("Source validation failed; diagnostics withheld") from None
    return _write_new(destination, encrypt_source(raw, key_id, master_key))


def compile_encrypted_file(path: Path, key_resolver: Callable[[str], bytes]) -> dict:
    return compile_encrypted(_read(path, ".skellenc", MAX_ENVELOPE), key_resolver)


def rotate_file(source_path: Path, destination: Path,
                old_key_resolver: Callable[[str], bytes],
                new_key_id: str, new_master_key: bytes) -> Path:
    protected = _read(source_path, ".skellenc", MAX_ENVELOPE)
    updated = rotate_source(protected, old_key_resolver, new_key_id, new_master_key)
    return _write_new(destination, updated)
