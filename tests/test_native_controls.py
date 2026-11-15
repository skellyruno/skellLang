import unittest
from skelllang import SkellLangError
from skelllang.native_controls import compile_controls, parse_controls, manifest, compatibility_errors, read_source


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


class NativeSchemaV2Tests(unittest.TestCase):
    source = 'skell-native 2\nparameter wet 10 "Wet" 0 100 100 1 0 "%" automate\nparameter bypass 11 "Bypass" 0 1 0 1 1 "" bypass\n'

    def test_metadata_and_manifest(self):
        version, controls = parse_controls(self.source)
        self.assertEqual(version, 2)
        self.assertEqual(controls[1].steps, 1)
        self.assertIn('NativeControlFlags::bypass', compile_controls(self.source))
        self.assertEqual(manifest(self.source)["controls"][0]["units"], "%")

    def test_compatibility_rejects_breaking_changes(self):
        for before, after in [('wet 10', 'wet 20'), ('0 100 100 1', '0 200 100 1'),
                              ('0 100 100 1', '0 100 50 1'), ('0 100 100 1', '0 100 100 0.5'),
                              ('0 "%" automate', '100 "%" automate'), ('automate', 'readonly')]:
            with self.subTest(after=after):
                self.assertTrue(compatibility_errors(self.source, self.source.replace(before, after)))
        self.assertTrue(compatibility_errors(self.source, self.source.split('parameter bypass')[0]))

    def test_labels_and_append_are_compatible(self):
        updated = self.source.replace('"Wet"', '"Wet Mix"') + 'parameter gain 12 "Gain" -12 12 0 1 0 "dB" automate\n'
        self.assertEqual(compatibility_errors(self.source, updated), [])
        self.assertEqual(compatibility_errors(self.source, self.source.replace('100 100', '100.0 100.0')), [])

    def test_rejects_malformed_discrete_contracts(self):
        for old, new in [('1 "" bypass', '0 "" bypass'), ('0 1 0 1 1', '0 2 0 1 1'),
                         ('0 1 0 1 1', '0 1 0.1 1 1'), ('0 1 0 1 1', '0 1 0 0.4 1'),
                         ('0 "%" automate', '65536 "%" automate'), ('automate', 'unknown')]:
            with self.subTest(new=new), self.assertRaises(SkellLangError):
                compile_controls(self.source.replace(old, new))

    def test_float32_collapse_is_rejected(self):
        with self.assertRaisesRegex(SkellLangError, 'float32'):
            compile_controls('skell-native 1\nparameter tiny 1 "Tiny" 999999.000001 999999.000002 999999.000001 1')

    def test_v2_128_controls_and_limit(self):
        source = 'skell-native 2\n' + ''.join(f'parameter p{i} {i+1} "P" 0 1 0 1 0 "" automate\n' for i in range(128))
        self.assertEqual(len(parse_controls(source)[1]), 128)
        with self.assertRaises(SkellLangError):
            parse_controls(source + 'parameter extra 129 "P" 0 1 0 1 0 "" automate\n')

    def test_encrypted_extension_fails_closed(self):
        from pathlib import Path
        with self.assertRaisesRegex(SkellLangError, 'encrypted'):
            read_source(Path('missing.skellenc'))

    def test_cli_does_not_overwrite_source(self):
        import subprocess, sys, tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'controls.skell'
            path.write_text(self.source)
            result = subprocess.run([sys.executable, '-m', 'skelllang.native_controls', str(path), str(path)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(path.read_text(), self.source)
