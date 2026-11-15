# SkellCipher Crypto: encrypted source + offline recovery

Status: experimental cryptography built on the maintained cryptography Python library. Not independently security-audited or certified for production IP.

## Authenticated source format v1

Source format: 9-byte SKELLENC + NUL magic, 2-byte big-endian header length, canonical JSON header, and AES-256-GCM ciphertext with 16-byte tag.

Required header: v=1, alg="AES-256-GCM+HKDF-SHA256", kid, nonce (12 random bytes, lowercase hex), salt (32 random bytes, lowercase hex), ctype="skell-source-utf8". Magic, length and complete header are authenticated as additional data. Max source is 32768 bytes and max header 512 bytes.

A fresh random 256-bit salt derives a per-file encryption key using HKDF-SHA256 from the stored 256-bit master; a fresh 96-bit nonce is also sampled. Unique random salts/nonces are overwhelmingly likely but not mathematically guaranteed. Wrong keys, modified headers, missing metadata, bad versions, malformed UTF-8, ciphertext corruption and unauthorized resolvers fail closed. Re-keying generates new salt and nonce and preserves previous encrypted source.

## Password-protected offline recovery backup v1

Backup format: 9-byte SKELLREC + NUL magic; two-byte length, canonical authenticated JSON header, then AES-256-GCM encrypted 32-byte master key. Required header includes v=1, kind, kid, kdf="scrypt", n=131072, r=8, p=1, random 32-byte salt and random 12-byte nonce. Parameters are fixed and validated before deriving any key to block resource-exhaustion metadata. The recovery key is derived from a user-entered high-entropy passphrase using scrypt (128 MiB work factor). This backup is not the same key as the source encryption root key.

Use an offline random recovery secret generated in a trusted password manager; human-created 20-character passwords are not necessarily secure. CLI prompts through getpass twice for backup and once for restore, and refuses noninteractive or piped passphrase input. Recovery backups are written only to new .skellbackup files, mode 0600 on POSIX (Windows inherits the parent ACL). Backup bytes are authenticated and self-tested before reporting success. Recovery verifies header, password, tag, expected length and then imports the master key into Windows Credential Manager without overwriting any existing key identifier.

**Operational recovery check:** Back up each root key separately, keep copies of each .skellbackup offline, store each passphrase separately and securely, test restoration on a spare Windows profile/device, and never delete older keys or plaintext source until every protected file opens under the new key. Do not commit .skellbackup to GitHub or upload it to this chat.

## Key storage and source compilation

Windows root keys reside only in approved WinVaultKeyring-backed Windows Credential Manager. No fallback to plaintext keyrings, raw key CLI arguments or environment variables. The standalone cipher library accepts explicit in-memory test/authorized keys cross-platform.

Authorized encrypted compilation decrypts in memory and suppresses error diagnostics that might echo private source tokens. Normal skell 1 compiler stays compatible and refuses .skellenc. On success the authorized caller receives the unencrypted Studio document, which must not be copied into logs or public build artifacts. Encryption does not protect generated VST3 binaries.

Python immutable key and plaintext bytes cannot be reliably zeroized; memory inspection, swap, backups and machine compromise remain risks. A third-party security review and user-device restore test remain required before production use.

## Testing

Cross-platform regression suite: encryption/decryption, tamper resistance, wrong keys, metadata authentication, UTF-8 bounds, key rotation, redacted diagnostics, scrypt recovery backup and corruption, overwrite refusal, Windows vault mock, and ephemeral real-Windows vault loss/restore CI. All keys and passphrases in tests are synthetic, never production.

## Native source integration (2026-11-15)

The explicit native entrypoints authenticate encrypted `skell-native 1/2`,
compile controls in memory and redact parser diagnostics. Existing Studio
entrypoints retain their dictionary return type and reject native source.
`cipher-check --native` validates without outputting source or generated C++.
Encrypted file reads are bounded even if a file grows after stat. Recovery
rejects incorrect ciphertext lengths before running scrypt. No keys, passwords
or decrypted build artifacts are written by these native checks.
