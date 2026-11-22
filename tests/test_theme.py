"""Formato del tema: validazione, lettura sicura e scrittura atomica (anche contro input ostili)."""
import json
import pathlib
import os
import stat
import tempfile
import unittest

from camenix import theme as th


class TempConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._old = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = self.tmp
        self.path = th.theme_path()

    def tearDown(self):
        if self._old is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old

    def put(self, text):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(text)


class TestRoles(unittest.TestCase):
    def test_roles_unique_and_valid(self):
        keys = [r["key"] for r in th.roles()]
        self.assertEqual(len(keys), len(set(keys)))
        for r in th.roles():
            self.assertRegex(r["default"], th.HEX)
            self.assertIn(r["group"], ("base", "derived"))

    def test_preset_matches_defaults(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        preset = json.loads(pathlib.Path(here, "presets", "gudetama.json").read_text())
        self.assertEqual(preset["colors"], th.defaults())

    def test_quickshell_theme_has_every_role(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        qml = pathlib.Path(here, "integrations", "quickshell", "Theme.qml").read_text(encoding="utf-8")
        for key, value in th.defaults().items():
            self.assertIn(f'{key}: "{value}"', qml)
            self.assertIn(f"readonly property color {key}: values.{key}", qml)


class TestNormalize(unittest.TestCase):
    def test_full_valid_theme(self):
        t = th.default_theme("Prova")
        t["colors"]["text"] = "#abcdef"
        out, problems = th.normalize(t)
        self.assertEqual(problems, [])
        self.assertEqual(out["colors"]["text"], "#ABCDEF")
        self.assertEqual(out["name"], "Prova")

    def test_not_an_object(self):
        for bad in ([], "x", 42, None):
            out, problems = th.normalize(bad)
            self.assertEqual(out["colors"], th.defaults())
            self.assertTrue(problems)

    def test_hostile_colors_fall_back(self):
        out, problems = th.normalize({"format": th.FORMAT, "version": 1, "colors": {
            "text": "red; } Rectangle {", "glass": "#12345", "accent": ["#FF0000"],
            "error": "#GGGGGG", "accent2": "#FF0000FF", "success": " #2F7A4B"}})
        self.assertEqual(out["colors"], th.defaults())
        self.assertEqual(len(problems), 6)

    def test_unknown_roles_ignored(self):
        out, problems = th.normalize({"format": th.FORMAT, "version": 1,
                                      "colors": {"__proto__": "#FF0000", "constructor": "#FF0000"}})
        self.assertNotIn("__proto__", out["colors"])
        self.assertEqual(len(problems), 2)

    def test_name_is_cleaned(self):
        out, _ = th.normalize({"name": "\x1b[31mEvil\x00" + "x" * 500})
        self.assertNotIn("\x1b", out["name"])
        self.assertNotIn("\x00", out["name"])
        self.assertLessEqual(len(out["name"]), 60)

    def test_wallpaper_paths(self):
        good = {"home": "/home/a/b.png", "lock": None}
        out, problems = th.normalize({"format": th.FORMAT, "version": 1, "wallpaper": good})
        self.assertEqual(out["wallpaper"]["home"], "/home/a/b.png")
        self.assertEqual(problems, [])
        for bad in ("relative.png", "/etc/shadow", "/x/y.png\nexec rm -rf ~", "/x/\x00.png", "/x/" + "a" * 5000 + ".png", 12):
            out, problems = th.normalize({"format": th.FORMAT, "version": 1, "wallpaper": {"home": bad}})
            self.assertIsNone(out["wallpaper"]["home"], bad)
            self.assertTrue(problems)

    def test_wallpaper_flags_only_bool(self):
        out, _ = th.normalize({"wallpaper": {"lock_same": "no", "lock_blur": 0}})
        self.assertIs(out["wallpaper"]["lock_same"], True)
        self.assertIs(out["wallpaper"]["lock_blur"], True)


class TestReadWrite(TempConfig):
    def test_missing_file(self):
        theme, problems, exists = th.read()
        self.assertFalse(exists)
        self.assertEqual(theme["colors"], th.defaults())

    def test_roundtrip_and_permissions(self):
        t = th.default_theme("Mio")
        t["colors"]["accent"] = "#112233"
        th.write(t)
        theme, problems, exists = th.read()
        self.assertTrue(exists)
        self.assertEqual(problems, [])
        self.assertEqual(theme["colors"]["accent"], "#112233")
        mode = stat.S_IMODE(os.stat(self.path).st_mode)
        self.assertEqual(mode, 0o644)
        self.assertEqual(stat.S_IMODE(os.stat(os.path.dirname(self.path)).st_mode) & 0o077, 0)

    def test_write_normalizes_hostile_input(self):
        th.write({"colors": {"text": "javascript:alert(1)"}})
        theme, _, _ = th.read()
        self.assertEqual(theme["colors"]["text"], th.defaults()["text"])

    def test_broken_json(self):
        self.put('{"colors": {"text": "#FF0000"')
        theme, problems, _ = th.read()
        self.assertEqual(theme["colors"], th.defaults())
        self.assertEqual(problems[0][0], "problem.not_json")

    def test_too_big(self):
        self.put('{"x": "' + "A" * (th.MAX_BYTES + 10) + '"}')
        _, problems, _ = th.read()
        self.assertEqual(problems[0][0], "problem.too_big")

    def test_symlink_is_refused(self):
        target = os.path.join(self.tmp, "elsewhere.json")
        pathlib.Path(target).write_text("{}")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        os.symlink(target, self.path)
        with self.assertRaises(th.UnsafePath):
            th.read()
        with self.assertRaises(th.UnsafePath):
            th.write(th.default_theme())
        self.assertEqual(pathlib.Path(target).read_text(), "{}")          # il file puntato non viene toccato

    def test_directory_is_refused(self):
        os.makedirs(self.path)
        with self.assertRaises(th.UnsafePath):
            th.read()

    def test_no_temp_files_left(self):
        th.write(th.default_theme())
        th.write(th.default_theme())
        leftovers = [f for f in os.listdir(os.path.dirname(self.path)) if f.startswith(".theme-")]
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
