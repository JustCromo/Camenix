#!/usr/bin/env python3
"""Rigenera integrations/quickshell/Theme.qml da camenix/data/roles.json (unica fonte dei ruoli)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
roles = json.load(open(os.path.join(ROOT, "camenix", "data", "roles.json"), encoding="utf-8"))["roles"]
defs = ",\n".join(f'        {r["key"]}: "{r["default"]}"' for r in roles)
props = "\n".join(f'    readonly property color {r["key"]}: values.{r["key"]}' for r in roles)
qml = f'''pragma Singleton
// Camenix · tema per Quickshell (generato da tools/gen_theme_qml.py: non modificare a mano)
// Legge ~/.config/camenix/theme.json e si aggiorna da solo quando il file cambia.
// Uso nei file QML:  color: Theme.text   ·   color: Theme.a(Theme.text, 0.6)
// Un file mancante, rotto o ostile non rompe nulla: si usano i colori predefiniti.
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {{
    id: theme

    // palette predefinita (= preset "Gudetama")
    readonly property var defaults: ({{
{defs}
    }})
    property var values: defaults
    property string name: "Gudetama"
    // cresce a ogni ricarica: utile a chi deve ridisegnare (Canvas)
    property int revision: 0

{props}

    // colore con trasparenza, identico al vecchio "#AARRGGBB" (es. a(Theme.text, 0.6))
    function a(c, alpha) {{
        const v = Math.max(0, Math.min(255, Math.round(alpha * 255)))
        return "#" + (v < 16 ? "0" : "") + v.toString(16) + String(c).slice(1)
    }}

    // ── leggibilità ─────────────────────────────────────
    // Colori usati come scritte e icone sopra il vetro delle isole (batteria, spegnimento, avvisi).
    // Se la palette li rende poco visibili (es. verde scuro su vetro scuro), si schiariscono o si
    // scuriscono quanto basta. La palette originale non cambia; theme.json resta com'è.
    readonly property var readableRoles: ({{ text: 4.5, success: 4.5, error: 4.5, warning: 3, accent2: 3 }})
    function lum(hex) {{
        const ch = i => {{ const c = parseInt(hex.substr(i, 2), 16) / 255
                          return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4) }}
        return 0.2126 * ch(1) + 0.7152 * ch(3) + 0.0722 * ch(5)
    }}
    function contrast(x, y) {{ const p = lum(x), q = lum(y); return (Math.max(p, q) + 0.05) / (Math.min(p, q) + 0.05) }}
    function toHsl(hex) {{
        const r = parseInt(hex.substr(1, 2), 16) / 255, g = parseInt(hex.substr(3, 2), 16) / 255, b = parseInt(hex.substr(5, 2), 16) / 255
        const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn
        if (d === 0) return [0, 0, l]
        const s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn)
        let h = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4
        return [h / 6, s, l]
    }}
    function fromHsl(h, s, l) {{
        const f = n => {{ const k = (n + h * 12) % 12, a = s * Math.min(l, 1 - l)
                         const v = l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))
                         const x = Math.round(Math.max(0, Math.min(1, v)) * 255).toString(16).toUpperCase()
                         return x.length < 2 ? "0" + x : x }}
        return "#" + f(0) + f(8) + f(4)
    }}
    function readable(colors) {{
        const out = {{}}
        for (const k in colors) out[k] = colors[k]
        const glass = out.glass, darken = lum(glass) > 0.18
        for (const role in readableRoles) {{
            // palette originale intatta: identica a prima
            if (out[role] === defaults[role] && glass === defaults.glass) continue
            const target = Math.min(readableRoles[role], Math.max(3, contrast(defaults[role], defaults.glass)))
            const hsl = toHsl(out[role])
            let l = hsl[2]
            for (let i = 0; i < 60 && contrast(out[role], glass) < target; i++) {{
                l += darken ? -0.02 : 0.02
                if (l < 0 || l > 1) break
                out[role] = fromHsl(hsl[0], hsl[1], l)
            }}
        }}
        return out
    }}

    readonly property int maxBytes: 65536
    function valid(v) {{ return typeof v === "string" && /^#[0-9A-Fa-f]{{6}}$/.test(v) }}

    function load(raw) {{
        let data = null
        if (typeof raw === "string" && raw.length > 0 && raw.length <= maxBytes) {{
            try {{ data = JSON.parse(raw) }} catch (e) {{ data = null }}
        }}
        const colors = (data && typeof data === "object" && data.colors && typeof data.colors === "object") ? data.colors : {{}}
        const out = {{}}
        for (const key in defaults)
            out[key] = valid(colors[key]) ? colors[key].toUpperCase() : defaults[key]
        values = readable(out)
        name = (data && typeof data.name === "string" && data.name.length < 61) ? data.name : "Gudetama"
        revision++
    }}

    FileView {{
        id: file
        path: Quickshell.env("HOME") + "/.config/camenix/theme.json"
        watchChanges: true
        onFileChanged: reload()
        onLoaded: theme.load(file.text())
        onLoadFailed: theme.load("")
    }}
}}
'''
open(os.path.join(ROOT, "integrations", "quickshell", "Theme.qml"), "w", encoding="utf-8").write(qml)
print("Theme.qml rigenerato:", len(roles), "ruoli")
