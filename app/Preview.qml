// anteprima in miniatura: desktop (isole, kitty, rofi) o schermata di blocco, con i colori della bozza
import QtQuick
import QtQuick.Effects

Rectangle {
    id: pv
    property var ui
    property var theme: null              // bozza
    property bool lock: false
    property var lockInfo: null           // com'è fatta la schermata di blocco vera (hyprlock.conf)
    property string user: ""
    readonly property bool realLock: !!lockInfo && lockInfo.found
    readonly property var bg: realLock && lockInfo.background ? lockInfo.background : null
    property var highlight: []            // zone da illuminare (passando sopra un colore)
    function hl(z) { return highlight.indexOf(z) >= 0 }
    property string label: lock ? "Blocco schermo" : "Scrivania"
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

    radius: 18
    clip: true
    color: ui.panel
    border.width: 1.5
    border.color: ui.line

    Image {
        id: img
        anchors.fill: parent
        source: pv.wall
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        sourceSize.width: 1400
    }
    MultiEffect {                          // blocco: stesso sfondo sfocato
        anchors.fill: parent
        source: img
        visible: pv.lock
        blurEnabled: true
        // come hyprlock: più passaggi e più grandezza = più sfocato; luminosità e vivacità dal file
        blur: pv.bg ? Math.min(1, pv.bg.blur_passes * pv.bg.blur_size / 21) : 1.0
        blurMax: 48
        brightness: pv.bg ? Math.max(-1, Math.min(1, pv.bg.brightness - 1)) : -0.03
        saturation: pv.bg ? Math.max(-1, Math.min(1, pv.bg.vibrancy)) : 0
    }
    Text {
        visible: pv.wall === ""
        anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 14
        text: "nessuno sfondo: scegline uno qui sotto"
        color: ui.muted
        font.family: ui.font
        font.pixelSize: 11
    }

    // ── home: isole, kitty, rofi ───────────────────────
    Item {
        anchors.fill: parent
        visible: !pv.lock && !!pv.theme
        component Pill: Rectangle {
            height: 16; radius: 8
            color: pv.a(pv.c.glass || "#FBF8FF", 0.75)
            border.width: 1
            border.color: pv.c.accent || "#FFD25A"
            property alias text: t.text
            Glow { on: pv.hl("pills"); r: 8 }
            Text { id: t; anchors.centerIn: parent; color: pv.c.text || "#1E1528"; font.family: ui.font; font.pixelSize: 8; font.bold: true }
        }
        Pill { x: 12; y: 8; width: 40; text: "● ○" }
        Pill { anchors.horizontalCenter: parent.horizontalCenter; y: 8; width: 84; text: "10:32" }
        Pill { anchors.right: parent.right; anchors.rightMargin: 12; y: 8; width: 40; text: "97%" }
        Pill { anchors.right: parent.right; anchors.rightMargin: 58; y: 8; width: 38; text: "☁ 14°" }

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
                       text: "<font color='" + (pv.term.color2 || "#19CB00") + "'>ivan@archlinux</font> <font color='" + (pv.term.color4 || "#0D73CC") + "'>~</font> $ fastfetch" }
                Text { font.family: ui.font; font.pixelSize: 9; color: pv.term.foreground || "#DDDDDD"; text: "OS: Arch Linux · WM: Hyprland" }
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

}
