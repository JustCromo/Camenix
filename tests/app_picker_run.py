"""Usa l'app Camenix (QML) come farebbe una persona: mouse e tastiera veri (simulati), su una home finta.
Uso: python3 tests/app_picker_run.py <cartella-foto> [--first]   (HOME deve già puntare alla home finta)
Con --first la home non ha ancora un tema: si parte dalla schermata di benvenuto."""
import json
import math
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QTimer, QUrl      # noqa: E402
from PySide6.QtGui import QGuiApplication                                # noqa: E402
from PySide6.QtQuick import QQuickItem, QQuickView                       # noqa: E402
from PySide6.QtTest import QTest                                         # noqa: E402
from tests import qs_mock                                                # noqa: E402

out = sys.argv[1]
FIRST = "--first" in sys.argv
os.makedirs(out, exist_ok=True)
app = QGuiApplication(sys.argv)
qs_mock.register(os.path.join(ROOT, "app"))
wrap = os.path.join(ROOT, "app", "__test_wrap_picker.qml")
with open(wrap, "w") as f:
    f.write('import QtQuick\nItem { width: 1180; height: 760\n'
            '  QtObject { id: ff; objectName: "fader"; property bool available: true; property int begun: 0\n'
            '    property int finished: 0; function begin(fn) { begun++; fn() } function finish() { finished++ } }\n'
            '  Engine { id: e; objectName: "eng"; fader: ff }\n  Main { objectName: "main"; anchors.fill: parent; eng: e }\n}\n')
view = QQuickView()
errors = []
view.engine().warnings.connect(lambda ws: errors.extend(w.toString() for w in ws))
view.setSource(QUrl.fromLocalFile(wrap))
errors += [e.toString() for e in view.errors()]
view.resize(1180, 760)
view.show()
root = view.rootObject()
R = {"errors": errors, "steps": {}}
S = R["steps"]


def obj(name):
    found = root.findChild(QObject, name)
    if found is None:                            # creato da un Repeater: si cerca nell'albero visivo
        found = next((i for i in tree(root) if i.objectName() == name), None)
    return found


def val(v):
    return v.toVariant() if hasattr(v, "toVariant") else v


def draft():
    return val(obj("eng").property("draft"))


def tree(item):
    # albero visivo: i riquadri creati dai Repeater non sono "figli" QObject, ma figli visivi sì
    yield item
    for c in item.childItems():
        yield from tree(c)


def items(cls):
    return [o for o in tree(root) if o.metaObject().className().startswith(cls)]


def editor():
    return items("ColorEditor")[0]


def btn(text):
    return [b for b in items("Btn") if b.property("text") == text and b.isVisible()][0]


def at(item, x=None, y=None):
    x = item.width() / 2 if x is None else x
    y = item.height() / 2 if y is None else y
    p = item.mapToScene(QPointF(x, y))
    return QPoint(round(p.x()), round(p.y()))


def click(item, x=None, y=None):
    QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, at(item, x, y))


def type_text(text):
    for ch in text:
        key = Qt.Key_NumberSign if ch == "#" else Qt.Key(ord(ch.upper()))
        QTest.keyClick(view, key, Qt.ShiftModifier if ch == "#" else Qt.NoModifier)


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


if FIRST:
    @step(1500)
    def welcome():
        e = obj("eng")
        S["first_run"] = e.property("firstRun")
        S["welcome_visible"] = items("Welcome")[0].isVisible()
        S["detected_border"] = val(e.property("detected"))["theme"]["colors"]["borderFrom"]
        S["theme_before_start"] = os.path.exists(os.path.expanduser("~/.config/camenix/theme.json"))
        shot("0-welcome")
        click(obj("startBtn"))

    @step(2500)
    def started():
        S["first_run_after"] = obj("eng").property("firstRun")
        S["theme_border"] = theme_file()["colors"]["borderFrom"]
        S["draft_border_start"] = draft()["colors"]["borderFrom"]


@step(1500)
def start():
    shot("0-main")
    S["palettes"] = [p["name"] for p in val(obj("main").property("palettes"))]
    dark = obj("palette-Sfondo scuro")
    if dark is not None:                         # palette ricavata dallo sfondo
        click(dark)


@step(1500)
def palette_back():
    d = draft()["colors"]
    S["dark_glass"] = d["glass"]
    S["dirty_after_palette"] = obj("eng").property("dirty")
    shot("0b-palette")
    click(obj("palette-In uso"))                 # e si torna a quella in uso


@step(1500)
def hover():
    S["dirty_after_back"] = obj("eng").property("dirty")
    QTest.mouseMove(view, at(obj("color-accent")))


@step(300)
def hover_check():
    S["hover_zones"] = val(obj("main").property("hoverZones"))
    shot("1-hover")
    click(obj("color-accent"))


@step(800)
def ring():
    ed = editor()
    S["editor_role"] = ed.property("role")
    S["wall_colors"] = val(ed.property("wallColors"))
    pk = obj("picker")
    ro = pk.width() / 2
    r = ro - 11
    a = math.radians(120)
    click(pk, ro + r * math.cos(a), ro + r * math.sin(a))


@step(200)
def square():
    S["hue_after_ring"] = round(editor().property("hue"))
    click(obj("svSquare"))


@step(200)
def slider():
    S["hex_after_square"] = editor().property("hex")
    tr = [t for t in obj("chanR").findChildren(QQuickItem) if t.objectName() == "track"][0]
    click(tr, tr.width() + 5)                    # oltre la fine: si ferma a 255


@step(200)
def dots():
    S["hex_after_slider"] = editor().property("hex")
    if S["wall_colors"]:                         # un colore preso dallo sfondo (se c'è uno sfondo)
        click([d for d in items("ColorDot") if d.property("c") == S["wall_colors"][-1]][0])


@step(200)
def typing():
    S["hex_after_wall_dot"] = editor().property("hex")
    f = obj("hexField")
    click(f)
    QTest.keyClick(view, Qt.Key_A, Qt.ControlModifier)
    type_text("12")                  # incompleto: Invio non deve fare niente
    QTest.keyClick(view, Qt.Key_Return)


@step(200)
def typing2():
    S["open_after_bad_enter"] = editor().property("role")
    QTest.keyClick(view, Qt.Key_A, Qt.ControlModifier)
    type_text("zz#3fe0d0")           # le lettere non valide vengono rifiutate dal campo
    shot("2-picker")


@step(200)
def use():
    S["hex_typed"] = editor().property("hex")
    S["field_typed"] = obj("hexField").property("text")
    click(obj("useColor"))


@step(1500)
def after_use():
    d = draft()
    S["editor_closed"] = editor().property("role") == ""
    S["draft_accent"] = d["colors"]["accent"]
    S["dirty"] = obj("eng").property("dirty")
    S["theme_untouched"] = theme_file()["colors"]["accent"]
    click(obj("color-borderFrom"))


@step(500)
def border():
    S["border_desc"] = editor().property("desc")
    click(obj("hexField"))
    QTest.keyClick(view, Qt.Key_A, Qt.ControlModifier)
    type_text("ff00aa")
    QTest.keyClick(view, Qt.Key_Return)


@step(1500)
def apply_():
    S["draft_border"] = draft()["colors"]["borderFrom"]
    S["changes"] = obj("main").property("changes")
    shot("3-modified")
    S["apply_enabled"] = btn("Applica ✓").property("enabledBtn")
    shot("4-review")
    click(btn("Applica ✓"))


@step(2500)
def applied():
    t = theme_file()
    S["applied"] = [t["colors"]["accent"], t["colors"]["borderFrom"]]
    hypr = [os.path.expanduser(p) for p in ("~/.config/hypr/config/decoration.lua", "~/.config/hypr/hyprland.conf")]
    with open([p for p in hypr if os.path.exists(p)][0]) as f:
        S["hypr_border"] = "rgba(ff00aaff)" in f.read().lower()
    click(btn("Tieni ✓"))


@step(800)
def done():
    S["awaiting"] = obj("eng").property("awaitingKeep")
    S["fader"] = [obj("fader").property("begun"), obj("fader").property("finished")]
    S["pending_after_keep"] = os.path.exists(os.path.expanduser("~/.config/camenix/pending.json"))
    S["kept"] = theme_file()["colors"]["accent"]
    R["errors"] = errors
    with open(os.path.join(out, "report.json"), "w") as f:
        json.dump(R, f, indent=1)
    app.quit()


# un passo alla volta: il successivo parte solo quando il precedente ha finito
# (clic e tasti simulati fanno girare gli eventi, e due passi non devono accavallarsi)
def run(i=0):
    if i >= len(steps):
        return
    delay, fn = steps[i]

    def go():
        try:
            fn()
        except Exception as e:                  # un passo fallito non blocca gli altri: finisce nel report
            errors.append(f"{fn.__name__}: {e!r}")
        run(i + 1)
    QTimer.singleShot(delay, go)


QTimer.singleShot(10000 * 6, app.quit)          # rete di sicurezza: mai appeso per sempre
run()
try:
    app.exec()
finally:
    if os.path.exists(wrap):
        os.remove(wrap)
