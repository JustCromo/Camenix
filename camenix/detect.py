"""Primo avvio: legge i colori che il desktop ha già, così Camenix parte da quelli (non da un tema suo).

Legge solo file di config nella home (con gli stessi controlli di sicurezza di tutto il resto):
  - bordi di Hyprland (active_border / inactive_border, file .conf o .lua)
  - kitty (background, foreground, color0..15, anche nei file inclusi)
  - mako (background-color, text-color, border-color)
  - sfondo attuale
Quello che non trova resta al valore predefinito. Non scrive niente."""
import glob
import os
import re

from camenix import derive as dv, files, theme as th, wallpaper

HEX = re.compile(r"(?:#|rgba?\()([0-9A-Fa-f]{6})(?:[0-9A-Fa-f]{2})?(?![0-9A-Fa-f])")
ACTIVE = re.compile(r"(?<![A-Za-z_])active_border")
INACTIVE = re.compile(r"(?<![A-Za-z_])inactive_border")
KITTY_KEYS = ("background", "foreground", "cursor", "selection_background", "selection_foreground") + \
             tuple(f"color{i}" for i in range(16))


def _read(path):
    try:
        return files.read_text(files.resolve(path))
    except (files.UnsafeFile, OSError, ValueError):
        return None


def _hexes(text):
    return ["#" + h.upper() for h in HEX.findall(text)]


def hypr_files():
    out = []
    for p in [os.path.expanduser("~/.config/hypr/hyprland.conf")] + \
            sorted(glob.glob(os.path.expanduser("~/.config/hypr/**/*.lua"), recursive=True)) + \
            sorted(glob.glob(os.path.expanduser("~/.config/hypr/**/*.conf"), recursive=True)):
        if p not in out and os.path.isfile(p) and not p.endswith(("hyprlock.conf", "hypridle.conf", "hyprpaper.conf")):
            out.append(p)
    return out


def hyprland():
    """-> {"active": [colori…], "inactive": colore o None} dalla prima config che li definisce."""
    found = {"active": [], "inactive": None}
    for p in hypr_files():
        text = _read(p)
        if not text:
            continue
        for line in text.splitlines():
            code = line.strip()
            if code.startswith("#") or code.startswith("--"):     # commenti di .conf e .lua
                continue
            m = ACTIVE.search(code)
            if m and not found["active"]:
                found["active"] = _hexes(code[m.end():])[:2]
            m = INACTIVE.search(code)
            if m and found["inactive"] is None:
                h = _hexes(code[m.end():])
                found["inactive"] = h[0] if h else None
        if found["active"]:
            break
    return found


def kitty():
    """-> colori di kitty trovati (solo quelli scritti nei file; il resto è il predefinito di kitty)."""
    main = os.path.expanduser("~/.config/kitty/kitty.conf")
    seen, out = set(), {}

    def walk(path, depth):
        real = os.path.realpath(path)
        if depth > 2 or real in seen or real.startswith(os.path.realpath(th.config_dir())):
            return                                  # i colori generati da Camenix non contano
        seen.add(real)
        text = _read(path)
        if not text:
            return
        for line in text.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) != 2:
                continue
            key, value = parts[0], parts[1].strip()
            if key == "include":
                inc = os.path.expanduser(value)
                if not os.path.isabs(inc):
                    inc = os.path.join(os.path.dirname(path), inc)
                walk(inc, depth + 1)
            elif key in KITTY_KEYS and re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
                out[key] = value.upper()
    if os.path.isfile(main):
        walk(main, 0)
    return out


def mako():
    text = _read(os.path.expanduser("~/.config/mako/config"))
    out = {}
    if not text:
        return out
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            break                                  # solo le impostazioni generali, non le sezioni
        if "=" in line:
            key, value = (s.strip() for s in line.split("=", 1))
            h = _hexes(value)
            if key in ("background-color", "text-color", "border-color") and h:
                out[key] = h[0]
    return out


def _lum(hex_color):
    def ch(i):
        c = int(hex_color[i:i + 2], 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(1) + 0.7152 * ch(3) + 0.0722 * ch(5)


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def detect():
    """-> (tema completo costruito dai colori trovati, elenco di cosa è stato trovato)."""
    theme = th.default_theme("Il mio desktop")
    found = []
    term = dict(th.TERMINAL_DEFAULTS)
    k = kitty()
    term.update(k)
    if k:
        found.append("kitty")
    theme["terminal"] = term
    h, m = hyprland(), mako()
    if h["active"]:
        found.append("hyprland")
    if m:
        found.append("mako")
    base = {}
    base["glass"] = m.get("background-color") or term["background"]
    text = m.get("text-color") or term["foreground"]
    if contrast(text, base["glass"]) < 4.5:            # testo illeggibile: bianco o quasi-nero, il più leggibile
        text = max(("#FFFFFF", "#1A1A1A"), key=lambda c: contrast(c, base["glass"]))
    base["text"] = text
    active = h["active"] or []
    base["borderFrom"] = active[0] if active else term["color4"]
    base["borderTo"] = active[1] if len(active) > 1 else base["borderFrom"]
    base["accent"] = m.get("border-color") or base["borderFrom"]
    base["accent2"] = base["borderTo"] if base["borderTo"] != base["accent"] else term["color3"]
    base["secondary"] = term["color5"]
    base["success"], base["warning"], base["error"] = term["color2"], term["color3"], term["color1"]
    colors = dv.derive(dict(th.defaults(), **base))
    if h["inactive"]:
        colors["borderIdle"] = h["inactive"]
    theme["colors"] = colors
    wp = wallpaper.current()
    if wp and wallpaper.is_image(wp):
        theme["wallpaper"]["home"] = wp
        found.append("wallpaper")
    theme, _ = th.normalize(theme)                    # ultima rete: tutto passa dai controlli di sempre
    return theme, found
