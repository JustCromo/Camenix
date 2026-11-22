"""Modelli di config: i colori diventano segnaposto e tornano colori del tema.

Un segnaposto sostituisce solo le 6 cifre esadecimali: '#', trasparenza e rgba() restano del file.
  #FFD25AF2         ->  #{{cmx:accent}}F2
  rgba(2B2236ee)    ->  rgba({{cmx:textAlt}}ee)
  "rgba(e0b0ffff)"  ->  "rgba({{cmx:borderFrom:lower}}ff)"
  path = ~/sfondo.png  (se è lo sfondo del tema)  ->  path = {{cmx:wallpaper.lock}}
Così render(adopt(file)) restituisce il file di partenza."""
import os
import re

PH = re.compile(r"\{\{cmx:([A-Za-z0-9_.]+)(:lower)?\}\}")
HEXCOL = re.compile(r"(#|rgba?\()([0-9A-Fa-f]{6})((?:[0-9A-Fa-f]{2})?)(?![0-9A-Fa-f])")
PATHLINE = re.compile(r"^(\s*path\s*=\s*)(\S.*?)(\s*)$", re.M)


class RenderError(Exception):
    def __init__(self, key):
        super().__init__(key)
        self.key = key


def values(theme):
    """Tutto ciò che un segnaposto può valere (solo colori validati e percorsi validati)."""
    out = {k: v[1:] for k, v in theme["colors"].items()}
    out.update({f"terminal.{k}": v[1:] for k, v in theme.get("terminal", {}).items()})
    wp = theme.get("wallpaper", {})
    home = wp.get("home")
    lock = home if wp.get("lock_same", True) or not wp.get("lock") else wp.get("lock")
    if home:
        out["wallpaper.home"] = home
    if lock:
        out["wallpaper.lock"] = lock
    return out


def render(template, theme):
    vals = values(theme)

    def sub(m):
        key, lower = m.group(1), m.group(2)
        if key not in vals:
            raise RenderError(key)
        v = vals[key]
        return v.lower() if lower else v
    out = PH.sub(sub, template)
    if "{{cmx:" in out:                       # segnaposto malformato: meglio fermarsi che scriverlo
        raise RenderError("malformed")
    return out


def keys(template):
    return {m.group(1) for m in PH.finditer(template)}


def adopt(text, theme, prefer=()):
    """Testo di una config -> (modello, numero di segnaposto). Solo i colori uguali a un ruolo del tema
    diventano segnaposto; gli altri restano. In caso di colori uguali vincono i ruoli `prefer` (quelli
    che quel file usa davvero, es. i bordi per Hyprland), poi il primo ruolo dell'elenco."""
    by_hex = {}
    order = [k for k in prefer if k in theme["colors"]] + [k for k in theme["colors"] if k not in prefer]
    for key in order:
        value = theme["colors"][key]
        by_hex.setdefault(value[1:].upper(), key)
    count = 0

    def sub_color(m):
        nonlocal count
        prefix, digits, alpha = m.groups()
        role = by_hex.get(digits.upper())
        if role is None:
            return m.group(0)
        count += 1
        lower = ":lower" if digits.islower() and not digits.isdigit() else ""
        return f"{prefix}{{{{cmx:{role}{lower}}}}}{alpha}"
    template = HEXCOL.sub(sub_color, text)

    wp = theme.get("wallpaper", {})
    current = {p for p in (wp.get("home"), wp.get("lock")) if p}
    if current:
        def sub_path(m):
            nonlocal count
            if os.path.realpath(os.path.expanduser(m.group(2))) in {os.path.realpath(p) for p in current}:
                count += 1
                return f"{m.group(1)}{{{{cmx:wallpaper.lock}}}}{m.group(3)}"
            return m.group(0)
        template = PATHLINE.sub(sub_path, template)
    return template, count
