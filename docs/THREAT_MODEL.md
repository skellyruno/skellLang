# SkellCipher Crypto: threat model v0.1

**Status: experimental AES-256-GCM authenticated encryption implemented; no independent security audit. Durable key backup and restore are not implemented. Do not use for irreplaceable projects.**

Assets: non-public SkellLang source, source-level DSP/UI IP, encryption master keys, unlocked compiler source and generated artifacts. Adversaries include unauthorized repository readers, unauthorized agents without keys, tampered encrypted files and accidental CI/log/artifact leaks.

Existing protections: authenticated encryption using cryptography AES-256-GCM and HKDF-SHA256 independent per-file keys from random salts; fresh random AES-GCM nonces; strict bounded versioned authenticated metadata; generic errors for failed authentication and compiler diagnostics; file exclusive-create; rotation without original overwrite; Windows Credential Manager-only master-key storage with unsafe backends rejected; CI negative cases and filename-based tracked-artifact checks.

Residual exposure: the public header exposes key ID and approximate source length; encryption does not prevent ciphertext rollback or deletion. Authorized source is present in memory and can be inspected by malware, a debugger or crash dump. Keys in Windows Credential Manager are accessible to the authorized user context and may be stolen if that context is compromised. Editor caches, backups and the original plaintext file may persist. The authenticated compiler returns plaintext-derived Studio data; generated plugin binaries can be reverse-engineered. Secrets in Python immutable bytes cannot be securely zeroized. Arbitrary AI agents with authorized plaintext can read it; encryption only blocks unkeyed access to ciphertext.

Known blockers: independent recovery backup and restore, Windows machine/account migration, audited build output filtering, full secrets scanning of files/binaries/crash dumps, external crypto review, host integration, production release policy. Test suites are not sufficient to claim absolute security. Random nonce/salt uniqueness is probabilistic.

Next security gate: implement offline encrypted key recovery with a reviewed KDF and authenticated envelope, validate with lost-account and offline restores, then integrate authorized SkellForge decryption and scan generated outputs. Maintain backwards compatible SkellLang 0.1 and immutable host parameter IDs.
