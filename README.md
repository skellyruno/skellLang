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

### Native control declarations

A separate `skell-native 1` source declares a stable host parameter table.
For example:

```text
skell-native 1
parameter speed 2100 "Retune Speed (ms)" 0 200 25 0.4
```

Run `python -m skelllang.native_controls INPUT OUTPUT` to generate a C++ include. The command creates a new file and refuses to overwrite an existing destination. Fields are stable key, numeric VST3 ID, title, physical minimum,
maximum, default and skew. Keep released keys and IDs stable. The plugin
supplies the DSP and binds those controls. The original `skell 1` Studio
export continues to use its existing commands.
