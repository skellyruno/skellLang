"""Cross-check extracted compiler against pinned original SkellForge commit."""
import json
import sys
from pathlib import Path
from skelllang import compile_source, format_source
from skelllang.compat.automation import sync_registry

origin = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(origin))
from skellforge.skelllang import compile_source as old_compile
from skellforge.skelllang import format_source as old_format
from skellforge.automation import sync_registry as old_sync

examples = [
    "skell 1\n",
    "skell 1\nfx saturate warmth 2.5 on\n",
    "skell 1\nfx lowpass tone 8500 off\n",
    "skell 1\nknob t tone TONE 300 130 100 100\nfx lowpass tone 5000 on\n",
    Path("examples/SkellWarmth.skell").read_text(encoding="utf-8"),
]
for number, source in enumerate(examples):
    now, before = compile_source(source), old_compile(source)
    assert json.dumps(now, sort_keys=True) == json.dumps(before, sort_keys=True), number
    assert format_source(now) == old_format(before), number
    sync_registry(now)
    old_sync(before)
    assert json.dumps(now, sort_keys=True) == json.dumps(before, sort_keys=True), number
    assert format_source(now) == old_format(before), number
print("SkellForge v0.1 parity: 5 scenarios passed")
