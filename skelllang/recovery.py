"""Offline SkellCipher recovery: password-wrapped root key with audited primitives.

Recovery passwords must be supplied interactively, never through process args,
environment variables, source control, logs, or this repository.
"""
from __future__ import annotations
import json
import os
import re
import struct
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from .cipher import CipherError, _canonical, _key, _key_id

MAGIC = b"SKELLREC\x00"
VERSION = 1
COST_N = 1 << 17
COST_R = 8
COST_P = 1
SALT_BYTES = 32
NONCE_BYTES = 12
MAX_HEADER = 512
MAX_BACKUP = 2048
ERROR = "Invalid or unauthorized SkellCipher recovery backup"
FIELDS = frozenset(("v", "kind", "kdf", "n", "r", "p", "kid", "salt", "nonce"))


def _passphrase(secret: str) -> bytes:
    if not isinstance(secret, str) or not (20 <= len(secret) <= 1024):
        raise CipherError("A high-entropy recovery passphrase of 20-1024 characters is required")
    if any(ord(ch) < 32 for ch in secret):
        raise CipherError("Recovery passphrase contains unsupported characters")
    return secret.encode("utf-8")


def _derive(secret: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=COST_N, r=COST_R, p=COST_P)
    return kdf.derive(_passphrase(secret))


def create_backup(key_id: str, master_key: bytes, recovery_passphrase: str) -> bytes:
    """Make a versioned authenticated offline backup from an authorized master."""
    _key_id(key_id)
    _key(master_key)
    salt = os.urandom(SALT_BYTES)
    nonce = os.urandom(NONCE_BYTES)
    header = {"v": VERSION, "kind": "SkellCipher-master-key",
              "kdf": "scrypt", "n": COST_N, "r": COST_R, "p": COST_P,
              "kid": key_id, "salt": salt.hex(), "nonce": nonce.hex()}
    packed = _canonical(header)
    if len(packed) > MAX_HEADER:
        raise CipherError(ERROR)
    aad = MAGIC + struct.pack(">H", len(packed)) + packed
    ct = AESGCM(_derive(recovery_passphrase, salt)).encrypt(nonce, master_key, aad)
    return aad + ct


def restore_backup(blob: bytes, recovery_passphrase: str) -> tuple[str, bytes]:
    """Verify authenticated metadata and restore only a 32-byte master key."""
    try:
        if not isinstance(blob, bytes) or len(blob) > MAX_BACKUP:
            raise ValueError("backup size")
        fixed = len(MAGIC) + 2
        if not blob.startswith(MAGIC) or len(blob) < fixed + 16:
            raise ValueError("backup magic")
        size = struct.unpack(">H", blob[len(MAGIC):fixed])[0]
        if not (1 <= size <= MAX_HEADER) or len(blob) < fixed + size + 16:
            raise ValueError("header length")
        header = json.loads(blob[fixed:fixed + size])
        if not isinstance(header, dict) or frozenset(header) != FIELDS:
            raise ValueError("header fields")
        if _canonical(header) != blob[fixed:fixed + size]:
            raise ValueError("header format")
        if (type(header["v"]) is not int or header["v"] != VERSION
                or header["kind"] != "SkellCipher-master-key"):
            raise ValueError("version")
        if (header["kdf"] != "scrypt" or type(header["n"]) is not int
                or type(header["r"]) is not int or type(header["p"]) is not int
                or (header["n"], header["r"], header["p"]) != (COST_N, COST_R, COST_P)):
            raise ValueError("KDF cost")
        _key_id(header["kid"])
        salt, nonce = header["salt"], header["nonce"]
        if not (isinstance(salt, str) and len(salt) == 2 * SALT_BYTES
                and re.fullmatch("[0-9a-f]+", salt)):
            raise ValueError("salt")
        if not (isinstance(nonce, str) and len(nonce) == 2 * NONCE_BYTES
                and re.fullmatch("[0-9a-f]+", nonce)):
            raise ValueError("nonce")
        recovered = AESGCM(_derive(recovery_passphrase, bytes.fromhex(salt))).decrypt(
            bytes.fromhex(nonce), blob[fixed + size:], blob[:fixed + size])
        return header["kid"], _key(recovered)
    except Exception:
        raise CipherError(ERROR) from None


def _read_backup(path: Path) -> bytes:
    path = Path(path).expanduser()
    if path.suffix.lower() != ".skellbackup" or path.is_symlink() or not path.is_file():
        raise CipherError("Invalid recovery backup path")
    if path.stat().st_size > MAX_BACKUP:
        raise CipherError(ERROR)
    raw = path.read_bytes()
    if len(raw) > MAX_BACKUP:
        raise CipherError(ERROR)
    return raw


def backup_to_file(path: Path, key_id: str, master_key: bytes,
                   recovery_passphrase: str) -> Path:
    path = Path(path).expanduser()
    if path.suffix.lower() != ".skellbackup" or not path.parent.is_dir():
        raise CipherError("Recovery backup must use .skellbackup in an existing folder")
    payload = create_backup(key_id, master_key, recovery_passphrase)
    if restore_backup(payload, recovery_passphrase) != (key_id, master_key):
        raise CipherError(ERROR)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        raise CipherError("Refusing to overwrite an existing recovery backup") from None
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def restore_from_file(path: Path, recovery_passphrase: str) -> tuple[str, bytes]:
    return restore_backup(_read_backup(path), recovery_passphrase)
