# SkellLang 🩻

Skelly's experimental proprietary audio-plugin language, extracted from the original SkellForge v0.1 compiler.

**Status:** backwards-compatible standalone compiler, plus experimental SkellCipher 0.1 authenticated encryption. The compiler still targets validated SkellForge Studio JSON, not a direct native VST3 backend. The original SkellForge repo and shipped plugins remain unchanged.

## Plaintext language compiler (Python 3.10+)

    python -m skelllang check examples/SkellWarmth.skell
    python -m skelllang export examples/SkellWarmth.skell scene.json
    python -m unittest discover -s tests -v

The extracted compatibility layer preserves SkellLang 0.1 syntax, retired automation IDs, stable Studio JSON and deterministic formatting.

## SkellCipher encryption (experimental)

On Windows, install:

    python -m pip install ".[windows]"

Use only replaceable development data because key recovery is not implemented:

    python -m skelllang cipher-key-create test-v1 --i-understand-no-recovery
    python -m skelllang cipher-encrypt examples/SkellWarmth.skell example.skellenc --key-id test-v1
    python -m skelllang cipher-check example.skellenc
    python -m skelllang cipher-key-create test-v2 --i-understand-no-recovery
    python -m skelllang cipher-rotate example.skellenc rotated.skellenc --new-key-id test-v2
    python -m skelllang cipher-check rotated.skellenc

The Windows CLI requires Windows Credential Manager and rejects unsafe keyring backends. It never accepts keys as command arguments. The cipher API is also usable programmatically with explicit in-memory keys, without Windows, after installing the cipher extra.

**IMPORTANT:** No independent key backup or recovery has been implemented. Losing the Windows account/vault may permanently destroy access. Do not encrypt irreplaceable Skelly source with this experimental version. Rotation exists but recovery does not. The original unencrypted input is not automatically deleted, and encrypted files are not silently compiled by the ordinary plaintext compiler.

**PUBLIC REPOSITORY:** Do not commit private plaintext SkellLang projects, master keys or generated unprotected assets. Compiled binaries and output models still expose information about DSP and UI.

SkellCipher Crypto is distinct from SkellForge's historic artistic SkellCipher alphabet. See docs/SKELLCIPHER.md, docs/THREAT_MODEL.md and docs/ARCHITECTURE.md.
