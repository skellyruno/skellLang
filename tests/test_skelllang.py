"""SkellLang v0.1: safe deterministic compiler; new-project workflow tests."""
from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from skelllang import (
    SkellLangError, compile_source, compile_file, export_json,
    format_source, export_from_studio, import_to_studio_model,
)
from skelllang.compat.studio import load_studio

GOOD = """\
# SkellLang example
skell 1
canvas 440 310
fx saturate warmth 2.5 on
fx lowpass tone 8500 off
knob drive_knob warmth "DRIVE" 18 128 105 110
knob tone_knob tone "TONE" 315 128 105 110
meter output_meter "OUT" 20 270 155 22
text brand_label "SKELLY / FORGE" 192 270 200 22
"""


class SkellLangTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "test.skell"
        self.source.write_text(GOOD, encoding="utf-8")

    def test_compiles_validated_dsp_and_ui(self):
        model = compile_source(GOOD)
        self.assertEqual(model["schema"], "skellforge/studio/1")
        self.assertEqual(len(model["chain"]), 3)
        self.assertEqual(model["chain"][1]["id"], "warmth")
        self.assertEqual(model["chain"][1]["drive"], 2.5)
        self.assertTrue(model["chain"][1]["enabled"])
        self.assertFalse(model["chain"][2]["enabled"])
        self.assertEqual(len(model["components"]), 8)
        self.assertEqual(model["components"][4]["parameter_id"], "fx_warmth_drive")
        self.assertEqual(model["components"][5]["parameter_id"], "fx_tone_cutoff_hz")

    def test_compiles_deterministically(self):
        self.assertEqual(json.dumps(compile_source(GOOD), sort_keys=True),
                         json.dumps(compile_source(GOOD), sort_keys=True))

    def test_no_empty_or_duplicate_language_headers(self):
        with self.assertRaisesRegex(SkellLangError, "No SkellLang version"):
            compile_source("")
        with self.assertRaisesRegex(SkellLangError, "first statement"):
            compile_source("fx saturate drive 2 on")
        with self.assertRaisesRegex(SkellLangError, "duplicate language version"):
            compile_source("skell 1\nskell 1")

    def test_rejects_unknown_operations_and_python_execution(self):
        for snippet in ("import os", "eval()", "exec test", "while true", "python"):
            with self.subTest(snippet=snippet):
                with self.assertRaises(SkellLangError):
                    compile_source("skell 1\n" + snippet)

    def test_rejects_duplicate_components_and_nodes(self):
        with self.assertRaisesRegex(SkellLangError, "duplicate FX"):
            compile_source("skell 1\nfx saturate warmth 2 on\nfx saturate warmth 3 on")
        with self.assertRaisesRegex(SkellLangError, "duplicate UI"):
            compile_source("skell 1\nmeter title OUT 10 270 100 25")
        with self.assertRaisesRegex(SkellLangError, "duplicate UI"):
            compile_source("skell 1\ntext x A 10 260 100 24\ntext x B 20 260 100 24")

    def test_bad_ranges_and_missing_nodes_fail_validation(self):
        with self.assertRaisesRegex(SkellLangError, "outside fixed bounds|between 1 and 10"):
            compile_source("skell 1\nfx saturate warmth 999 on")
        with self.assertRaisesRegex(SkellLangError, "missing FX"):
            compile_source("skell 1\nknob drive_knob missing DRIVE 20 140 100 100")
        with self.assertRaisesRegex(SkellLangError, "outside the canvas"):
            compile_source("skell 1\nmeter meter_out OUT 425 280 60 40")
        with self.assertRaisesRegex(SkellLangError, "finite"):
            compile_source("skell 1\nfx lowpass tone NaN on")

    def test_builtin_move_and_forward_reference(self):
        model = compile_source(
            'skell 1\nmove gain_knob 150 101 130 130\n'
            'knob knob1 tone "LOWPASS" 312 120 100 110\n'
            'fx lowpass tone 6000 on\n'
        )
        self.assertEqual(model["components"][3]["x"], 150)
        self.assertEqual(model["components"][-1]["parameter_id"],
                         "fx_tone_cutoff_hz")

    def test_limits_malformed_quotes_and_truncated_source(self):
        with self.assertRaisesRegex(SkellLangError, "invalid quotes"):
            compile_source('skell 1\ntext tagline "oops 10 250 100 20')
        with self.assertRaisesRegex(SkellLangError, "32 KiB"):
            compile_source("skell 1\n" + ("# " + "a"*120 + "\n")*290)
        with self.assertRaisesRegex(SkellLangError, "256 lines"):
            compile_source("skell 1\n" + "# ok\n" * 256)

    def test_json_export_never_overwrites_existing_file(self):
        output = self.root / "scene.json"
        export_json(self.source, output)
        self.assertEqual(json.loads(output.read_text())["chain"][1]["id"], "warmth")
        with self.assertRaisesRegex(SkellLangError, "Refusing to overwrite"):
            export_json(self.source, output)

    def test_source_roundtrip_without_registry(self):
        scene = compile_source(GOOD)
        output = format_source(scene)
        self.assertEqual(compile_source(output), scene)
        self.assertEqual(format_source(compile_source(output)), output)

    def test_unknown_fields_refused_not_silently_removed(self):
        original = compile_source(GOOD)
        original["component_extension"] = {"version": 2}
        with self.assertRaisesRegex(SkellLangError, "Unknown Studio fields"):
            format_source(original)
        original.pop("component_extension")
        original["components"][4]["future_ui_prop"] = True
        with self.assertRaisesRegex(SkellLangError, "Unknown attributes"):
            format_source(original)

    def test_quoted_captions_survive_source_export(self):
        model = compile_source(
            "skell 1\ntext label1 \"It\\'s Skelly's world\" 20 266 230 22\n")
        source = format_source(model)
        self.assertEqual(compile_source(source), model)

if __name__ == "__main__":
    unittest.main()
