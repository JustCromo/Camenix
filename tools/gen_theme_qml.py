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
            out[key] = valid(colors[key]) ? colors[key] : defaults[key]
        values = out
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
