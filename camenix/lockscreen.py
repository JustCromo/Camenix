"""Com'è fatta la schermata di blocco (hyprlock), per disegnarla fedele nell'anteprima.

Legge ~/.config/hypr/hyprlock.conf (o il suo modello, se Camenix lo gestisce: così i colori restano
collegati ai ruoli del tema e l'anteprima li cambia insieme alla bozza). Non scrive niente.
Restituisce solo numeri, colori e testi brevi: niente che l'app possa eseguire."""
import json
import os
import re

from camenix import files, system

MAX_ITEMS = 12
PH = r"\{\{cmx:([A-Za-z0-9_.]+)(?::lower)?\}\}"
COLOR = re.compile(
    r"rgba?\(\s*(?:" + PH + r"|([0-9A-Fa-f]{6}))([0-9A-Fa-f]{2})?\s*\)"       # rgba(RRGGBBAA) / rgba({{cmx:ruolo}}AA)
    r"|rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*([0-9.]+))?\s*\)"  # rgba(r, g, b, a)
    r"|0x([0-9A-Fa-f]{2})([0-9A-Fa-f]{6})"                                    # 0xAARRGGBB
    r"|#([0-9A-Fa-f]{6})([0-9A-Fa-f]{2})?")                                   # #RRGGBB(AA)
ANGLE = re.compile(r"(-?\d{1,3})\s*deg")


def _num(value, default=0.0):
    try:
        v = float(str(value).strip())
        return v if -100000 < v < 100000 else default
    except ValueError:
        return default


def parse_color(value):
    """'rgba(AEBEEEee) rgba({{cmx:accent}}ee) 45deg' -> {"stops": [{"hex"|"role", "a"}], "angle": 45} o None."""
    stops = []
    for m in COLOR.finditer(value or ""):
        g = m.groups()
        if g[0] or g[1]:
            a = int(g[2], 16) / 255 if g[2] else 1.0
            stops.append({"role": g[0], "a": round(a, 3)} if g[0] else {"hex": "#" + g[1].upper(), "a": round(a, 3)})
        elif g[3]:
            r, gg, b = (min(255, int(x)) for x in g[3:6])
            a = min(1.0, max(0.0, _num(g[6], 1.0))) if g[6] else 1.0
            stops.append({"hex": "#%02X%02X%02X" % (r, gg, b), "a": round(a, 3)})
        elif g[7]:
            stops.append({"hex": "#" + g[8].upper(), "a": round(int(g[7], 16) / 255, 3)})
        elif g[9]:
            a = int(g[10], 16) / 255 if g[10] else 1.0
            stops.append({"hex": "#" + g[9].upper(), "a": round(a, 3)})
        if len(stops) >= 4:
            break
    if not stops:
        return None
    m = ANGLE.search(value)
    return {"stops": stops, "angle": int(m.group(1)) % 360 if m else 0}


def _pair(value, screen):
    """'0, 210' o '10%, -5%' -> [x, y] in pixel."""
    parts = [p.strip() for p in str(value).split(",")][:2]
    out = []
    for i, p in enumerate(parts + ["0"] * (2 - len(parts))):
        if p.endswith("%"):
            out.append(_num(p[:-1]) / 100 * screen[i])
        else:
            out.append(_num(p))
    return out


DATE_FMT = re.compile(r"""\bdate\b[^+]*\+\s*["']?([%A-Za-z0-9 ,.:/\-]{1,40})""")


def date_text(cmd):
    """La data come la scriverebbe `date +FORMATO` (nella lingua del sistema), senza eseguire il comando:
    del comando si prende solo il formato, fatto di lettere, cifre, spazi e pochi segni."""
    import locale
    import time
    m = DATE_FMT.search(cmd)
    fmt = m.group(1).strip() if m else "%A %d %B"
    try:
        locale.setlocale(locale.LC_TIME, "")
    except locale.Error:
        pass
    try:
        out = time.strftime(fmt)
    except ValueError:
        return ""
    return "".join(ch for ch in out if ch.isprintable())[:60]


def parse(text, screen=(1920, 1080)):
    """Testo di hyprlock.conf -> blocchi utili all'anteprima."""
    variables, blocks, stack = {}, [], []
    for raw in text.splitlines()[:5000]:
        line = raw.split("#", 1)[0].strip() if not raw.strip().startswith("##") else ""
        if not line:
            continue
        if line.endswith("{"):
            stack.append({"type": line[:-1].strip().lower(), "keys": {}})
            continue
        if line == "}":
            if stack:
                b = stack.pop()
                if not stack:
                    blocks.append(b)
            continue
        if "=" in line:
            key, value = (s.strip() for s in line.split("=", 1))
            if key.startswith("$") and not stack:
                variables[key] = value
            elif stack:
                for name, v in sorted(variables.items(), key=lambda kv: -len(kv[0])):
                    value = value.replace(name, v)
                stack[-1]["keys"][key.lower()] = value[:300]
    out = {"background": None, "labels": [], "inputs": []}
    for b in blocks:
        k = b["keys"]
        if b["type"] == "background" and out["background"] is None:
            out["background"] = {"blur_passes": int(_num(k.get("blur_passes"), 0)) % 100,
                                 "blur_size": int(_num(k.get("blur_size"), 7)) % 200,
                                 "brightness": _num(k.get("brightness"), 0.8),
                                 "vibrancy": _num(k.get("vibrancy"), 0.17),
                                 "color": parse_color(k.get("color", ""))}
        elif b["type"] == "label" and len(out["labels"]) < MAX_ITEMS:
            t = k.get("text", "")
            kind = "time" if "$TIME" in t else "date" if re.search(r"\bdate\b", t) else "user" if "$USER" in t else "text"
            plain = re.sub(r"<[^>]*>", "", t)
            plain = date_text(t) if kind == "date" else \
                "" if plain.startswith("cmd[") else "".join(ch for ch in plain if ch.isprintable())[:60]
            out["labels"].append({"kind": kind, "text": plain, "color": parse_color(k.get("color", "")),
                                  "font_size": max(4, min(400, _num(k.get("font_size"), 16))),
                                  "bold": "bold" in k.get("font_family", "").lower(),
                                  "position": _pair(k.get("position", "0, 0"), screen),
                                  "halign": k.get("halign", "center"), "valign": k.get("valign", "center")})
        elif b["type"] == "input-field" and len(out["inputs"]) < MAX_ITEMS:
            out["inputs"].append({"size": _pair(k.get("size", "400, 90"), screen),
                                  "rounding": _num(k.get("rounding"), -1),
                                  "outline": max(0, min(40, _num(k.get("outline_thickness"), 4))),
                                  "outer": parse_color(k.get("outer_color", "")),
                                  "inner": parse_color(k.get("inner_color", "")),
                                  "font": parse_color(k.get("font_color", "")),
                                  "position": _pair(k.get("position", "0, -20"), screen),
                                  "halign": k.get("halign", "center"), "valign": k.get("valign", "center")})
    return out


def screen_size():
    """Grandezza logica del monitor principale (quella che usa hyprlock), o 1920×1080."""
    ok, out = system.run(["hyprctl", "monitors", "-j"])
    try:
        mons = json.loads(out) if ok else []
        m = next((x for x in mons if x.get("focused")), mons[0])
        scale = float(m.get("scale") or 1) or 1
        w, h = int(m["width"]) / scale, int(m["height"]) / scale
        if int(m.get("transform", 0)) % 2:
            w, h = h, w
        if 200 < w < 20000 and 200 < h < 20000:
            return [round(w), round(h)]
    except (ValueError, KeyError, IndexError, TypeError, AttributeError, StopIteration):
        pass
    return [1920, 1080]


def info(state=None, cfg_dir=None):
    """-> dict per l'anteprima; found=False se hyprlock.conf non c'è o non si può leggere."""
    path = os.path.expanduser("~/.config/hypr/hyprlock.conf")
    screen = screen_size()
    text = None
    try:
        real = files.resolve(path)
        for f in (state or {}).get("files", []):                 # gestito: si legge il modello (ruoli)
            if f.get("target") == real and cfg_dir:
                text = files.read_text(os.path.join(cfg_dir, "templates", os.path.basename(f["template"])))
                break
        if text is None:
            text = files.read_text(real)
    except (files.UnsafeFile, OSError, ValueError):
        return {"found": False, "screen": screen}
    return dict(parse(text, screen), found=True, screen=screen)
