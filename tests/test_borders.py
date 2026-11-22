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

    def test_labels(self):
        self.assertNotEqual(t("role.borderFrom"), "role.borderFrom")
        self.assertNotEqual(t("role.borderTo"), "role.borderTo")


if __name__ == "__main__":
    unittest.main()
