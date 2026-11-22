"""Il selettore dei colori usato col mouse e con la tastiera (simulati), sull'app vera e una home finta.
Richiede PySide6; senza, il test viene saltato."""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.fakehome import CONFIGS, png

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    import PySide6  # noqa: F401
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "PySide6 non installato")
class TestPicker(unittest.TestCase):
    def test_mouse_and_keyboard(self):
        home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, home, True)
        for rel, text in CONFIGS.items():
            p = pathlib.Path(home, rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        wall = png(os.path.join(home, "sfondo.png"))
        env = {"HOME": home, "PATH": "/usr/bin:/bin", "QT_QPA_PLATFORM": "offscreen", "LANG": "C.UTF-8"}
        engine = [sys.executable, os.path.join(ROOT, "bin", "camenix-engine")]
        subprocess.run(engine + ["setup"], env=env, capture_output=True, timeout=60, check=True)
        subprocess.run(engine + ["wallpaper", "set", wall], env=env, capture_output=True, timeout=60)
        shots = os.path.join(home, "foto")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "app_picker_run.py"), shots],
                           env=env, capture_output=True, text=True, timeout=120)
        s = json.loads(pathlib.Path(shots, "report.json").read_text())
        self.assertEqual(s["errors"], [], r.stderr[-2000:])
        s = s["steps"]
        self.assertEqual(s["palettes"][0], "In uso")
        self.assertIn("Sfondo scuro", s["palettes"])                     # palette proposte dallo sfondo
        self.assertTrue(s["dirty_after_palette"])
        r_, g_, b_ = (int(s["dark_glass"][i:i + 2], 16) for i in (1, 3, 5))
        self.assertLess(r_ + g_ + b_, 200)                               # "scuro" è davvero scuro
        self.assertFalse(s["dirty_after_back"])                          # "In uso" torna al tema applicato
        self.assertEqual(s["changes"], 2)                                # accento e bordo
        self.assertEqual(s["hover_zones"], ["pills", "menu", "lock"])     # il passaggio illumina l'anteprima
        self.assertEqual(s["editor_role"], "accent")
        self.assertTrue(s["wall_colors"])                                # colori letti dallo sfondo
        self.assertEqual(s["hue_after_ring"], 120)                       # anello: tinta verde
        self.assertEqual(s["hex_after_square"], "#3F7F3F")               # quadrato: metà saturazione/luminosità
        self.assertEqual(s["hex_after_slider"], "#FF7F3F")               # R oltre la fine: fermo a 255
        self.assertEqual(s["hex_after_wall_dot"], s["wall_colors"][-1])  # pallino dello sfondo
        self.assertEqual(s["open_after_bad_enter"], "accent")            # "12" + Invio: non conferma niente
        self.assertEqual(s["hex_typed"], "#3FE0D0")                      # lettere non valide rifiutate
        self.assertTrue(s["editor_closed"])
        self.assertEqual(s["draft_accent"], "#3FE0D0")
        self.assertTrue(s["dirty"] and s["apply_enabled"])               # Applica si accende
        self.assertEqual(s["theme_untouched"], "#FFD25A")                # niente cambia prima di Applica
        self.assertEqual(s["draft_border"], "#FF00AA")                   # bordo scelto a mano, non ricalcolato
        self.assertEqual(s["applied"], ["#3FE0D0", "#FF00AA"])
        self.assertTrue(s["hypr_border"])                                # arrivato fino a Hyprland
        self.assertFalse(s["awaiting"])                                  # "Tieni" chiude il paracadute
        self.assertEqual(s["fader"], [1, 1])                             # dissolvenza: foto prima, sfuma dopo
        self.assertFalse(s["pending_after_keep"])                        # e il guardiano non tornerà indietro
        self.assertEqual(s["kept"], "#3FE0D0")


    def test_first_run_on_a_new_desktop(self):
        # un desktop "di fabbrica": nessun tema Camenix, config di esempio di Hyprland, kitty e mako
        from tests.test_detect import STOCK
        home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, home, True)
        for rel, text in STOCK.items():
            p = pathlib.Path(home, rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        hypr_before = pathlib.Path(home, ".config/hypr/hyprland.conf").read_text()
        env = {"HOME": home, "PATH": "/usr/bin:/bin", "QT_QPA_PLATFORM": "offscreen", "LANG": "C.UTF-8"}
        shots = os.path.join(home, "foto")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "app_picker_run.py"), shots, "--first"],
                           env=env, capture_output=True, text=True, timeout=120)
        s = json.loads(pathlib.Path(shots, "report.json").read_text())
        self.assertEqual(s["errors"], [], r.stderr[-2000:])
        s = s["steps"]
        self.assertTrue(s["first_run"] and s["welcome_visible"])
        self.assertFalse(s["theme_before_start"])                        # prima di "Inizia" non scrive niente
        self.assertEqual(s["detected_border"], "#33CCFF")                # colori letti dal desktop
        self.assertFalse(s["first_run_after"])
        self.assertEqual(s["theme_border"], "#33CCFF")
        self.assertEqual(s["draft_border_start"], "#33CCFF")
        self.assertEqual(s["applied"], ["#3FE0D0", "#FF00AA"])          # poi tutto funziona come sempre
        hypr = pathlib.Path(home, ".config/hypr/hyprland.conf").read_text()
        self.assertIn("rgba(ff00aaee)", hypr)                           # il bordo arriva a Hyprland
        self.assertEqual(hypr.replace("ff00aa", "33ccff"), hypr_before)  # e nient'altro cambia nel file


if __name__ == "__main__":
    unittest.main()
