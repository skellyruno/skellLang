# SkellCipher Crypto v0.1: authenticated source encryption

Status: experimental cryptographic implementation, not a reviewed production secret-management system.

## Versioned file format

Binary layout: 9-byte magic SKELLENC + NUL, 2-byte unsigned big-endian header length, canonical UTF-8 JSON header, and AES-GCM ciphertext plus a 16-byte authentication tag. Max source length is 32768 bytes; max header is 512 bytes.

Required fields: v=1, alg="AES-256-GCM+HKDF-SHA256", kid (key ID), nonce (12 random bytes represented as lowercase hex), salt (32 random bytes as lowercase hex), and ctype="skell-source-utf8".

All fields, magic and header length are authenticated as AES-GCM associated data. An unverified key ID is used only to find the candidate master key; it is not itself proof of authorization.

For each encryption, generate a new 256-bit salt and a 96-bit nonce from the OS CSPRNG. Derive a 256-bit per-file encryption key using HKDF-SHA256 with master key, random salt and context "SkellCipher/source/v1/aes-256-gcm". AES-256-GCM from the maintained cryptography library encrypts the source. Random salt and nonce collisions are extremely unlikely but are probabilistic, not a mathematically guaranteed impossibility.

The parser rejects noncanonical headers, unknown or missing fields, unsupported versions, tampering, truncated files, wrong keys and oversized inputs. It never falls back to plaintext. Re-keying decrypts inside memory and encrypts into a new file with a different key ID, salt and nonce. Old encrypted files remain unchanged.

## Windows keys

Only Windows Credential Manager using keyring WinVaultKeyring (pywin32) may persist keys. No plaintext keyrings or other providers are accepted. Key creation samples 32 random bytes from the OS, checks for collision with existing key IDs, and verifies that the credential can be retrieved. The CLI never accepts or prints secret key strings.

**Recovery and cross-machine import are not implemented.** Use experimental keys only on replaceable source, with the explicit no-recovery acknowledgment. Production protection requires audited offline backup and restore with tested loss/recovery behavior before enabling use on irreplaceable projects. Do not delete older vault keys until all rotated files and archived copies have been checked.

## Build and exposure boundaries

- Original .skell plaintext stays on disk after encryption: never assume it was securely erased.
- The compiler has an explicit in-memory encrypted compile entry point, with source-neutral error messages. No plaintext temporary source files are created by this entry point.
- Generated Studio JSON, C++ and VST3 binary output is not encrypted and must be handled as potentially sensitive.
- Python bytes may remain in process memory, swap, crash dumps or diagnostics; it cannot be reliably zeroized by this implementation.
- Input source symlinks are refused; output files are exclusive-create. On POSIX output mode is 0600; Windows ACLs inherit from parent.
- The local Windows key backend requires a logged-in authorized user. This does not protect against malware already running as that user.

## Testing

Cross-platform compiler and crypto suite, wrong key and tamper tests, in-memory compiler parity, key rotation, filename secret-artifact scan, and ephemeral Windows Credential Manager CI smoke. No production key is needed. Neither CI nor passing crypto tests are a comprehensive third-party security audit.
