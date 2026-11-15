# SkellLang 0.1 extraction audit and roadmap

Origin: `skellyruno/skellforge`, immutable commit `33ccce7ff7cfff48695fe13e5c05b652a4a7e744` on `feature/skelllang-sdk-v0.1`.

The legacy parser is a bounded line-oriented Python implementation based on `shlex.split`, with validated deterministic Studio JSON output. Supported syntax: `skell 1`, `canvas`, `fx`, `reserve`, `move`, `text`, `meter`, `knob`. Bounds: 32 KiB and 256 source lines. Studio model is `skellforge/studio/1`; automation IDs are tied to stable DSP node IDs and must never be reused.

This extraction relocates original parser and its Studio validator, automation registry, and UI generator to `skelllang/v0_1.py` and `skelllang/compat/`. Other than imported module paths and explicit rejection of `.skellenc`, v0.1 parsing and output remain unchanged. The compatibility snapshot is a bridge, not the future independent language architecture. Existing SkellForge/SkellNative repositories are not changed.

**Next modules (planned, not implemented):** versioned lexer, AST, semantic analyzer, static numeric types/units, real-time safety checker, canonical `SkellIR/1` with explicit versioned schema, SkellForge adapter, SkellNative DSP generator and SkellDraw UI generator. Only UI-thread code may animate; DSP callback code must not allocate, lock, block, throw exceptions or do filesystem operations.

Current SkellForge exporter remains JUCE-based. The separate direct Steinberg VST3 prototype exists on `feature/skellnative-direct-vst3-gain` but is not yet a general SkellLang backend. Preserve original plugins, host parameter IDs, save states, presets and UI while migrating. Pin a verified SkellLang package commit before Forge switches to this package.
