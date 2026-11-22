"""Modelli: render(adopt(file)) == file, segnaposto sconosciuti, valori sicuri."""
import unittest

from camenix import render, theme as th


class TestRender(unittest.TestCase):
    def setUp(self):
        self.theme = th.default_theme()
        self.theme["wallpaper"]["home"] = "/home/u/sfondo.png"

    def roundtrip(self, text):
        tpl, n = render.adopt(text, self.theme)
        self.assertEqual(render.render(tpl, self.theme), text)
        return tpl, n

    def test_formats_roundtrip(self):
        for text in ("background-color=#FBF8FFD9\ntext-color=#2B2236\n",
                     "color = rgba(2B2236ee)\nouter = rgba(D4C8FAee) rgba(FFD25Aee) 45deg\n",
                     'active = {"rgba(E0B0FFff)", "rgba(FFBF00ff)"}\n',
                     "prugna: #2b2236;\ntuorlo: #FFD25A;\n",
                     "progress-color=over #FFD25A\n"):
            tpl, n = self.roundtrip(text)
            self.assertGreater(n, 0, text)
            self.assertNotRegex(render.PH.sub("", tpl), r"(?i)(2B2236|FFD25A|E0B0FF)")

    def test_unknown_colors_and_lookalikes_untouched(self):
        for text in ("#123456", "#FFD25A0", "#FFD25AFFAA", "id: FFD25A", "#ffd25", "0xFFD25A"):
            tpl, n = render.adopt(text, self.theme)
            self.assertEqual((tpl, n), (text, 0), text)

    def test_alpha_and_case_kept(self):
        tpl, _ = render.adopt("#ffd25af2", self.theme)
        self.assertEqual(tpl, "#{{cmx:accent:lower}}f2")
        t2 = th.default_theme()
        t2["colors"]["accent"] = "#3FE0D0"
        self.assertEqual(render.render(tpl, t2), "#3fe0d0f2")

    def test_same_color_two_roles_first_wins(self):
        tpl, _ = render.adopt("#E8892A", self.theme)
        self.assertEqual(tpl, "#{{cmx:accent2}}")

    def test_wallpaper_path(self):
        tpl, n = render.adopt("    path = /home/u/sfondo.png\n    path = /altro.png\n", self.theme)
        self.assertIn("{{cmx:wallpaper.lock}}", tpl)
        self.assertIn("/altro.png", tpl)
        self.assertEqual(n, 1)

    def test_lock_wallpaper_choice(self):
        t = self.theme
        t["wallpaper"].update(lock="/home/u/blocco.png", lock_same=False)
        self.assertEqual(render.render("{{cmx:wallpaper.lock}}", t), "/home/u/blocco.png")
        t["wallpaper"]["lock_same"] = True
        self.assertEqual(render.render("{{cmx:wallpaper.lock}}", t), "/home/u/sfondo.png")

    def test_unknown_placeholder_fails(self):
        with self.assertRaises(render.RenderError):
            render.render("{{cmx:__class__}}", self.theme)
        with self.assertRaises(render.RenderError):
            render.render("{{cmx:wallpaper.lock}}", th.default_theme())     # nessuno sfondo
        with self.assertRaises(render.RenderError):
            render.render("{{cmx:../../etc/passwd}}", self.theme)          # segnaposto malformato

    def test_values_cannot_inject(self):
        """Anche con un tema ostile, nel file finiscono solo 6 cifre esadecimali o percorsi validati."""
        bad, problems = th.normalize({"format": th.FORMAT, "version": 1,
                                      "colors": {"accent": "FFD25A\nexec = rm -rf ~"},
                                      "wallpaper": {"home": "/x/a.png\nexec-once = curl evil"}})
        out = render.render("c=#{{cmx:accent}}\n", bad)
        self.assertEqual(out, "c=#FFD25A\n")
        self.assertIsNone(bad["wallpaper"]["home"])
        self.assertEqual(len(problems), 2)


if __name__ == "__main__":
    unittest.main()
