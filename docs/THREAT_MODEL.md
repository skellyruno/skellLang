# SkellCipher Crypto threat model — design, NOT IMPLEMENTED

**No SkellLang source is encrypted by this migration.** This is a planning document; there is no shipped cryptographic primitive or key manager.

Protected assets: secret `.skell` projects, encryption and wrapping keys, compiler inputs, non-public presets and DSP IP, compiler artifacts. Threats: unauthorized repository readers, malicious or compromised CI, leaked build logs, lost laptops, tampered encrypted files, unauthorized agents without keys.

Design gates: use an audited maintained AEAD implementation (AES-256-GCM or XChaCha20-Poly1305), secure per-key nonce uniqueness, authenticated file header/version/algorithm/key-ID metadata, reliable key rotation, bounded parsing, fail-closed authentication errors, Windows DPAPI or Credential Manager for local wrapping keys with independent backup and recovery, no production keys in source or chats, transient authorized in-memory plaintext compilation, redacted errors, zero plaintext in artifacts, thorough corruption/wrong-key/recovery/security tests.

Residual risks: compromised authorized machine, malware/debuggers inspecting unlocked memory, an authorized developer disclosing source, and compiled VST3 reverse engineering. Encryption at rest does not make AI unable to understand exposed plaintext.

**Compatibility:** Current plaintext `.skell` stays supported by v0.1 compiler, but `.skellenc` is rejected and NEVER silently interpreted as plaintext. Separate this cryptographic product from the existing artistic SkellCipher alphabet.
