"""I due colori del bordo delle finestre li sceglie l'utente: le sfumature non li toccano."""
import unittest

from camenix import derive as dv
from camenix import theme as th
from camenix.i18n import t


class TestBorders(unittest.TestCase):
    def test_are_base_roles(self):
        groups = {r["key"]: r["group"] for r in th.roles()}
        self.assertEqual(groups["borderFrom"], "base")
        self.assertEqual(groups["borderTo"], "base")
        self.assertNotIn("borderFrom", dv.FAMILY)
        self.assertNotIn("borderTo", dv.FAMILY)

    def test_accent_change_keeps_borders(self):
        c = th.defaults()
        c["accent"], c["secondary"] = "#3FE0D0", "#112233"
        out = dv.derive(c)
        self.assertEqual(out["borderFrom"], "#E0B0FF")
        self.assertEqual(out["borderTo"], "#FFBF00")

    def test_user_border_survives_derive(self):
        c = th.defaults()
        c["borderFrom"], c["borderTo"], c["accent"] = "#FF00AA", "#00FFAA", "#123456"
        out = dv.derive(c)
        self.assertEqual((out["borderFrom"], out["borderTo"]), ("#FF00AA", "#00FFAA"))

    def test_hostile_border_value_is_rejected(self):
        raw = th.default_theme()
        raw["colors"]["borderFrom"] = "red; rm -rf ~"
        theme, problems = th.normalize(raw)
        self.assertEqual(theme["colors"]["borderFrom"], "#E0B0FF")
        self.assertTrue(problems)

    def test_shades_come_back_with_their_base(self):
        # prova una palette, poi torna a quella in uso: anche le sfumature tornano quelle in uso
        current = th.defaults()
        tried = dv.derive(dict(current, accent="#123456"), current)
        self.assertNotEqual(tried["accentSoft"], current["accentSoft"])
        back = dv.derive(dict(tried, accent=current["accent"]), current)
        self.assertEqual(back, current)

    def test_icons_and_links_stay_visible(self):
        # palette chiarissima (come quelle ricavate da uno sfondo pastello): icone e link restano leggibili
        c = th.defaults()
        c.update(glass="#F4F0FB", secondary="#E6DDF7", accent2="#FFE7A6", text="#2A2233")
        out = dv.derive(c)
        for role, cap in dv.FOREGROUND.items():
            target = min(cap, dv.contrast(th.defaults()[role], th.defaults()["glass"]))
            self.assertGreaterEqual(dv.contrast(out[role], out["glass"]) + 0.01, target, role)
        # pannelli scuri: si schiarisce invece di scurire
        c = th.defaults()
        c.update(glass="#14101A", secondary="#2A2140", text="#F0EAF8")
        out = dv.derive(c)
        self.assertGreaterEqual(dv.contrast(out["secondaryDeep"], out["glass"]) + 0.01, 3)
        self.assertEqual(dv.derive(th.defaults()), th.defaults())          # la palette originale non cambia

    def test_labels(self):
        self.assertNotEqual(t("role.borderFrom"), "role.borderFrom")
        self.assertNotEqual(t("role.borderTo"), "role.borderTo")


if __name__ == "__main__":
    unittest.main()
