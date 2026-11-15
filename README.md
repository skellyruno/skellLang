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

### Native schema v2 and encrypted native checks

`skell-native 2` appends `STEPS UNITS FLAGS` to each declaration. `STEPS=0`
means continuous; positive steps use a linear quantized mapping. Flags are
`automate`, `bypass`, or `readonly`. Bypass must be 0..1 with one step.
V1 output remains supported. V2 allows 128 controls within 32 KiB.

```text
skell-native 2
parameter wet 2102 "Wet Mix" 0 100 100 1 0 "%" automate
parameter bypass 2104 "Bypass" 0 1 0 1 1 "" bypass
```

```sh
python -m skelllang.native_controls controls.skell Controls.inc
python -m skelllang.native_controls controls.skell controls.json --json
python -m skelllang.native_controls controls.skell --check --against released.skell
python -m skelllang cipher-check controls.skellenc --native
```

Compatibility checks reject changes to existing order, keys, IDs, ranges,
defaults, skew, steps or flags. Appends and display-label changes are allowed.
This is a declaration check, not proof of audio/DAW compatibility. V1 has no
explicit bypass metadata, so migration from a plugin-specific V1 bypass needs
manual verification, as done for Mini's unchanged host flags and state.

`cipher-encrypt` validates either Studio or native source. Native encrypted
compilation is explicit (`compile_encrypted_native` or `cipher-check --native`),
authenticates first, and produces C++ only in memory. Diagnostics are redacted;
no plaintext temp file or automatic build-cache export is introduced. Generated
C++ still contains parameter names and values if a caller chooses to save it.

Windows verification on 2026-11-15: 54 tests, 53 passed, one unavailable symlink
creation test skipped. Real temporary Credential Manager create/delete/restore
passed; five original Forge compiler parity scenarios passed. Private artifact
filename scan passed. External security review remains outstanding.
