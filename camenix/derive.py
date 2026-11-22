"""Sfumature calcolate: quando cambi un colore principale, le sue sfumature lo seguono.

Ogni sfumatura ricorda di quanto differisce (tonalità, saturazione, luminosità) dal suo colore
principale nella palette originale, e applica la stessa differenza al colore nuovo.
Le famiglie il cui colore principale non è cambiato restano identiche (nessun arrotondamento).
I due colori del bordo delle finestre (borderFrom, borderTo) li sceglie l'utente: non seguono nessuno."""
import colorsys

from camenix import theme as th

FAMILY = {
    "accentHover": "accent", "accentSoft": "accent", "accentPale": "accent", "accentWarm": "accent",
    "accentGlow": "accent",
    "accentDeep": "accent2", "accentDeeper": "accent2",
    "secondaryLight": "secondary", "secondaryPale": "secondary", "secondaryPaler": "secondary",
    "secondaryMist": "secondary", "secondaryDeep": "secondary", "secondaryDarker": "secondary",
    "textAlt": "text", "textMuted": "text",
    "sheen": "glass", "paper": "glass", "borderIdle": "glass",
    "warningStrong": "warning", "caution": "warning",
    "errorBright": "error", "errorPale": "error",
}


def to_hls(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)


def to_hex(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h % 1.0, min(1, max(0, l)), min(1, max(0, s)))
    return "#%02X%02X%02X" % tuple(round(c * 255) for c in (r, g, b))


def shade(base_default, derived_default, base_new):
    """Applica a base_new la stessa differenza che c'è tra base_default e derived_default."""
    bh, bl, bs = to_hls(base_default)
    dh, dl, ds = to_hls(derived_default)
    nh, nl, ns = to_hls(base_new)
    # la luminosità segue in proporzione verso il bianco o verso il nero, così non "esce" dai limiti
    if dl >= bl:
        l = nl + (1 - nl) * ((dl - bl) / (1 - bl) if bl < 1 else 0)
    else:
        l = nl * (dl / bl if bl > 0 else 1)
    s = ns * (ds / bs) if bs > 0.02 else ds
    if ns < 0.02:                                  # colore nuovo grigio: le sfumature restano grigie
        s = 0
    return to_hex(nh + (dh - bh), l, s)


def derive(colors, previous=None):
    """-> nuovi colori: le sfumature dei principali cambiati rispetto a `previous` vengono ricalcolate."""
    defaults = th.defaults()
    previous = previous or defaults
    out = dict(colors)
    for derived, base in FAMILY.items():
        if colors.get(base) != previous.get(base):
            out[derived] = shade(defaults[base], defaults[derived], colors[base])
        elif derived in previous:
            # colore principale tornato com'era (es. "palette in uso" dopo un'altra palette):
            # tornano anche le sue sfumature, non restano quelle della prova di prima
            out[derived] = previous[derived]
    return out
