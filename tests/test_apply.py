"""Applica: tutto o niente, copie di sicurezza, ricariche, storico, sfondo, file pericolosi."""
import json
import os
import pathlib
import stat
import unittest

from camenix import apply as ap, files, theme as th, wallpaper
from tests.fakehome import FakeHome, png


class TestSetup(FakeHome):
    def test_setup_keeps_files_identical(self):
        before = self.snapshot()
        act = ap.setup()
        self.assertEqual(act["wallpaper"], os.path.realpath(self.wall))
        self.assertEqual(len(act["adopted"]), 4)
        after = self.snapshot()
        for rel in before:
            if rel.endswith("hyprlock.conf"):
                self.assertEqual(after[rel], before[rel].replace("~/sfondo.png", os.path.realpath(self.wall)))
            elif rel.endswith("kitty.conf"):
                self.assertTrue(after[rel].startswith(before[rel].rstrip("\n")))
                self.assertIn(ap.KITTY_INCLUDE, after[rel])
            else:
                self.assertEqual(after[rel], before[rel], rel)

    def test_setup_twice_is_idempotent(self):
        ap.setup()
        once = self.snapshot()
        act = ap.setup()
        self.assertEqual(act["adopted"], [])
        self.assertIsNone(act["kitty"])
        self.assertEqual(self.snapshot(), once)

    def test_dry_run_changes_nothing(self):
        before = self.snapshot()
        ap.setup(dry_run=True)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(os.path.exists(th.theme_path()))

    def test_backups_and_private_dirs(self):
        ap.setup()
        backups = ap.cfg("backups")
        copies = [p for p in pathlib.Path(backups).rglob("*") if p.is_file()]
        self.assertGreaterEqual(len(copies), 5)
        for d in (backups, ap.cfg("templates")):
            self.assertEqual(stat.S_IMODE(os.stat(d).st_mode), 0o700)

    def test_first_apply_does_not_restart_wallpaper(self):
        ap.setup()
        rep = ap.apply()
        self.assertTrue(rep.as_dict()["ok"])
        self.assertIsNone(rep.wallpaper)
        self.assertNotIn(["swaybg", "SIGTERM"], self.calls)


class TestApply(FakeHome):
    def setUp(self):
        super().setUp()
        ap.setup()
        ap.apply()
        self.calls.clear()

    def change(self, **colors):
        t, _, _ = th.read()
        t["colors"].update(colors)
        return ap.change_theme(t)

    def test_change_updates_files_and_reloads(self):
        rep = self.change(accent="#3FE0D0")
        self.assertTrue(rep.as_dict()["ok"])
        self.assertIn("#3FE0D0", self.read(".config/mako/config"))
        self.assertIn("rgba(3FE0D0ee)", self.read(".config/hypr/hyprlock.conf"))
        self.assertIn(["makoctl", "reload"], self.calls)
        self.assertNotIn(["hyprctl", "reload"], self.calls)        # i bordi non sono cambiati

    def test_border_change_reloads_hyprland(self):
        self.change(borderFrom="#FF00AA")
        self.assertIn('"rgba(FF00AAff)"', self.read(".config/hypr/config/decoration.lua"))
        self.assertIn(["hyprctl", "reload"], self.calls)

    def test_unknown_colors_survive(self):
        self.change(accent="#3FE0D0")
        self.assertIn("#123456", self.read(".config/rofi/config.rasi"))

    def test_manual_edit_blocks_everything(self):
        pathlib.Path(self.p(".config/mako/config")).write_text("mia modifica\n")
        before = self.snapshot()
        theme_before = pathlib.Path(th.theme_path()).read_text()
        rep = self.change(accent="#3FE0D0")
        self.assertFalse(rep.as_dict()["ok"])
        self.assertEqual(rep.conflicts[0]["file"], os.path.realpath(self.p(".config/mako/config")))
        self.assertEqual(self.snapshot(), before)                   # nessun file toccato
        self.assertEqual(pathlib.Path(th.theme_path()).read_text(), theme_before)   # tema invariato
        self.assertEqual(self.calls, [])

    def test_adopt_keeps_manual_edit(self):
        path = self.p(".config/mako/config")
        pathlib.Path(path).write_text(self.read(".config/mako/config") + "# mia\n")
        state = ap.load_state()
        ap.adopt_file(path, th.read()[0], state)
        ap.save_state(state)
        self.assertTrue(self.change(accent="#3FE0D0").as_dict()["ok"])
        self.assertTrue(self.read(".config/mako/config").endswith("# mia\n"))

    def test_undo_restores_exactly(self):
        before = self.snapshot()
        self.change(accent="#3FE0D0", text="#000000")
        self.assertNotEqual(self.snapshot(), before)
        rep = ap.undo()
        self.assertTrue(rep.as_dict()["ok"])
        self.assertEqual(self.snapshot(), before)

    def test_quick_changes_undo_in_order(self):
        """Due cambi nello stesso secondo, poi due annulla: si torna esattamente all'inizio."""
        before = self.snapshot()
        theme_before = th.read()[0]["colors"]
        self.change(accent="#3FE0D0")
        self.change(accent2="#2F7FB8")
        ap.undo()
        self.assertEqual(th.read()[0]["colors"]["accent"], "#3FE0D0")
        self.assertEqual(th.read()[0]["colors"]["accent2"], theme_before["accent2"])
        ap.undo()
        self.assertEqual(th.read()[0]["colors"], theme_before)
        self.assertEqual(self.snapshot(), before)

    def test_history_order_many_fast_changes(self):
        for i in range(10):
            self.change(accent="#%06X" % (i + 1))
        for i in reversed(range(10)):
            ap.undo()
            expected = "#%06X" % i if i else th.defaults()["accent"]
            self.assertEqual(th.read()[0]["colors"]["accent"], expected)

    def test_undo_empty(self):
        for p in pathlib.Path(ap.cfg("history")).glob("*.json") if os.path.isdir(ap.cfg("history")) else []:
            p.unlink()
        self.assertIsNone(ap.undo())

    def test_history_is_bounded(self):
        for i in range(ap.HISTORY_KEEP + 5):
            self.change(accent="#%06X" % (i + 1))
        self.assertEqual(len(list(pathlib.Path(ap.cfg("history")).glob("*.json"))), ap.HISTORY_KEEP)

    def test_kitty_colors_generated(self):
        self.change(accent="#3FE0D0")
        t, _, _ = th.read()
        t["terminal"]["background"] = "#1E1528"
        ap.change_theme(t)
        self.assertIn("background #1E1528", pathlib.Path(ap.cfg("generated", "kitty.conf")).read_text())
        self.assertIn(["kitty", "SIGUSR1"], self.calls)

    def test_missing_template_is_an_error_not_a_crash(self):
        state = ap.load_state()
        os.unlink(ap.cfg("templates", state["files"][0]["template"]))
        before = self.snapshot()
        rep = self.change(accent="#3FE0D0")
        self.assertFalse(rep.as_dict()["ok"])
        self.assertEqual(self.snapshot(), before)

    def test_tampered_template_cannot_leak(self):
        """Un modello modificato con un segnaposto inventato non produce nulla."""
        state = ap.load_state()
        tpl = ap.cfg("templates", state["files"][0]["template"])
        pathlib.Path(tpl).write_text("{{cmx:../../etc/passwd}}")
        rep = self.change(accent="#3FE0D0")
        self.assertFalse(rep.as_dict()["ok"])

    def test_wallpaper_change(self):
        new = png(self.p("nuovo.png"))
        t, _, _ = th.read()
        t["wallpaper"]["home"] = new
        rep = ap.change_theme(t)
        self.assertEqual(rep.wallpaper["path"], new)
        self.assertIn(["swaybg", "-i", new, "-m", "fill"], self.calls)
        self.assertIn(f"path = {new}", self.read(".config/hypr/hyprlock.conf"))


class TestSafety(FakeHome):
    def test_symlink_outside_home_refused(self):
        outside = os.path.join(os.path.dirname(self.home), "fuori-" + os.path.basename(self.home))
        pathlib.Path(outside).write_text("color=#FFD25A\n")
        link = self.p(".config/rofi/trappola.rasi")
        os.symlink(outside, link)
        with self.assertRaises(files.UnsafeFile):
            ap.adopt_file(link, th.default_theme(), ap.load_state())
        act = ap.setup()
        self.assertIn(link, act["skipped"])
        self.assertEqual(pathlib.Path(outside).read_text(), "color=#FFD25A\n")

    def test_symlink_inside_home_writes_real_file(self):
        """Dotfiles gestiti con GNU Stow: il collegamento resta, cambia il file vero."""
        real = self.p("dotfiles/mako/config")
        os.makedirs(os.path.dirname(real))
        os.replace(self.p(".config/mako/config"), real)
        os.symlink(real, self.p(".config/mako/config"))
        ap.setup()
        t, _, _ = th.read()
        t["colors"]["accent"] = "#3FE0D0"
        self.assertTrue(ap.change_theme(t).as_dict()["ok"])
        self.assertTrue(os.path.islink(self.p(".config/mako/config")))
        self.assertIn("#3FE0D0", pathlib.Path(real).read_text())

    def test_directory_and_fifo_refused(self):
        os.mkfifo(self.p("fifo"))
        for p in (self.p("fifo"), self.p(".config")):
            with self.assertRaises(files.UnsafeFile):
                files.read_text(p)

    def test_huge_file_refused(self):
        big = self.p(".config/rofi/enorme.rasi")
        with open(big, "w") as f:
            f.write("#FFD25A\n" * (files.MAX_CONFIG_BYTES // 8 + 10))
        act = ap.setup()
        self.assertIn(big, act["skipped"])

    def test_permissions_preserved(self):
        os.chmod(self.p(".config/mako/config"), 0o600)
        ap.setup()
        t, _, _ = th.read()
        t["colors"]["accent"] = "#3FE0D0"
        ap.change_theme(t)
        self.assertEqual(stat.S_IMODE(os.stat(self.p(".config/mako/config")).st_mode), 0o600)

    def test_wallpaper_validation(self):
        fake = self.p("finto.png")
        pathlib.Path(fake).write_text("#!/bin/sh\nrm -rf ~\n")
        self.assertFalse(wallpaper.is_image(fake))
        self.assertEqual(wallpaper.set_wallpaper(fake), (False, None))
        self.assertEqual(wallpaper.set_wallpaper("relativo.png"), (False, None))
        self.assertEqual(wallpaper.set_wallpaper("/etc/passwd"), (False, None))
        self.assertTrue(wallpaper.is_image(self.wall))
        self.assertEqual(self.calls, [])

    def test_wallpaper_backends(self):
        self.running = {"swww-daemon": [(9, ["swww-daemon"])]}
        self.assertEqual(wallpaper.set_wallpaper(self.wall), (True, "swww"))
        self.assertEqual(self.calls[-1][:3], ["swww", "img", self.wall])
        self.running = {"hyprpaper": [(9, ["hyprpaper"])]}
        self.assertEqual(wallpaper.set_wallpaper(self.wall), (True, "hyprpaper"))
        self.assertEqual(self.calls[-1], ["hyprctl", "hyprpaper", "reload", "," + self.wall])

    def test_corrupt_state_is_ignored(self):
        ap.setup()
        pathlib.Path(ap.state_path()).write_text("{not json")
        self.assertEqual(ap.load_state()["files"], [])


if __name__ == "__main__":
    unittest.main()
