"""Extraction compatibility and encryption fail-closed regression tests."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from skelllang import (SkellLangError, compile_file, compile_source,
                       format_source, export_from_studio, import_to_studio_model)
from skelllang.compat.automation import sync_registry
from skelllang.compat.studio import default_studio

SOURCE = """skell 1
canvas 440 310
fx saturate warmth 2.5 on
fx lowpass tone 8500 off
knob drive_knob warmth DRIVE 18 128 105 110
knob tone_knob tone TONE 315 128 105 110
"""

class StandaloneTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.src = self.root / "original.skell"
        self.src.write_text(SOURCE, encoding="utf-8")

    def test_skellenc_never_compiles_as_plaintext(self):
        enc = self.root / "locked.skellenc"
        enc.write_bytes(b"skell 1\n")
        with self.assertRaisesRegex(SkellLangError, "SkellCipher unlock"):
            compile_file(enc)

    def test_retired_host_ids_roundtrip(self):
        scene = compile_source(SOURCE)
        sync_registry(scene)
        scene["chain"] = scene["chain"][:1]
        scene["components"] = [c for c in scene["components"] if c["type"] != "effect_knob"]
        self.assertEqual(compile_source(format_source(scene)), scene)

    def test_import_is_in_memory(self):
        project = self.root / "project"
        project.mkdir()
        path = project / "forge-studio.json"
        path.write_text(json.dumps(default_studio()), encoding="utf-8")
        before = path.read_bytes()
        imported = import_to_studio_model(project, self.src)
        self.assertEqual(len(imported["parameter_registry"]), 2)
        self.assertEqual(before, path.read_bytes())

    def test_published_default_cannot_change(self):
        project = self.root / "published"
        project.mkdir()
        previous = compile_source(SOURCE)
        sync_registry(previous)
        (project / "forge-studio.json").write_text(json.dumps(previous), encoding="utf-8")
        changed = self.root / "changed.skell"
        changed.write_text(SOURCE.replace("warmth 2.5 on", "warmth 9.0 on"), encoding="utf-8")
        with self.assertRaisesRegex(SkellLangError, "compatibility"):
            import_to_studio_model(project, changed)

    def test_export_from_studio_without_overwrite(self):
        project = self.root / "studio"
        project.mkdir()
        saved = compile_source(SOURCE)
        sync_registry(saved)
        (project / "forge-studio.json").write_text(json.dumps(saved), encoding="utf-8")
        dest = self.root / "roundtrip.skell"
        export_from_studio(project, dest)
        self.assertEqual(compile_file(dest), saved)
        with self.assertRaises(SkellLangError):
            export_from_studio(project, dest)

    def test_cli_check_and_export(self):
        args = [sys.executable, "-m", "skelllang"]
        a = subprocess.run(args + ["check", str(self.src)], text=True, capture_output=True)
        self.assertEqual(a.returncode, 0, a.stderr)
        target = self.root / "scene.json"
        b = subprocess.run(args + ["export", str(self.src), str(target)], text=True, capture_output=True)
        self.assertEqual(b.returncode, 0, b.stderr)
        self.assertTrue(target.exists())
        c = subprocess.run(args + ["export", str(self.src), str(target)], text=True, capture_output=True)
        self.assertNotEqual(c.returncode, 0)
        locked = self.root / "locked.skellenc"
        locked.write_bytes(b"not ciphertext")
        d = subprocess.run(args + ["check", str(locked)], text=True, capture_output=True)
        self.assertNotEqual(d.returncode, 0)
        self.assertIn("SkellCipher", d.stderr)

if __name__ == "__main__":
    unittest.main()
