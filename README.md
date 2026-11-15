# SkellLang 🩻

Skelly's experimental proprietary audio-plugin language, extracted from the existing SkellForge v0.1 compiler.

**Current status:** standalone 0.1-compatible compiler, experimental SkellCipher AES-256-GCM encrypted source, and optional scrypt-protected offline key backup/recovery. The compiler targets Studio JSON and native C++ parameter tables consumed by SkellNative pilots. Original SkellForge and existing plugin projects are unchanged.

## Plaintext compiler

    python -m skelllang check examples/SkellWarmth.skell
    python -m skelllang export examples/SkellWarmth.skell scene.json
    python -m unittest discover -s tests -v

Preserves SkellLang 0.1 syntax, Studio JSON format, retired automation IDs and deterministic code generation.

## SkellCipher encrypted source: experimental Windows CLI

    python -m pip install ".[windows]"
    python -m skelllang cipher-key-create dev-v1 --i-understand-recovery-required
    python -m skelllang cipher-backup dev-v1 D:/offline/dev-v1.skellbackup
    python -m skelllang cipher-encrypt examples/SkellWarmth.skell encrypted.skellenc --key-id dev-v1
    python -m skelllang cipher-check encrypted.skellenc
    python -m skelllang cipher-key-create dev-v2 --i-understand-recovery-required
    python -m skelllang cipher-backup dev-v2 D:/offline/dev-v2.skellbackup
    python -m skelllang cipher-rotate encrypted.skellenc rotated.skellenc --new-key-id dev-v2
    python -m skelllang cipher-check rotated.skellenc

The backup command prompts interactively twice for a recovery passphrase. Choose a truly random, high-entropy passphrase using a trusted offline password manager; do not supply it to ChatGPT, an AI agent, environment variables, scripts or process arguments. Store the encrypted backup on separate offline media and the passphrase independently. Before deleting any master key, test backup recovery. If migrating to another Windows account/device, use:

    python -m skelllang cipher-restore D:/offline/dev-v1.skellbackup

Restoring refuses to overwrite an existing key ID in the current Windows Credential Manager vault. Source encryption never deletes the original plaintext .skell input. Ordinary skelllang check does not decrypt .skellenc; only the explicit authorized encrypted entrypoints do.

**Still experimental:** code and CI tests do not replace an external cryptographic/security review or real migration on the target Windows PC. The Windows vault may be compromised by malware running as the authorized user; compiled binaries and source-derived Studio JSON remain potentially inspectable. Until end-to-end recovery is reviewed, protect only replaceable development sources, not irreplaceable production IP.

**PUBLIC REPOSITORY:** never commit secret plaintext sources, private keys, recovery passwords, or recovery backup files. Only code and synthetic test data belong here.

SkellCipher Crypto is separate from SkellForge's historic artistic SkellCipher alphabet. See docs/SKELLCIPHER.md, docs/THREAT_MODEL.md and docs/ARCHITECTURE.md.

The prior *artistic* SkellCipher alphabet in SkellForge branding documentation is not cryptography; the experimental **SkellCipher Crypto** module is distinct.

### Native control declarations

A separate `skell-native 1` source declares a stable host parameter table.
For example:

```text
skell-native 1
parameter speed 2100 "Retune Speed (ms)" 0 200 25 0.4
```

Run `python -m skelllang.native_controls INPUT OUTPUT` to generate a C++
include. Fields are stable key, numeric VST3 ID, title, physical minimum,
maximum, default and skew. Keep released keys and IDs stable. The plugin
supplies the DSP and binds those controls. The original `skell 1` Studio
export continues to use its existing commands.
