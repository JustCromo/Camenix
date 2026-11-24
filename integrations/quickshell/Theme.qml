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

    // ── leggibilità ─────────────────────────────────────
    // Colori usati come scritte e icone sopra il vetro delle isole (batteria, spegnimento, avvisi).
    // Se la palette li rende poco visibili (es. verde scuro su vetro scuro), si schiariscono o si
    // scuriscono quanto basta. La palette originale non cambia; theme.json resta com'è.
    readonly property var readableRoles: ({ text: 4.5, success: 4.5, error: 4.5, warning: 3, accent2: 3 })
    function lum(hex) {
        const ch = i => { const c = parseInt(hex.substr(i, 2), 16) / 255
                          return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4) }
        return 0.2126 * ch(1) + 0.7152 * ch(3) + 0.0722 * ch(5)
    }
    function contrast(x, y) { const p = lum(x), q = lum(y); return (Math.max(p, q) + 0.05) / (Math.min(p, q) + 0.05) }
    function toHsl(hex) {
        const r = parseInt(hex.substr(1, 2), 16) / 255, g = parseInt(hex.substr(3, 2), 16) / 255, b = parseInt(hex.substr(5, 2), 16) / 255
        const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn
        if (d === 0) return [0, 0, l]
        const s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn)
        let h = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4
        return [h / 6, s, l]
    }
    function fromHsl(h, s, l) {
        const f = n => { const k = (n + h * 12) % 12, a = s * Math.min(l, 1 - l)
                         const v = l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))
                         const x = Math.round(Math.max(0, Math.min(1, v)) * 255).toString(16).toUpperCase()
                         return x.length < 2 ? "0" + x : x }
        return "#" + f(0) + f(8) + f(4)
    }
    function readable(colors) {
        const out = {}
        for (const k in colors) out[k] = colors[k]
        const glass = out.glass, darken = lum(glass) > 0.18
        for (const role in readableRoles) {
            // palette originale intatta: identica a prima
            if (out[role] === defaults[role] && glass === defaults.glass) continue
            const target = Math.min(readableRoles[role], Math.max(3, contrast(defaults[role], defaults.glass)))
            const hsl = toHsl(out[role])
            let l = hsl[2]
            for (let i = 0; i < 60 && contrast(out[role], glass) < target; i++) {
                l += darken ? -0.02 : 0.02
                if (l < 0 || l > 1) break
                out[role] = fromHsl(hsl[0], hsl[1], l)
            }
        }
        return out
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
            out[key] = valid(colors[key]) ? colors[key].toUpperCase() : defaults[key]
        values = readable(out)
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
