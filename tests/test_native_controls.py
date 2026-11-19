import unittest
from skelllang import SkellLangError
from pathlib import Path
from tempfile import TemporaryDirectory
from skelllang.native_controls import compile_controls, export_controls


class NativeControlTests(unittest.TestCase):
    def test_deterministic_and_preserves_explicit_id(self):
        source = 'skell-native 1\nparameter speed 2100 "Speed (ms)" 0 200 25 0.4\n'
        output = compile_controls(source)
        self.assertEqual(output, compile_controls(source))
        self.assertIn('control_speed', output)
        self.assertIn('2100u, u"Speed (ms)", "speed", 0.0f, 200.0f, 25.0f, 0.4f', output)

    def test_rejects_invalid_source(self):
        prefix = "skell-native 1\n"
        valid = 'parameter speed 2100 "Speed" 0 200 25 0.4\n'
        for bad in (valid + valid, valid.replace("2100", "0"), valid.replace("25", "250"),
                    valid.replace("25", "nan"), valid.replace("0.4", "0"),
                    valid.replace("Speed", "Speed^"), " " * 8193):
            with self.subTest(line=bad[:80]), self.assertRaises(SkellLangError):
                compile_controls(prefix + bad)


class NativeControlExportTests(unittest.TestCase):
    SOURCE = "skell-native 1\nparameter speed 2100 \"Speed (ms)\" 0 200 25 0.4\n"

    def test_export_creates_new_file_and_preserves_source(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "controls.skell"
            output = Path(folder) / "Controls.inc"
            source.write_text(self.SOURCE, encoding="utf-8")
            original = source.read_bytes()
            self.assertEqual(export_controls(source, output), output)
            self.assertEqual(output.read_text(encoding="utf-8"), compile_controls(self.SOURCE))
            self.assertEqual(source.read_bytes(), original)

    def test_export_refuses_to_overwrite_existing_destination(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "controls.skell"
            output = Path(folder) / "Controls.inc"
            source.write_text(self.SOURCE, encoding="utf-8")
            output.write_text("preserve this file\n", encoding="utf-8")
            with self.assertRaises(SkellLangError):
                export_controls(source, output)
            self.assertEqual(output.read_text(encoding="utf-8"), "preserve this file\n")

    def test_export_refuses_source_as_destination(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "controls.skell"
            source.write_text(self.SOURCE, encoding="utf-8")
            original = source.read_bytes()
            with self.assertRaises(SkellLangError):
                export_controls(source, source)
            self.assertEqual(source.read_bytes(), original)
