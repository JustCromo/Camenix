"""Conti sui colori del selettore (app/color.js), eseguiti nel motore JavaScript di Qt.
Richiede PySide6; senza, il test viene saltato."""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from PySide6.QtQml import QJSEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "PySide6 non installato")
class TestColorJs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtCore import QCoreApplication
        cls.app = QCoreApplication.instance() or QCoreApplication([])
        cls.js = QJSEngine()
        with open(os.path.join(ROOT, "app", "color.js")) as f:
            src = f.read().replace(".pragma library", "", 1)
        r = cls.js.evaluate(src)
        assert not r.isError(), r.toString()

    def ev(self, expr):
        r = self.js.evaluate(expr)
        self.assertFalse(r.isError(), r.toString())
        return r.toVariant()

    def test_normhex(self):
        self.assertEqual(self.ev('normHex("#ffd25a")'), "#FFD25A")
        self.assertEqual(self.ev('normHex(" FFD25A ")'), "#FFD25A")
        for bad in ('"#FFD25"', '"#FFD25AA"', '"red"', '"#GG0000"', "null", "42", '"#FFF"', '"#FF0000; x"'):
            self.assertEqual(self.ev(f"normHex({bad})"), "", bad)

    def test_round_trip_every_step(self):
        # ogni colore passa da HSV e torna identico
        bad = self.ev("""(function () { let n = 0
            for (let r = 0; r < 256; r += 15) for (let g = 0; g < 256; g += 17) for (let b = 0; b < 256; b += 51) {
                const h = rgbToHsv(r, g, b), c = hsvToRgb(h.h, h.s, h.v)
                if (c.r !== r || c.g !== g || c.b !== b) n++ }
            return n })()""")
        self.assertEqual(bad, 0)

    def test_known_values(self):
        self.assertEqual(self.ev("hsvToHex(0, 1, 1)"), "#FF0000")
        self.assertEqual(self.ev("hsvToHex(120, 1, 1)"), "#00FF00")
        self.assertEqual(self.ev("hsvToHex(240, 1, 1)"), "#0000FF")
        self.assertEqual(self.ev("hsvToHex(360, 1, 1)"), "#FF0000")
        self.assertEqual(self.ev("hsvToHex(-120, 1, 1)"), "#0000FF")

    def test_hostile_numbers_are_clamped(self):
        self.assertEqual(self.ev("rgbToHex(300, -5, NaN)"), "#FF0000")
        self.assertEqual(self.ev("hsvToHex(NaN, 9, -1)"), "#000000")
        self.assertEqual(self.ev('rgbToHex("x", 1e9, undefined)'), "#00FF00")

    def test_palette(self):
        # 3/4 rosso, 1/4 blu, qualche pixel trasparente: rosso prima, blu dopo, trasparenti ignorati
        cols = self.ev("""(function () { const d = []
            for (let i = 0; i < 300; i++) d.push(250, 10, 10, 255)
            for (let i = 0; i < 100; i++) d.push(10, 10, 250, 255)
            for (let i = 0; i < 900; i++) d.push(0, 255, 0, 0)
            return palette(d, 8) })()""")
        self.assertEqual(cols[:2], ["#FA0A0A", "#0A0AFA"])
        self.assertEqual(len(cols), 2)

    def test_palette_empty_and_broken(self):
        self.assertEqual(self.ev("palette([], 8)"), [])
        self.assertEqual(self.ev("palette(null, 8)"), [])
        self.assertEqual(self.ev("palette([1, 2, 3], 8)"), [])       # pixel incompleto

    def test_palette_limits_and_distance(self):
        cols = self.ev("""(function () { const d = []
            for (let k = 0; k < 64; k++) for (let i = 0; i < 5; i++) d.push((k * 37) % 256, (k * 91) % 256, (k * 53) % 256, 255)
            return palette(d, 8) })()""")
        self.assertLessEqual(len(cols), 8)
        self.assertEqual(len(set(cols)), len(cols))


    def test_suggest(self):
        wall = '["#F2EDFA", "#FFE7A6", "#A7593A", "#251B34", "#DC9457", "#4788D5"]'
        for dark in ("false", "true"):
            p = self.ev(f"suggest({wall}, {dark})")
            self.assertEqual(set(p), {"glass", "text", "accent", "accent2", "secondary", "borderFrom", "borderTo"})
            for v in p.values():
                self.assertRegex(v, r"^#[0-9A-F]{6}$")
            self.assertGreaterEqual(self.ev(f'contrast("{p["text"]}", "{p["glass"]}")'), 4.5)   # testo leggibile
            self.assertEqual(p["accent"], p["borderFrom"])
            for k in ("accent", "accent2"):                                   # pallini e icone visibili
                self.assertGreaterEqual(self.ev(f'contrast("{p[k]}", "{p["glass"]}")'), 2.99, k)
        light, dark_ = self.ev(f"suggest({wall}, false)"), self.ev(f"suggest({wall}, true)")
        self.assertGreater(self.ev(f'lum("{light["glass"]}")'), self.ev(f'lum("{dark_["glass"]}")'))

    def test_suggest_pastel_wallpaper(self):
        # sfondo pastello (tipo Gudetama): l'accento giallo chiaro viene scurito quanto basta
        p = self.ev('suggest(["#D4C8FA", "#FFE7A6", "#FBF8FF", "#F8AD41"], false)')
        self.assertGreaterEqual(self.ev(f'contrast("{p["accent"]}", "{p["glass"]}")'), 2.99)
        self.assertGreaterEqual(self.ev(f'contrast("{p["accent2"]}", "{p["glass"]}")'), 2.99)

    def test_suggest_hostile_or_empty(self):
        self.assertIsNone(self.ev("suggest([], false)"))
        self.assertIsNone(self.ev("suggest(null, true)"))
        self.assertIsNone(self.ev('suggest(["red", "#12", "<script>"], false)'))
        p = self.ev('suggest(["#808080"], true)')                     # sfondo grigio: niente tinta, ma funziona
        self.assertGreaterEqual(self.ev(f'contrast("{p["text"]}", "{p["glass"]}")'), 4.5)


if __name__ == "__main__":
    unittest.main()
