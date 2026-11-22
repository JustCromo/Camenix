// anteprima in miniatura: desktop (isole, kitty, rofi) o schermata di blocco, con i colori della bozza
import QtQuick

Rectangle {
    id: pv
    property var ui
    property var theme: null              // bozza
    property bool lock: false
    property var lockInfo: null           // com'è fatta la schermata di blocco vera (hyprlock.conf)
    property string user: ""
    property string emptyText: ""
    // nome utente per il terminale finto: solo lettere, cifre e . _ - (finisce in un testo con markup)
    readonly property string safeUser: (user.replace(/[^A-Za-z0-9._-]/g, "") || "user").slice(0, 24)
    readonly property bool realLock: !!lockInfo && lockInfo.found
    readonly property real screenW: lockInfo && lockInfo.screen ? lockInfo.screen[0] : 1920
    readonly property real k: width / screenW              // scala: pixel dello schermo vero -> anteprima
    readonly property var bg: realLock && lockInfo.background ? lockInfo.background : null
    property var highlight: []            // zone da illuminare (passando sopra un colore)
    function hl(z) { return highlight.indexOf(z) >= 0 }
    readonly property var c: theme ? theme.colors : ({})
    readonly property var term: theme ? theme.terminal : ({})
    readonly property string wall: {
        if (!theme) return ""
        const w = theme.wallpaper
        const p = (lock && !w.lock_same && w.lock) ? w.lock : w.home
        return p ? "file://" + p : ""
    }
    // testo leggibile sopra un colore: quasi nero o bianco
    function ink(hex) {
        const l = [1, 3, 5].map(i => parseInt(hex.substr(i, 2), 16) / 255).map(c => c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4))
        return 0.2126 * l[0] + 0.7152 * l[1] + 0.0722 * l[2] > 0.18 ? "#1E1528" : "#FFFFFF"
    }
    function a(hex, alpha) { return Qt.rgba(parseInt(hex.substr(1, 2), 16) / 255, parseInt(hex.substr(3, 2), 16) / 255, parseInt(hex.substr(5, 2), 16) / 255, alpha) }

    radius: 22
    clip: true
    color: ui.panel

    Image {
        id: img
        anchors.fill: parent
        visible: !pv.lock
        source: pv.wall
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        sourceSize.width: 1400
    }
    // blocco: sfondo sfocato come hyprlock. Raggio di hyprlock ≈ blur_size × 2^blur_passes / 2.
    readonly property real lockRadius: bg ? Math.min(400, bg.blur_size * Math.pow(2, Math.min(bg.blur_passes, 6)) / 2) : 20
    // Sfocatura fatta a mano, senza effetti grafici (che su alcuni sistemi non si vedono): l'immagine viene
    // disegnata piccola (160 px), sfocata con tre passaggi di media sui vicini (≈ sfocatura gaussiana) e poi
    // ingrandita con interpolazione morbida. Funziona con qualsiasi scheda video e anche nei test automatici.
    Image {
        id: lockSrc
        visible: false
        source: pv.lock ? pv.wall : ""
        asynchronous: true
        sourceSize.width: 640
        onStatusChanged: if (status === Image.Ready) lockCanvas.requestPaint()
    }
    Canvas {                                  // la versione piccola e sfocata, ingrandita a tutta l'anteprima
        id: lockCanvas
        visible: pv.lock
        readonly property int sw: 160
        width: sw
        height: Math.max(1, Math.round(sw * pv.height / Math.max(1, pv.width)))
        transformOrigin: Item.TopLeft
        scale: pv.width / sw
        smooth: true                          // ingrandimento con interpolazione morbida
        // raggio in pixel della versione piccola (tarato sulla schermata vera di hyprlock)
        readonly property int r: Math.max(1, Math.min(12, Math.round(pv.lockRadius * sw / pv.screenW)))
        readonly property string key: [pv.lock, pv.wall, r, height].join()
        onKeyChanged: requestPaint()
        onPaint: {
            const ctx = getContext("2d")
            ctx.reset()
            if (!pv.lock || lockSrc.status !== Image.Ready) return
            const iw = lockSrc.implicitWidth, ih = lockSrc.implicitHeight
            if (iw < 1 || ih < 1) return
            // come PreserveAspectCrop (la forma a 9 argomenti di drawImage non è affidabile con un Image)
            const sc = Math.max(width / iw, height / ih), dw = iw * sc, dh = ih * sc
            ctx.drawImage(lockSrc, (width - dw) / 2, (height - dh) / 2, dw, dh)
            const src = ctx.getImageData(0, 0, width, height)
            const out = ctx.createImageData(width, height)
            pv.boxBlur(src.data, out.data, width, height, r)
            // forma completa a 7 argomenti: quella corta, in Qt, a volte non scrive niente
            ctx.putImageData(out, 0, 0, 0, 0, width, height)
        }
    }
    // media dei vicini in orizzontale e in verticale, tre volte (si avvicina a una sfocatura gaussiana)
    function boxBlur(src, dst, w, h, r) {
        const n = w * h * 4
        let a = new Float32Array(n), t = new Float32Array(n)
        for (let i = 0; i < n; i++) a[i] = src[i]
        for (let pass = 0; pass < 3; pass++) {
            for (let y = 0; y < h; y++) for (let c = 0; c < 4; c++) {
                let acc = 0
                for (let x = -r; x <= r; x++) acc += a[(y * w + Math.min(w - 1, Math.max(0, x))) * 4 + c]
                for (let x = 0; x < w; x++) {
                    t[(y * w + x) * 4 + c] = acc / (2 * r + 1)
                    acc += a[(y * w + Math.min(w - 1, x + r + 1)) * 4 + c] - a[(y * w + Math.max(0, x - r)) * 4 + c]
                }
            }
            for (let x = 0; x < w; x++) for (let c = 0; c < 4; c++) {
                let acc = 0
                for (let y = -r; y <= r; y++) acc += t[(Math.min(h - 1, Math.max(0, y)) * w + x) * 4 + c]
                for (let y = 0; y < h; y++) {
                    a[(y * w + x) * 4 + c] = acc / (2 * r + 1)
                    acc += t[(Math.min(h - 1, y + r + 1) * w + x) * 4 + c] - t[(Math.max(0, y - r) * w + x) * 4 + c]
                }
            }
        }
        for (let i = 0; i < n; i++) dst[i] = Math.round(a[i])
    }
    Rectangle {                              // luminosità di hyprlock (brightness < 1 = più scuro)
        anchors.fill: parent
        visible: pv.lock && !!pv.bg
        color: pv.bg && pv.bg.brightness < 1 ? "black" : "white"
        opacity: pv.bg ? Math.min(0.8, Math.abs(1 - pv.bg.brightness)) : 0
    }
    Text {
        visible: pv.wall === ""
        anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 14
        text: pv.emptyText
        color: ui.muted
        font.family: ui.font
        font.pixelSize: 11
    }

    // ── home: isole, kitty, rofi ───────────────────────
    Item {
        anchors.fill: parent
        visible: !pv.lock && !!pv.theme
        // isole come quelle di Quickshell: vetro (sfondo al 40%) con bordo che sfuma da secondario chiaro ad accento
        component Pill: Canvas {
            id: pill
            property string text: ""
            height: Math.round(34 * pv.k)
            readonly property string key: [pv.c.glass, pv.c.secondaryLight, pv.c.accent, width, height].join()
            onKeyChanged: requestPaint()
            onPaint: {
                const ctx = getContext("2d"), r = height / 2, t = Math.max(1, 1.6 * pv.k)
                ctx.reset()
                ctx.beginPath(); ctx.roundedRect(t / 2, t / 2, width - t, height - t, r - t / 2, r - t / 2)
                ctx.fillStyle = pv.a(pv.c.glass || "#FBF8FF", 0.4); ctx.fill()
                const g = ctx.createLinearGradient(0, 0, width, 0)
                g.addColorStop(0, pv.a(pv.c.secondaryLight || "#D4C8FA", 0.902))
                g.addColorStop(1, pv.a(pv.c.accent || "#FFD25A", 0.902))
                ctx.lineWidth = t; ctx.strokeStyle = g; ctx.stroke()
            }
            Glow { on: pv.hl("pills"); r: pill.height / 2 }
            Text { anchors.centerIn: parent; text: pill.text; color: pv.c.text || "#1E1528"; font.family: ui.font; font.pixelSize: Math.max(6, 13 * pv.k); font.bold: true }
        }
        Pill { x: 14 * pv.k; y: 10 * pv.k; width: 84 * pv.k; text: "● ○" }
        Pill { anchors.horizontalCenter: parent.horizontalCenter; y: 10 * pv.k; width: 170 * pv.k; text: "10:32" }
        Pill { anchors.right: parent.right; anchors.rightMargin: 14 * pv.k; y: 10 * pv.k; width: 84 * pv.k; text: "97%" }
        Pill { anchors.right: parent.right; anchors.rightMargin: 108 * pv.k; y: 10 * pv.k; width: 84 * pv.k; text: "☁ 14°" }

        Rectangle {                         // finestra di kitty con il bordo di Hyprland (gradiente inizio → fine)
            x: parent.width * 0.06; y: parent.height * 0.22
            width: parent.width * 0.48; height: parent.height * 0.62
            radius: 8
            gradient: Gradient { orientation: Gradient.Horizontal
                GradientStop { position: 0; color: pv.c.borderFrom || "#E0B0FF" }
                GradientStop { position: 1; color: pv.c.borderTo || "#FFBF00" } }
            Glow { on: pv.hl("border"); r: 8 }
            Rectangle {
                anchors.fill: parent; anchors.margins: 2.5
                radius: 6
                color: pv.term.background || "#000000"
                Glow { on: pv.hl("term"); r: 6; anchors.margins: 3 }
            }
            Column {
                x: 10; y: 8; spacing: 3
                Text { textFormat: Text.StyledText; font.family: ui.font; font.pixelSize: 9; color: pv.term.foreground || "#DDDDDD"
                       text: "<font color='" + (pv.term.color2 || "#19CB00") + "'>" + pv.safeUser + "@hyprland</font> <font color='" + (pv.term.color4 || "#0D73CC") + "'>~</font> $ fastfetch" }
                Text { font.family: ui.font; font.pixelSize: 9; color: pv.term.foreground || "#DDDDDD"; text: "WM: Hyprland · Theme: Camenix" }
                Row { spacing: 2; Repeater { model: 8; Rectangle { width: 12; height: 8; color: pv.term["color" + index] || "#000" } } }
                Text { font.family: ui.font; font.pixelSize: 9; color: pv.term.foreground || "#DDDDDD"; text: "$ █" }
            }
        }
        Rectangle {                         // rofi
            anchors.right: parent.right; anchors.rightMargin: parent.width * 0.06
            y: parent.height * 0.26
            width: parent.width * 0.34; height: parent.height * 0.5
            radius: 10
            color: pv.a(pv.c.glass || "#FBF8FF", 0.95)
            border.width: 1.5
            border.color: pv.c.secondary || "#B9A6F5"
            Glow { on: pv.hl("menu"); r: 10 }
            Column {
                x: 8; y: 8; width: parent.width - 16; spacing: 5
                Rectangle { width: parent.width; height: 16; radius: 8; color: pv.a(pv.c.text || "#1E1528", 0.07); border.width: 1; border.color: pv.a(pv.c.secondary || "#B9A6F5", 0.6)
                    Text { x: 8; anchors.verticalCenter: parent.verticalCenter; text: "Cerca…"; color: pv.a(pv.c.text || "#1E1528", 0.55); font.family: ui.font; font.pixelSize: 8 } }
                Rectangle { width: parent.width; height: 18; radius: 6; color: pv.c.accent || "#FFD25A"
                    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 2; color: pv.c.accent2 || "#E8892A" }
                    Text { x: 8; anchors.verticalCenter: parent.verticalCenter; text: "Camenix"; color: pv.ink(pv.c.accent || "#FFD25A"); font.family: ui.font; font.pixelSize: 8; font.bold: true } }
                Repeater { model: ["kitty", "Brave"]
                    Text { x: 8; text: modelData; color: pv.c.text || "#1E1528"; font.family: ui.font; font.pixelSize: 8 } }
            }
        }
    }

    // ── blocco: orologio e campo password ──────────────
    LockView {
        anchors.fill: parent
        visible: pv.lock && !!pv.theme && pv.realLock
        info: pv.lockInfo
        theme: pv.theme
        user: pv.user
        font: ui.font
        Glow { on: pv.hl("lock") || pv.hl("clock"); r: 18; anchors.margins: 8 }
    }
    Column {                                 // senza hyprlock.conf: un blocco generico
        visible: pv.lock && !!pv.theme && !pv.realLock
        anchors.centerIn: parent
        spacing: 8
        Text { anchors.horizontalCenter: parent.horizontalCenter; text: "10:32"; color: pv.a(pv.c.textAlt || "#2B2236", 0.93); font.family: ui.font; font.pixelSize: 34; font.weight: Font.ExtraBold
               Glow { on: pv.hl("clock"); r: 8 } }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 170; height: 24; radius: 12
            color: pv.a(pv.c.glass || "#FBF8FF", 0.25)
            border.width: 2
            border.color: pv.c.accent || "#FFD25A"
            Glow { on: pv.hl("lock"); r: 12 }
        }
    }

    RoundCorners { radius: pv.radius; bg: ui.window; line: ui.line }
}
