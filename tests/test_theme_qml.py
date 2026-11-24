"""Theme.qml (integrazione Quickshell): predefiniti, file ostili, trasparenza esatta.
Richiede PySide6; senza, i test vengono saltati."""
import json
import pathlib
import os
import shutil
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QUrl, QMetaObject, Q_ARG, Q_RETURN_ARG
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlEngine, QQmlComponent
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "PySide6 non installato")
class TestThemeQml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.dir = tempfile.mkdtemp()
        shutil.copy(os.path.join(ROOT, "integrations", "quickshell", "Theme.qml"), cls.dir)
        pathlib.Path(cls.dir, "qmldir").write_text("singleton Theme 1.0 Theme.qml\n")
        pathlib.Path(cls.dir, "Probe.qml").write_text(
            "import QtQuick\nQtObject {\n"
            "  function load(raw) { Theme.load(raw); return JSON.stringify(Theme.values) }\n"
            "  function rev() { return Theme.revision }\n"
            "  function alpha(c, a) { return Theme.a(c, a) }\n"
            "  function text() { return String(Theme.text) }\n}\n")
        cls.engine = QQmlEngine()
        cls.engine.addImportPath(os.path.join(ROOT, "tests", "qml_mocks"))
        cls.comp = QQmlComponent(cls.engine, QUrl.fromLocalFile(os.path.join(cls.dir, "Probe.qml")))
        cls.probe = cls.comp.create()
        assert cls.probe is not None, cls.comp.errorString()
        QQmlEngine.setObjectOwnership(cls.probe, QQmlEngine.ObjectOwnership.CppOwnership)
        cls.defaults = {r["key"]: r["default"] for r in
                        json.loads(pathlib.Path(ROOT, "camenix", "data", "roles.json").read_text())["roles"]}

    def call(self, name, *args):
        return QMetaObject.invokeMethod(self.probe, name, Q_RETURN_ARG("QVariant"),
                                        *[Q_ARG("QVariant", a) for a in args])

    def load(self, raw):
        return json.loads(self.call("load", raw))

    def test_defaults_match_roles(self):
        self.assertEqual(self.load(""), self.defaults)

    def test_valid_theme(self):
        v = self.load(json.dumps({"colors": {"text": "#F0F0F0", "glass": "#203040"}}))
        self.assertEqual(v["text"], "#F0F0F0")
        self.assertEqual(v["glass"], "#203040")
        self.assertEqual(v["accent"], self.defaults["accent"])

    def test_hostile_inputs_fall_back(self):
        for raw in ('{"colors": {"text": "#FF0000"', "[1,2,3]", "null", '"x"', '{"colors": "red"}',
                    json.dumps({"colors": {"text": "red; } Rectangle {", "glass": "#12345", "accent": ["#FF0000"]}}),
                    json.dumps({"colors": {"__proto__": {"text": "#FF0000"}, "constructor": "#FF0000"}}),
                    '{"colors":{"text":"#FF0000"},"x":"' + "A" * 70000 + '"}'):
            self.assertEqual(self.load(raw), self.defaults, raw[:60])

    def test_readable_on_dark_glass(self):
        # il caso reale: tema scuro, verde e rosso scuri della palette chiara -> schiariti quanto basta
        from camenix.derive import contrast, to_hls
        v = self.load(json.dumps({"colors": {"glass": "#2A1418", "text": "#F2E6E8"}}))
        for role, need in (("success", 4.5), ("error", 4.5), ("accent2", 3), ("warning", 3)):
            self.assertGreaterEqual(contrast(v[role], v["glass"]), need, role)
            self.assertAlmostEqual(to_hls(v[role])[0], to_hls(self.defaults[role])[0], delta=0.02)   # stessa tinta
        self.assertEqual(v["text"], "#F2E6E8")          # già leggibile: non si tocca

    def test_readable_on_light_glass(self):
        from camenix.derive import contrast
        v = self.load(json.dumps({"colors": {"glass": "#FFFFFF", "success": "#B8F5C8", "accent2": "#FFE0B0"}}))
        self.assertGreaterEqual(contrast(v["success"], "#FFFFFF"), 4.5)
        self.assertGreaterEqual(contrast(v["accent2"], "#FFFFFF"), 3)

    def test_readable_keeps_original_palette(self):
        # Gudetama scritto per intero (anche in minuscolo): identico ai predefiniti
        lower = {k: c.lower() for k, c in self.defaults.items()}
        self.assertEqual(self.load(json.dumps({"colors": lower})), self.defaults)
        self.assertEqual(self.load(json.dumps({"colors": self.defaults})), self.defaults)

    def test_readable_always_ends(self):
        # vetro grigio medio, colori impossibili: si ferma senza bloccarsi e restituisce colori validi
        import re
        for glass in ("#808080", "#000000", "#FFFFFF", "#767676"):
            for c in ("#000000", "#FFFFFF", "#808080", "#FF0000"):
                v = self.load(json.dumps({"colors": {"glass": glass, "success": c, "text": c, "accent2": c}}))
                for role in ("success", "text", "accent2", "error", "warning"):
                    self.assertRegex(v[role], r"^#[0-9A-F]{6}$")

    def test_revision_grows(self):
        before = self.call("rev")
        self.load("")
        self.assertEqual(self.call("rev"), before + 1)

    def test_alpha_is_exact(self):
        self.assertEqual(self.call("alpha", "#1e1528", 0.6), "#991e1528")
        self.assertEqual(self.call("alpha", "#ffffff", 0.2), "#33ffffff")
        self.assertEqual(self.call("alpha", "#ffffff", 0.004), "#01ffffff")
        self.assertEqual(self.call("alpha", "#ffffff", 5), "#ffffffff")
        self.assertEqual(self.call("alpha", "#ffffff", -1), "#00ffffff")
        for a in range(256):
            self.assertEqual(self.call("alpha", "#000000", round(a / 255, 3)), "#%02x000000" % a)


if __name__ == "__main__":
    unittest.main()
