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
