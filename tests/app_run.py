"""Esegue l'app Camenix (QML) su una home finta e scatta foto delle varie fasi.
Uso: python3 tests/app_run.py <cartella-foto>   (HOME deve già puntare alla home finta)"""
import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PySide6.QtCore import QObject, QUrl, QTimer, QMetaObject, Q_ARG, Q_RETURN_ARG    # noqa: E402
from PySide6.QtGui import QGuiApplication                                    # noqa: E402
from PySide6.QtQuick import QQuickView                                       # noqa: E402
from tests import qs_mock                                                   # noqa: E402

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
app = QGuiApplication(sys.argv)
qs_mock.register(os.path.join(ROOT, "app"))
wrap = os.path.join(ROOT, "app", "__test_wrap.qml")
with open(wrap, "w") as f:
    f.write('import QtQuick\nItem { width: 1180; height: 760\n  property alias eng: e\n'
            '  Engine { id: e; objectName: "eng" }\n  Main { id: m; anchors.fill: parent; eng: e }\n'
            '  function editor() { return m.children[m.children.length - 1] }\n}\n')
view = QQuickView()
errors = []
view.engine().warnings.connect(lambda ws: errors.extend(w.toString() for w in ws))
view.setSource(QUrl.fromLocalFile(wrap))
errors += [e.toString() for e in view.errors()]
view.resize(1180, 760)
view.show()
root = view.rootObject()
report = {"errors": errors, "steps": {}}


def eng():
    from PySide6.QtCore import QObject
    return root.findChild(QObject, "eng")


def draft():
    d = eng().property("draft")
    return d.toVariant() if hasattr(d, "toVariant") else d


def call(obj, name, *args):
    return QMetaObject.invokeMethod(obj, name, Q_RETURN_ARG("QVariant"), *[Q_ARG("QVariant", a) for a in args])


def shot(name):
    view.grabWindow().save(os.path.join(out, name + ".png"))


def theme_file():
    with open(os.path.expanduser("~/.config/camenix/theme.json")) as f:
        return json.load(f)


steps = []


def step(delay):
    def deco(fn):
        steps.append((delay, fn))
        return fn
    return deco


@step(1500)
def s1():
    d = draft()
    report["steps"]["loaded"] = bool(d) and d["colors"]["accent"]
    shot("1-light")


@step(600)
def s2():
    call(eng(), "setColor", "accent", "#3FE0D0")


@step(1500)
def s3():
    d = draft()
    report["steps"]["draft_accent"] = d["colors"]["accent"]
    report["steps"]["draft_soft"] = d["colors"]["accentSoft"]
    report["steps"]["dirty"] = eng().property("dirty")
    report["steps"]["theme_untouched"] = theme_file()["colors"]["accent"]
    shot("2-modified")
    call(eng(), "apply")


@step(2500)
def s4():
    report["steps"]["applied_accent"] = theme_file()["colors"]["accent"]
    report["steps"]["awaiting_keep"] = eng().property("awaitingKeep")
    shot("3-parachute")
    call(eng(), "revert")


@step(2500)
def s5():
    report["steps"]["reverted_accent"] = theme_file()["colors"]["accent"]
    call(eng(), "setMode", "dark")


@step(1500)
def s6():
    shot("4-dark")
    with open(os.path.expanduser("~/.config/camenix/app.json")) as f:
        report["steps"]["prefs"] = json.load(f)
    for it in root.findChildren(QObject):
        if it.metaObject().className().startswith("ColorEditor"):
            it.setProperty("label", "Accento")
            it.setProperty("against", "#1E1528")
            it.setProperty("startHex", "#FFD25A")
            it.setProperty("role", "accent")


@step(600)
def s7():
    shot("5-editor")
    report["steps"]["engine_calls"] = [c[1] for c in qs_mock.Process.log if len(c) > 1]
    report["errors"] = errors
    with open(os.path.join(out, "report.json"), "w") as f:
        json.dump(report, f, indent=1)
    app.quit()


t = 0
for delay, fn in steps:
    t += delay
    QTimer.singleShot(t, fn)
try:
    app.exec()
finally:
    if os.path.exists(wrap):                 # anche se qualcosa va storto, non lascia file nell'app
        os.remove(wrap)
