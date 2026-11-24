"""Sfondo della schermata di accesso: copia sicura in una cartella preparata dall'utente."""
import json
import os
import pathlib
import stat
import tempfile
import unittest

from camenix import apply as ap, login, theme as th
from tests.fakehome import FakeHome, png


class TestLoginSync(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.dir = os.path.join(self.base, "camenix")
        os.mkdir(self.dir, 0o755)
        os.chmod(self.dir, 0o755)
        self.old = login.DIR, login.lock_look
        login.DIR = self.dir
        login.lock_look = lambda: (0, 1.0, [1920, 1080])      # copia nitida: nessuna lettura di file veri
        self.img = png(os.path.join(self.base, "sfondo.png"))

    def tearDown(self):
        login.DIR, login.lock_look = self.old

    def out(self):
        return pathlib.Path(self.dir, login.NAME)

    def test_copy_then_same(self):
        self.assertEqual(login.sync(self.img), "copied")
        self.assertEqual(self.out().read_bytes(), pathlib.Path(self.img).read_bytes())
        self.assertEqual(stat.S_IMODE(self.out().stat().st_mode), 0o644)   # SDDM deve poterlo leggere
        self.assertEqual(login.sync(self.img), "same")
        other = png(os.path.join(self.base, "altro.png"), color=(10, 20, 30))
        self.assertEqual(login.sync(other), "copied")
        self.assertEqual(self.out().read_bytes(), pathlib.Path(other).read_bytes())
        self.assertEqual([n for n in os.listdir(self.dir) if n != login.NAME], [])   # niente temporanei

    def test_off_when_missing(self):
        login.DIR = os.path.join(self.base, "non-esiste")
        self.assertEqual(login.sync(self.img), "off")
        self.assertFalse(login.enabled())

    def test_refuses_symlinked_dir(self):
        # un collegamento al posto della cartella (verso un posto scelto da altri): non si scrive
        real = os.path.join(self.base, "altrove")
        os.mkdir(real, 0o755)
        link = os.path.join(self.base, "link")
        os.symlink(real, link)
        login.DIR = link
        self.assertEqual(login.sync(self.img), "off")
        self.assertEqual(os.listdir(real), [])

    def test_refuses_writable_by_others(self):
        for mode in (0o775, 0o757, 0o777):
            os.chmod(self.dir, mode)
            self.assertEqual(login.sync(self.img), "off", oct(mode))
        self.assertFalse(self.out().exists())

    def test_symlink_in_place_of_file_is_replaced_not_followed(self):
        victim = os.path.join(self.base, "vittima.txt")
        pathlib.Path(victim).write_text("non toccare")
        os.symlink(victim, self.out())
        self.assertEqual(login.sync(self.img), "copied")
        self.assertEqual(pathlib.Path(victim).read_text(), "non toccare")
        self.assertFalse(self.out().is_symlink())

    def test_rejects_non_images(self):
        txt = os.path.join(self.base, "x.png")
        pathlib.Path(txt).write_text("<script>")
        for bad in (txt, "relativo.png", "", None, "/etc/shadow", self.base, os.path.join(self.base, "manca.png")):
            self.assertEqual(login.sync(bad), "bad", bad)
        self.assertFalse(self.out().exists())

    def test_image_for(self):
        self.assertEqual(login.image_for({"wallpaper": {"home": "/a", "lock": "/b", "lock_same": True}}), "/a")
        self.assertEqual(login.image_for({"wallpaper": {"home": "/a", "lock": "/b", "lock_same": False}}), "/b")
        self.assertEqual(login.image_for({"wallpaper": {"home": "/a", "lock": None, "lock_same": False}}), "/a")
        self.assertIsNone(login.image_for({"wallpaper": {}}))
        self.assertIsNone(login.image_for("x"))


class TestApplyLogin(FakeHome):
    def setUp(self):
        super().setUp()
        self.old = login.DIR
        ap.setup()

    def tearDown(self):
        login.DIR = self.old
        super().tearDown()

    def theme_with_wall(self):
        t, _, _ = th.read()
        t["wallpaper"]["home"] = self.wall
        return t

    def test_apply_copies_when_prepared(self):
        login.DIR = self.p("var-lib-camenix")
        os.mkdir(login.DIR, 0o755)
        os.chmod(login.DIR, 0o755)
        rep = ap.change_theme(self.theme_with_wall()).as_dict()
        self.assertTrue(rep["ok"])
        self.assertEqual(rep["login"], "copied")
        # la hyprlock.conf finta sfoca (blur_passes = 3): sullo schermo di accesso va la versione sfocata
        from PIL import Image
        with Image.open(pathlib.Path(login.DIR, login.NAME)) as im:
            self.assertEqual((im.format, im.size), ("JPEG", (1920, 1080)))

    def test_apply_silent_when_not_prepared(self):
        login.DIR = self.p("non-preparata")
        rep = ap.change_theme(self.theme_with_wall()).as_dict()
        self.assertTrue(rep["ok"])
        self.assertEqual(rep["login"], "off")
        self.assertFalse(os.path.exists(login.DIR))


class TestLookLikeLock(FakeHome):
    """L'aspetto segue hyprlock.conf: sfocatura e luminosità, oppure immagine nitida."""
    def setUp(self):
        super().setUp()
        from PIL import Image
        self.Image = Image
        # immagine a righe: la sfocatura le appiattisce, quella nitida no
        im = Image.new("RGB", (400, 300))
        im.putdata([(255, 255, 255) if (x // 4) % 2 else (0, 0, 0) for y in range(300) for x in range(400)])
        self.src = self.p("righe.png")
        im.save(self.src)
        self.data = pathlib.Path(self.src).read_bytes()

    def conf(self, text):
        pathlib.Path(self.p(".config/hypr/hyprlock.conf")).write_text(text)

    def spread(self, data):
        import io
        with self.Image.open(io.BytesIO(data)) as im:
            px = list(im.convert("L").crop((100, 100, 200, 101)).getdata())
        return max(px) - min(px), sum(px) / len(px)

    def test_blur_and_brightness_from_hyprlock(self):
        self.conf("background {\n    path = ~/x.png\n    blur_passes = 3\n    blur_size = 7\n    brightness = 0.5\n}\n")
        radius, bright, screen = login.lock_look()
        self.assertEqual((radius, bright, screen), (28, 0.5, [1920, 1080]))
        out = login.styled(self.data, radius, bright, screen)
        spread, mean = self.spread(out)
        self.assertLess(spread, 40)                  # righe sparite: sfocata
        self.assertLess(mean, 100)                   # più scura (metà di ~128)

    def test_sharp_when_hyprlock_does_not_blur(self):
        self.conf("background {\n    path = ~/x.png\n    blur_passes = 0\n    brightness = 0.5\n}\n")
        self.assertEqual(login.lock_look()[:2], (0, 1.0))
        self.assertIsNone(login.styled(self.data, *login.lock_look()))   # si copia l'originale

    def test_no_hyprlock_means_sharp(self):
        os.unlink(self.p(".config/hypr/hyprlock.conf"))
        self.assertEqual(login.lock_look()[:2], (0, 1.0))

    def test_hostile_hyprlock_values_are_bounded(self):
        self.conf("background {\n    blur_passes = 99\n    blur_size = 199\n    brightness = 1e9\n}\n")
        radius, bright, _ = login.lock_look()
        self.assertLessEqual(radius, 400)
        self.assertLessEqual(bright, 2.0)

    def test_without_pillow_copies_sharp(self):
        import builtins
        real_import = builtins.__import__
        def no_pil(name, *a, **k):
            if name == "PIL" or name.startswith("PIL."):
                raise ImportError(name)
            return real_import(name, *a, **k)
        builtins.__import__ = no_pil
        try:
            self.assertIsNone(login.styled(self.data, 28, 0.8, [1920, 1080]))
        finally:
            builtins.__import__ = real_import

    def test_bad_images_fall_back(self):
        import io
        bomb = io.BytesIO()
        self.Image.new("1", (12000, 9000)).save(bomb, "PNG")         # 108 milioni di pixel: troppo
        gif = io.BytesIO()
        self.Image.new("RGB", (10, 10)).save(gif, "GIF")
        for data in (b"", b"\x89PNG\r\n\x1a\n" + b"x" * 100, bomb.getvalue(), gif.getvalue()):
            self.assertIsNone(login.styled(data, 28, 0.8, [1920, 1080]))


if __name__ == "__main__":
    unittest.main()
