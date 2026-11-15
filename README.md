# SkellLang 🩻

Skelly’s experimental proprietary audio-plugin language, extracted from the original SkellForge 0.1 compiler.

**Current status: independent 0.1 compatibility compiler (draft), not an encrypted-source or JUCE-free VST3 compiler yet.**

Use Python 3.10+:

```sh
python -m skelllang check examples/SkellWarmth.skell
python -m skelllang export examples/SkellWarmth.skell scene.json
python -m unittest discover -s tests -v
```

The extracted package includes a frozen Studio/automation compatibility layer so `skell 1` output, retired parameter IDs and existing JSON models do not silently change. The original SkellForge compiler remains intact until the new package and Forge integration are verified.

**Security:** This repository is public. Do not commit secret `.skell` projects as plaintext. The `.skellenc` extension is rejected until authenticated encryption and authorized key handling are implemented. See [architecture](docs/ARCHITECTURE.md) and [threat model](docs/THREAT_MODEL.md).

The prior *artistic* SkellCipher alphabet in SkellForge branding documentation is not cryptography; this planned **SkellCipher Crypto** module is distinct.
