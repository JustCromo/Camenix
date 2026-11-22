"""Testi dell'app (it/en) e temi pronti: completi, coerenti, leggibili."""
import glob
import io
import json
import os
import re
import unittest
from contextlib import redirect_stdout

from camenix import cli, theme as th

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lum(h):
    def ch(i):
        c = int(h[i:i + 2], 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(1) + 0.7152 * ch(3) + 0.0722 * ch(5)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


class TestTexts(unittest.TestCase):
    def load(self, lang):
        with open(os.path.join(ROOT, "app", "i18n", lang + ".json"), encoding="utf-8") as f:
            return json.load(f)

    def test_same_keys_in_every_language(self):
        it, en = self.load("it"), self.load("en")
        self.assertEqual(set(it), set(en))
        for lang in (it, en):
            for k, v in lang.items():
                self.assertTrue(v.strip(), k)
                self.assertNotIn("<", v, k)                     # niente markup nei testi

    def test_every_key_used_in_qml_exists(self):
        it = self.load("it")
        used = set()
        for path in glob.glob(os.path.join(ROOT, "app", "*.qml")):
            with open(path, encoding="utf-8") as f:
                src = f.read()
            used |= set(re.findall(r'\btr\("([a-zA-Z0-9_.]+)"', src))
        used = {k for k in used if not k.endswith(".")}
        self.assertTrue(used)
        self.assertEqual(sorted(used - set(it)), [])

    def test_dynamic_keys_exist(self):
        it = self.load("it")
        for name in ("glass", "text", "accent", "terminal", "accent2", "secondary", "success", "warning", "error",
                     "borderFrom", "borderTo"):
            for suffix in (".title", ".desc"):
                self.assertIn("color." + name + suffix, it)
        for kind in ("wallpaper", "hyprland", "kitty", "mako", "rofi", "hyprlock", "quickshell", "other"):
            self.assertIn("kind." + kind, it)

    def test_placeholders_match(self):
        it, en = self.load("it"), self.load("en")
        for k in it:
            self.assertEqual(set(re.findall(r"\{\w+\}", it[k])), set(re.findall(r"\{\w+\}", en[k])), k)


class TestPresets(unittest.TestCase):
    def test_presets_are_valid_and_readable(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(cli.cmd_presets([], None, None), 0)
        presets = json.loads(buf.getvalue())
        self.assertGreaterEqual(len(presets), 5)
        for p in presets:
            c = p["colors"]
            self.assertEqual(len(c), 10, p["name"])
            self.assertGreaterEqual(contrast(c["text"], c["glass"]), 4.5, p["name"])        # testo leggibile
            self.assertGreaterEqual(contrast(p["terminal"]["foreground"], p["terminal"]["background"]), 4.5, p["name"])
        for path in glob.glob(os.path.join(ROOT, "presets", "*.json")):
            with open(path, encoding="utf-8") as f:
                _, problems = th.normalize(json.load(f))
            self.assertEqual(problems, [], path)


if __name__ == "__main__":
    unittest.main()
