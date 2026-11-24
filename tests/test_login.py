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
        self.old = login.DIR
        login.DIR = self.dir
        self.img = png(os.path.join(self.base, "sfondo.png"))

    def tearDown(self):
        login.DIR = self.old

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
        self.assertEqual(pathlib.Path(login.DIR, login.NAME).read_bytes(), pathlib.Path(self.wall).read_bytes())

    def test_apply_silent_when_not_prepared(self):
        login.DIR = self.p("non-preparata")
        rep = ap.change_theme(self.theme_with_wall()).as_dict()
        self.assertTrue(rep["ok"])
        self.assertEqual(rep["login"], "off")
        self.assertFalse(os.path.exists(login.DIR))


if __name__ == "__main__":
    unittest.main()
