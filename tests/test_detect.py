"""Primo avvio su un desktop che non è il mio: Camenix legge i colori che ci sono e parte da quelli."""
import json
import os
import pathlib
import shutil

from camenix import apply as ap, detect, render, system, theme as th
from tests.fakehome import FakeHome

STOCK = {   # come li lascia un'installazione nuova (config di esempio di Hyprland, kitty con un tema incluso, mako)
    ".config/hypr/hyprland.conf": "general {\n    gaps_in = 5\n    border_size = 2\n"
                                  "    # col.active_border = rgba(ff0000ee)\n"
                                  "    col.active_border = rgba(33ccffee) rgba(00ff99ee) 45deg\n"
                                  "    col.inactive_border = rgba(595959aa)\n}\n",
    ".config/kitty/kitty.conf": "font_size 11\ninclude tema.conf\n",
    ".config/kitty/tema.conf": "background #1E1E2E\nforeground #CDD6F4\ncolor1 #F38BA8\ncolor2 #A6E3A1\n"
                               "color3 #F9E2AF\ncolor4 #89B4FA\ncolor5 #F5C2E7\n",
    ".config/mako/config": "background-color=#285577FF\ntext-color=#FFFFFF\nborder-color=#4C7899\n\n"
                           "[urgency=high]\nborder-color=#FF0000\n",
}


class TestDetect(FakeHome):
    def stock(self, configs=STOCK):
        shutil.rmtree(self.p(".config"))
        for rel, text in configs.items():
            p = pathlib.Path(self.home, rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)

    def test_stock_desktop(self):
        self.stock()
        theme, found = detect.detect()
        c = theme["colors"]
        self.assertEqual((c["borderFrom"], c["borderTo"], c["borderIdle"]), ("#33CCFF", "#00FF99", "#595959"))
        self.assertEqual((c["glass"], c["text"], c["accent"]), ("#285577", "#FFFFFF", "#4C7899"))
        self.assertEqual(theme["terminal"]["background"], "#1E1E2E")          # dal file incluso
        self.assertEqual((c["success"], c["warning"], c["error"]), ("#A6E3A1", "#F9E2AF", "#F38BA8"))
        self.assertEqual(theme["wallpaper"]["home"], self.wall)
        self.assertEqual(set(found), {"kitty", "hyprland", "mako", "wallpaper"})
        self.assertNotEqual(c["accentSoft"], th.defaults()["accentSoft"])     # sfumature dai colori trovati

    def test_nothing_configured(self):
        self.stock({})
        self.running = {}
        theme, found = detect.detect()
        self.assertEqual(found, [])
        self.assertEqual(theme["terminal"]["background"], "#000000")           # predefiniti di kitty
        self.assertGreaterEqual(detect.contrast(theme["colors"]["text"], theme["colors"]["glass"]), 4.5)

    def test_unreadable_text_is_fixed(self):
        self.stock({".config/mako/config": "background-color=#222222\ntext-color=#252525\n"})
        theme, _ = detect.detect()
        self.assertGreaterEqual(detect.contrast(theme["colors"]["text"], theme["colors"]["glass"]), 4.5)

    def test_ivan_desktop(self):
        theme, _ = detect.detect()                                             # le config di FakeHome
        c = theme["colors"]
        self.assertEqual((c["borderFrom"], c["borderTo"], c["borderIdle"]), ("#E0B0FF", "#FFBF00", "#FEFEFA"))
        self.assertEqual((c["glass"], c["text"]), ("#FBF8FF", "#2B2236"))

    def test_hostile_files_are_ignored(self):
        self.stock({})
        secret = os.path.join(self.home, "..", "fuori.conf")
        pathlib.Path(secret).write_text("background-color=#ABCDEF\n")
        os.makedirs(self.p(".config/mako"))
        os.symlink(os.path.realpath(secret), self.p(".config/mako/config"))     # link fuori dalla home
        os.makedirs(self.p(".config/kitty"))
        pathlib.Path(self.p(".config/kitty/kitty.conf")).write_text(
            "include /etc/passwd\ninclude kitty.conf\nbackground red; rm -rf ~\nforeground #12345\n"
            "color1 #FFFFFF\x00\nbackground " + "#" * 5000 + "\n")
        pathlib.Path(self.p(".config/hypr")).mkdir()
        pathlib.Path(self.p(".config/hypr/hyprland.conf")).write_bytes(b"col.active_border = rgba(" + b"A" * 2_000_000 + b")\n")
        theme, found = detect.detect()
        self.assertEqual(theme["colors"]["glass"], "#000000")                  # niente dal file fuori dalla home
        self.assertEqual(theme["terminal"]["background"], "#000000")
        self.assertNotIn("hyprland", found)                                     # file troppo grande: ignorato
        os.remove(secret)


class TestFirstRun(FakeHome):
    def test_first_run_links_files_to_found_colors(self):
        TestDetect.stock(self)
        system.has = lambda p: p in ("swaybg", "hyprctl", "makoctl", "kitty")
        before = pathlib.Path(self.p(".config/hypr/hyprland.conf")).read_text()
        res = ap.first_run()
        self.assertTrue(res["report"]["ok"], res)
        self.assertEqual(pathlib.Path(self.p(".config/hypr/hyprland.conf")).read_text(), before)   # niente cambia
        self.assertTrue(os.path.isfile(ap.original_path()))
        # ora cambiare il bordo cambia Hyprland, e non le notifiche
        theme, _, _ = th.read()
        theme["colors"]["borderFrom"] = "#FF00AA"
        self.assertTrue(ap.change_theme(theme).as_dict()["ok"])
        self.assertIn("rgba(ff00aaee)", pathlib.Path(self.p(".config/hypr/hyprland.conf")).read_text().lower())
        self.assertNotIn("FF00AA", pathlib.Path(self.p(".config/mako/config")).read_text().upper())
        # "colori iniziali" torna ai colori trovati, non a quelli di Camenix
        self.assertTrue(ap.reset_colors().as_dict()["ok"])
        theme, _, _ = th.read()
        self.assertEqual(theme["colors"]["borderFrom"], "#33CCFF")
        self.assertIn("rgba(33ccffee)", pathlib.Path(self.p(".config/hypr/hyprland.conf")).read_text())

    def test_border_equal_to_other_color_goes_to_border(self):
        TestDetect.stock(self, {".config/hypr/hyprland.conf": "col.active_border = rgba(4c7899ff)\n",
                                ".config/mako/config": "background-color=#285577\ntext-color=#FFFFFF\nborder-color=#4C7899\n"})
        ap.first_run()
        tmpl = [f for f in ap.load_state()["files"] if f["target"].endswith("hyprland.conf")][0]
        text = pathlib.Path(ap.cfg("templates", tmpl["template"])).read_text()
        self.assertIn("{{cmx:borderFrom:lower}}", text)

    def test_kitty_without_config_gets_one(self):
        TestDetect.stock(self, {})
        system.has = lambda p: p in ("kitty",)
        ap.first_run()
        self.assertIn(ap.KITTY_INCLUDE, pathlib.Path(self.p(".config/kitty/kitty.conf")).read_text())

    def test_never_overwrites_existing_theme(self):
        th.write(th.default_theme("Mio"))
        self.assertIsNone(ap.first_run())
        self.assertEqual(th.read()[0]["name"], "Mio")

    def test_bad_original_falls_back(self):
        os.makedirs(os.path.dirname(ap.original_path()), exist_ok=True)
        pathlib.Path(ap.original_path()).write_text('{"colors": {"accent": "$(rm -rf ~)"}}')
        self.assertEqual(ap.original()["colors"]["accent"], th.defaults()["accent"])
        pathlib.Path(ap.original_path()).write_text("non è json")
        self.assertIsNone(ap.original())

    def test_prefer_order(self):
        theme = th.default_theme()
        theme["colors"]["accent"] = theme["colors"]["borderFrom"] = "#123456"
        self.assertIn("borderFrom", render.adopt("x = rgba(123456ff)", theme, ("borderFrom",))[0])
        self.assertIn("accent", render.adopt("x = rgba(123456ff)", theme)[0])


if __name__ == "__main__":
    import unittest
    unittest.main()


class TestLockscreen(FakeHome):
    IVAN = """
general {
    hide_cursor = true
}
$fg = rgba(342429ee)
background {
    path = /x.png
    blur_passes = 3
    blur_size = 7
    brightness = 0.95
}
# Orologio
label {
    text = $TIME
    color = $fg
    font_size = 104
    font_family = JetBrainsMono Nerd Font ExtraBold
    position = 0, 210
    halign = center
    valign = center
}
label {
    text = <b>ciao</b> $USER
    color = rgb(10, 20, 30)
    position = 5%, -10%
}
input-field {
    size = 300, 52
    outer_color = rgba(AEBEEEee) rgba({{cmx:accent}}ee) 45deg
    inner_color = 0x40FBECF0
    position = 0, -150
}
"""

    def test_parse(self):
        from camenix import lockscreen
        d = lockscreen.parse(self.IVAN, (2000, 1000))
        clock, user = d["labels"]
        self.assertEqual(clock["kind"], "time")
        self.assertEqual(clock["color"]["stops"][0], {"hex": "#342429", "a": 0.933})     # variabile $fg risolta
        self.assertEqual((clock["font_size"], clock["position"], clock["bold"]), (104, [0, 210], True))
        self.assertEqual(user["text"], "ciao $USER")                                     # niente markup
        self.assertEqual(user["position"], [100, -100])                                  # percentuali
        self.assertEqual(user["color"]["stops"][0]["hex"], "#0A141E")
        f = d["inputs"][0]
        self.assertEqual(f["outer"]["stops"][1], {"role": "accent", "a": 0.933})        # colore collegato al tema
        self.assertEqual(f["outer"]["angle"], 45)
        self.assertEqual(f["inner"]["stops"][0], {"hex": "#FBECF0", "a": 0.251})
        self.assertEqual(d["background"]["blur_passes"], 3)
        self.assertIsNone(clock["shadow"])                                               # niente shadow_passes

    def test_date_never_runs_the_command(self):
        from camenix import lockscreen
        import time
        self.assertEqual(lockscreen.date_text('cmd[update:60000] date +"%Y"'), time.strftime("%Y"))
        evil = 'cmd[update:1] date +"%Y"; touch /tmp/camenix-pwned; $(id)'
        self.assertEqual(lockscreen.date_text(evil), time.strftime("%Y"))
        self.assertFalse(os.path.exists("/tmp/camenix-pwned"))
        self.assertNotIn("$", lockscreen.date_text('date +"$(whoami)"'))

    def test_hostile_config(self):
        from camenix import lockscreen
        evil = "label {\n text = cmd[update:1] rm -rf ~\n font_size = 1e308\n position = nan, inf\n color = rgba(999,999,999,9)\n}\n" * 50
        evil += "input-field {\n size = -5, 99999999999\n outline_thickness = 1000\n}\n" + "}\n" * 20 + "x {\n" * 30
        d = lockscreen.parse(evil)
        self.assertLessEqual(len(d["labels"]), lockscreen.MAX_ITEMS)
        lab = d["labels"][0]
        self.assertEqual(lab["text"], "")                                             # i comandi non diventano testo
        self.assertLessEqual(lab["font_size"], 400)
        self.assertEqual(lab["color"]["stops"][0]["hex"], "#FFFFFF")                  # valori fuori scala limitati
        self.assertLessEqual(d["inputs"][0]["outline"], 40)
        json.dumps(d)                                                                  # sempre serializzabile

    def test_info_reads_template_and_survives_missing_file(self):
        from camenix import lockscreen
        ap.setup()
        d = lockscreen.info(ap.load_state(), th.config_dir())
        self.assertTrue(d["found"])
        self.assertEqual(d["screen"], [1920, 1080])                                    # hyprctl finto: ripiego
        os.remove(self.p(".config/hypr/hyprlock.conf"))
        self.assertFalse(lockscreen.info(ap.load_state(), th.config_dir())["found"])
        os.symlink("/etc/passwd", self.p(".config/hypr/hyprlock.conf"))                # fuori dalla home
        self.assertFalse(lockscreen.info({}, th.config_dir())["found"])
