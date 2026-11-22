"""Funzioni del motore usate dall'app: sfumature, bozza, importazione sfondo, ripristino, menu."""
import json
import os
import pathlib
import stat
import unittest

from camenix import apply as ap, derive as dv, files, theme as th
from tests.fakehome import FakeHome, png


class TestDerive(unittest.TestCase):
    def test_defaults_are_reproduced_exactly(self):
        d = th.defaults()
        for derived, base in dv.FAMILY.items():
            self.assertEqual(dv.shade(d[base], d[derived], d[base]), d[derived], derived)

    def test_only_changed_family_moves(self):
        d = th.defaults()
        c = dict(d, accent="#3FE0D0")
        out = dv.derive(c, d)
        for derived, base in dv.FAMILY.items():
            if base == "accent":
                self.assertNotEqual(out[derived], d[derived], derived)
            else:
                self.assertEqual(out[derived], d[derived], derived)

    def test_extremes_stay_valid(self):
        d = th.defaults()
        for color in ("#000000", "#FFFFFF", "#FF0000", "#808080", "#010203"):
            out = dv.derive(dict(d, accent=color, text=color, glass=color, secondary=color), d)
            for v in out.values():
                self.assertRegex(v, th.HEX)

    def test_grey_base_gives_grey_shades(self):
        d = th.defaults()
        out = dv.derive(dict(d, accent="#808080"), d)
        r, g, b = (int(out["accentSoft"][i:i + 2], 16) for i in (1, 3, 5))
        self.assertLessEqual(max(r, g, b) - min(r, g, b), 1)


class TestAppEngine(FakeHome):
    def draft(self, data):
        return json.dumps(data) if not isinstance(data, str) else data

    def test_derive_draft(self):
        ap.setup()
        t, _, _ = th.read()
        t["colors"]["accent"] = "#3FE0D0"
        out = ap.derive_draft(self.draft(t))
        self.assertEqual(out["colors"]["accent"], "#3FE0D0")
        self.assertNotEqual(out["colors"]["accentSoft"], th.defaults()["accentSoft"])

    def test_draft_hostile(self):
        for bad in ('{"colors": {"text": "x"', "A" * (th.MAX_BYTES + 5), None, 42):
            with self.assertRaises((ValueError, TypeError)):
                ap.parse_draft(bad)
        for odd in ("[]", '{"colors": {"text": "red; }"}}', '{"wallpaper": {"home": "/x/a.png\\nexec-once = rm"}}'):
            theme = ap.parse_draft(odd)
            self.assertEqual(theme["colors"], th.defaults())
            self.assertIsNone(theme["wallpaper"]["home"])

    def test_import_wallpaper_copies_and_dedupes(self):
        a = ap.import_wallpaper(self.wall)
        b = ap.import_wallpaper(self.wall)
        self.assertEqual(a, b)
        self.assertTrue(a.startswith(ap.cfg("wallpapers")))
        self.assertTrue(a.endswith(".png"))
        self.assertEqual(stat.S_IMODE(os.stat(ap.cfg("wallpapers")).st_mode), 0o700)
        os.unlink(self.wall)                       # l'originale sparisce: la copia resta
        self.assertTrue(os.path.exists(a))

    def test_import_rejects_non_images(self):
        fake = self.p("trappola.png")
        pathlib.Path(fake).write_text("#!/bin/sh\nrm -rf ~\n")
        self.assertIsNone(ap.import_wallpaper(fake))
        self.assertIsNone(ap.import_wallpaper("/dev/zero"))
        self.assertIsNone(ap.import_wallpaper(self.p("non-esiste.png")))

    def test_reset_colors_keeps_wallpaper(self):
        ap.setup()
        t, _, _ = th.read()
        wall = t["wallpaper"]["home"]
        t["colors"]["accent"] = "#3FE0D0"
        ap.change_theme(t)
        rep = ap.reset_colors()
        self.assertTrue(rep.as_dict()["ok"])
        t2, _, _ = th.read()
        self.assertEqual(t2["colors"], th.defaults())
        self.assertEqual(t2["wallpaper"]["home"], wall)

    def test_changed_from_defaults(self):
        t = th.default_theme()
        self.assertEqual(ap.changed_from_defaults(t), 0)
        t["colors"]["accent"] = "#000000"
        self.assertEqual(ap.changed_from_defaults(t), 1)

    def test_desktop_entry(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = ap.install_desktop_entry(root)
        text = pathlib.Path(path).read_text()
        self.assertIn("Name=Camenix", text)
        self.assertIn(f"Exec={root}/bin/camenix", text)
        with self.assertRaises(files.UnsafeFile):
            ap.install_desktop_entry("/tmp/evil;rm -rf ~")


if __name__ == "__main__":
    unittest.main()
