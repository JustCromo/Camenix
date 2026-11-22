// schermata di blocco disegnata dalla config vera di hyprlock (posizioni, grandezze, colori)
// I colori collegati a un ruolo del tema seguono la bozza, gli altri restano quelli del file.
import QtQuick

Item {
    id: lv
    property var info: null                 // risposta di `camenix-engine lockscreen`
    property var theme: null                // bozza
    property string font: "JetBrainsMono Nerd Font"
    property string user: ""
    readonly property real sw: info ? info.screen[0] : 1920
    readonly property real sh: info ? info.screen[1] : 1080
    readonly property real s: Math.min(width / sw, height / sh)     // scala schermo vero -> anteprima

    function rgba(stop) {
        if (!stop) return "transparent"
        let hex = stop.hex
        if (stop.role && theme) hex = stop.role.indexOf("terminal.") === 0 ? theme.terminal[stop.role.slice(9)] : theme.colors[stop.role]
        if (!/^#[0-9A-Fa-f]{6}$/.test(hex || "")) return "transparent"
        return Qt.rgba(parseInt(hex.substr(1, 2), 16) / 255, parseInt(hex.substr(3, 2), 16) / 255, parseInt(hex.substr(5, 2), 16) / 255, stop.a)
    }
    function first(c, fallback) { return c && c.stops.length ? rgba(c.stops[0]) : fallback }
    // posizione come la calcola hyprlock: x verso destra, y verso l'alto, rispetto all'allineamento
    function px(it, w) {
        const ox = (width - sw * s) / 2, x = it.position[0] * s
        if (it.halign === "left") return ox + x
        if (it.halign === "right") return ox + sw * s - w + x
        return ox + (sw * s - w) / 2 + x
    }
    function py(it, h) {
        const oy = (height - sh * s) / 2, y = it.position[1] * s
        if (it.valign === "top") return oy - y
        if (it.valign === "bottom") return oy + sh * s - h - y
        return oy + (sh * s - h) / 2 - y
    }

    Repeater {
        model: lv.info ? lv.info.labels : []
        Text {
            required property var modelData
            readonly property var it: modelData
            x: lv.px(it, implicitWidth); y: lv.py(it, implicitHeight)
            textFormat: Text.PlainText                // il testo viene da un file: mai interpretato
            text: it.kind === "time" ? "10:32"
                : it.kind === "date" ? Qt.formatDate(new Date(), "dddd d MMMM")
                : it.kind === "user" ? lv.user : it.text
            color: lv.first(it.color, "white")
            font.family: lv.font
            font.pixelSize: Math.max(4, it.font_size * lv.s)
            font.weight: it.bold ? Font.ExtraBold : Font.Normal
        }
    }
    Repeater {
        model: lv.info ? lv.info.inputs : []
        Canvas {                                      // campo password: interno + bordo (anche a gradiente)
            id: field
            required property var modelData
            readonly property var it: modelData
            width: Math.max(8, it.size[0] * lv.s); height: Math.max(6, it.size[1] * lv.s)
            x: lv.px(it, width); y: lv.py(it, height)
            readonly property string key: JSON.stringify([lv.theme ? lv.theme.colors : null, width, height])
            onKeyChanged: requestPaint()
            onPaint: {
                const c = getContext("2d"), t = Math.max(1, it.outline * lv.s)
                c.reset()
                const r = it.rounding < 0 ? height / 2 : Math.min(height / 2, it.rounding * lv.s)
                c.beginPath(); c.roundedRect(t / 2, t / 2, width - t, height - t, Math.max(0, r - t / 2), Math.max(0, r - t / 2))
                c.fillStyle = lv.first(it.inner, "transparent"); c.fill()
                if (it.outer && it.outer.stops.length) {
                    let st = it.outer.stops[0]
                    let style = lv.rgba(st)
                    if (it.outer.stops.length > 1) {          // gradiente con l'angolo del file
                        const a = it.outer.angle * Math.PI / 180, cx = width / 2, cy = height / 2
                        const dx = Math.cos(a) * width / 2, dy = Math.sin(a) * height / 2
                        style = c.createLinearGradient(cx - dx, cy + dy, cx + dx, cy - dy)
                        for (let i = 0; i < it.outer.stops.length; i++)
                            style.addColorStop(i / (it.outer.stops.length - 1), lv.rgba(it.outer.stops[i]))
                    }
                    c.lineWidth = t; c.strokeStyle = style; c.stroke()
                }
            }
        }
    }
}
