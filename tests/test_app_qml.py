"""L'app vera (QML) con il motore vero, su una home finta: carica, modifica, applica, paracadute, annulla.
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
class TestApp(unittest.TestCase):
    def test_full_flow(self):
        home = tempfile.mkdtemp()
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
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "app_run.py"), shots],
                           env=env, capture_output=True, text=True, timeout=120)
        report = json.loads(pathlib.Path(shots, "report.json").read_text())
        s = report["steps"]
        self.assertEqual(report["errors"], [], r.stderr[-2000:])
        self.assertEqual(s["loaded"], "#FFD25A")
        self.assertEqual(s["draft_accent"], "#3FE0D0")
        self.assertNotEqual(s["draft_soft"], "#FFE7A6")          # le sfumature seguono
        self.assertTrue(s["dirty"])
        self.assertEqual(s["theme_untouched"], "#FFD25A")        # il desktop non cambia prima di Applica
        self.assertEqual(s["applied_accent"], "#3FE0D0")
        self.assertTrue(s["awaiting_keep"])                       # paracadute attivo
        self.assertEqual(s["reverted_accent"], "#FFD25A")        # Annulla torna indietro
        self.assertEqual(s["prefs"], {"mode": "dark"})            # chiaro/scuro ricordato
        mako = pathlib.Path(home, ".config/mako/config").read_text()
        self.assertIn("#FFD25A", mako)                             # anche le config sono tornate
        shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
