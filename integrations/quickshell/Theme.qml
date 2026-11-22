pragma Singleton
// Camenix · tema per Quickshell (generato da tools/gen_theme_qml.py: non modificare a mano)
// Legge ~/.config/camenix/theme.json e si aggiorna da solo quando il file cambia.
// Uso nei file QML:  color: Theme.text   ·   color: Theme.a(Theme.text, 0.6)
// Un file mancante, rotto o ostile non rompe nulla: si usano i colori predefiniti.
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: theme

    // palette predefinita (= preset "Gudetama")
    readonly property var defaults: ({
        text: "#1E1528",
        glass: "#FBF8FF",
        accent: "#FFD25A",
        accent2: "#E8892A",
        secondary: "#B9A6F5",
        success: "#2F7A4B",
        warning: "#E8892A",
        error: "#C2384F",
        sheen: "#FFFFFF",
        accentHover: "#FFE08A",
        accentSoft: "#FFE7A6",
        accentPale: "#FFF1CC",
        accentWarm: "#F5C451",
        accentGlow: "#F5A623",
        accentDeep: "#B85A0C",
        accentDeeper: "#A8530A",
        secondaryLight: "#D4C8FA",
        secondaryPale: "#E9E2FB",
        secondaryPaler: "#F3EFFD",
        secondaryMist: "#DCD2F7",
        secondaryDeep: "#8E78E0",
        secondaryDarker: "#5E4E92",
        textAlt: "#2B2236",
        warningStrong: "#D4661A",
        caution: "#C99A1E",
        errorBright: "#D6455E",
        errorPale: "#FFD9DE",
        borderFrom: "#E0B0FF",
        borderTo: "#FFBF00",
        borderIdle: "#FEFEFA",
        paper: "#FFF4DA",
        textMuted: "#8A7FA8"
    })
    property var values: defaults
    property string name: "Gudetama"
    // cresce a ogni ricarica: utile a chi deve ridisegnare (Canvas)
    property int revision: 0

    readonly property color text: values.text
    readonly property color glass: values.glass
    readonly property color accent: values.accent
    readonly property color accent2: values.accent2
    readonly property color secondary: values.secondary
    readonly property color success: values.success
    readonly property color warning: values.warning
    readonly property color error: values.error
    readonly property color sheen: values.sheen
    readonly property color accentHover: values.accentHover
    readonly property color accentSoft: values.accentSoft
    readonly property color accentPale: values.accentPale
    readonly property color accentWarm: values.accentWarm
    readonly property color accentGlow: values.accentGlow
    readonly property color accentDeep: values.accentDeep
    readonly property color accentDeeper: values.accentDeeper
    readonly property color secondaryLight: values.secondaryLight
    readonly property color secondaryPale: values.secondaryPale
    readonly property color secondaryPaler: values.secondaryPaler
    readonly property color secondaryMist: values.secondaryMist
    readonly property color secondaryDeep: values.secondaryDeep
    readonly property color secondaryDarker: values.secondaryDarker
    readonly property color textAlt: values.textAlt
    readonly property color warningStrong: values.warningStrong
    readonly property color caution: values.caution
    readonly property color errorBright: values.errorBright
    readonly property color errorPale: values.errorPale
    readonly property color borderFrom: values.borderFrom
    readonly property color borderTo: values.borderTo
    readonly property color borderIdle: values.borderIdle
    readonly property color paper: values.paper
    readonly property color textMuted: values.textMuted

    // colore con trasparenza, identico al vecchio "#AARRGGBB" (es. a(Theme.text, 0.6))
    function a(c, alpha) {
        const v = Math.max(0, Math.min(255, Math.round(alpha * 255)))
        return "#" + (v < 16 ? "0" : "") + v.toString(16) + String(c).slice(1)
    }

    readonly property int maxBytes: 65536
    function valid(v) { return typeof v === "string" && /^#[0-9A-Fa-f]{6}$/.test(v) }

    function load(raw) {
        let data = null
        if (typeof raw === "string" && raw.length > 0 && raw.length <= maxBytes) {
            try { data = JSON.parse(raw) } catch (e) { data = null }
        }
        const colors = (data && typeof data === "object" && data.colors && typeof data.colors === "object") ? data.colors : {}
        const out = {}
        for (const key in defaults)
            out[key] = valid(colors[key]) ? colors[key] : defaults[key]
        values = out
        name = (data && typeof data.name === "string" && data.name.length < 61) ? data.name : "Gudetama"
        revision++
    }

    FileView {
        id: file
        path: Quickshell.env("HOME") + "/.config/camenix/theme.json"
        watchChanges: true
        onFileChanged: reload()
        onLoaded: theme.load(file.text())
        onLoadFailed: theme.load("")
    }
}
