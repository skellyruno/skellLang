# SkellLang local development rules 🩻

Follow SkellWorld/AGENTS.md (https://github.com/skellyruno/SkellWorld/blob/main/AGENTS.md).

- Never commit private encryption keys, recovery passphrases, private plaintext source, offline key backups, decrypted temp files, or other secrets.
- Preserve skell 1 grammar, Studio JSON, immutable host parameter IDs, defaults and retired automation registrations.
- Use feature branches and draft PRs, batch changes, test on Windows and Linux; do not merge unverified work.
- Existing SkellForge, SkellNative, plugins, releases and user projects are unaffected until explicit migration is validated.
- The ordinary plaintext compiler MUST reject .skellenc. Only the explicit encrypted compile path may decrypt with authorized keys; never silently fall back to plaintext.
- Protect recovery files with authenticated encryption and require interactive password input. Never pass keys or passphrases via CLI arguments, source code, logs, environments or this chat.
- Run original SkellForge v0.1 parity, auth/corruption/rotation/recovery tests and Windows Credential Manager lifecycle checks. Passing CI is not a production security audit.
- DSP callback work must have zero blocking I/O, locks, allocations or exceptions.
