// Camenix · finestra principale: anteprima a sinistra, colori a destra, azioni in basso
import QtQuick

Rectangle {
    id: main
    property var eng

    // colori dell'app: seguono il tema applicato, in versione chiara o scura
    readonly property var t: eng.current ? eng.current.colors : null
    readonly property bool dark: eng.mode === "dark"
    QtObject {
        id: pal
        readonly property string font: "JetBrainsMono Nerd Font"
        readonly property color window: main.dark ? Qt.darker(main.t ? main.t.text : "#1E1528", 1.05) : (main.t ? main.t.glass : "#FBF8FF")
        readonly property color fg: main.dark ? (main.t ? main.t.glass : "#FBF8FF") : (main.t ? main.t.text : "#1E1528")
        readonly property color muted: Qt.alpha(fg, 0.6)
        readonly property color line: main.dark ? Qt.alpha(main.t ? main.t.secondary : "#B9A6F5", 0.35) : (main.t ? main.t.secondaryLight : "#D4C8FA")
        readonly property color card: main.dark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(1, 1, 1, 0.6)
        readonly property color hover: main.dark ? Qt.rgba(1, 1, 1, 0.1) : Qt.rgba(1, 1, 1, 0.95)
        readonly property color button: main.dark ? Qt.rgba(1, 1, 1, 0.07) : "#FFFFFF"
        readonly property color input: main.dark ? Qt.rgba(1, 1, 1, 0.08) : "#FFFFFF"
        readonly property color accent: main.t ? main.t.accent : "#FFD25A"
        readonly property color accentHover: main.t ? main.t.accentHover : "#FFE08A"
        readonly property color accent2: main.t ? main.t.accent2 : "#E8892A"
        readonly property color onAccent: main.t ? main.t.text : "#1E1528"
        readonly property color heading: main.dark ? (main.t ? main.t.secondary : "#B9A6F5") : (main.t ? main.t.secondaryDeep : "#8E78E0")
        readonly property color ok: main.dark ? "#7DE1A5" : (main.t ? main.t.success : "#2F7A4B")
        readonly property color bad: main.dark ? "#FF8FA0" : (main.t ? main.t.error : "#C2384F")
    }
    color: pal.window

    // ruoli mostrati come riquadri
    readonly property var roles: [
        { key: "glass", label: "Vetro isole" }, { key: "text", label: "Testo", against: "glass" },
        { key: "accent", label: "Accento" }, { key: "accent2", label: "Accento 2" },
        { key: "secondary", label: "Secondario" }, { key: "terminal.background", label: "Terminale" },
        { key: "success", label: "Successo" }, { key: "warning", label: "Avviso" }, { key: "error", label: "Errore" }
    ]
    function hexOf(key) {
        if (!eng.draft) return "#000000"
        return key.indexOf("terminal.") === 0 ? eng.draft.terminal[key.slice(9)] : eng.draft.colors[key]
    }

    // ── intestazione ───────────────────────────────────
    Row {
        id: header
        x: 22; y: 16
        spacing: 12
        Image { width: 40; height: 40; source: Qt.resolvedUrl("assets/camenix.svg"); sourceSize.width: 80; sourceSize.height: 80 }
        Column {
            anchors.verticalCenter: parent.verticalCenter
            Text { text: "Camenix"; color: pal.fg; font.family: pal.font; font.pixelSize: 19; font.weight: Font.ExtraBold }
            Text { text: "tema del desktop · Hyprland"; color: pal.muted; font.family: pal.font; font.pixelSize: 11 }
        }
    }
    Rectangle {                                     // interruttore chiaro / scuro
        anchors.right: parent.right; anchors.rightMargin: 22
        y: 20
        width: 74; height: 32; radius: 16
        color: pal.card
        border.width: 1.5; border.color: pal.line
        Rectangle {
            width: 28; height: 26; radius: 13; y: 3
            x: main.dark ? parent.width - width - 3 : 3
            color: pal.accent
            Behavior on x { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
        }
        Text { x: 10; anchors.verticalCenter: parent.verticalCenter; text: "☀"; color: pal.fg; font.pixelSize: 14 }
        Text { anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: "☾"; color: pal.fg; font.pixelSize: 14 }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: main.eng.setMode(main.dark ? "light" : "dark") }
    }
    Rectangle { x: 0; y: 72; width: parent.width; height: 1; color: pal.line }

    // ── anteprima ──────────────────────────────────────
    Item {
        id: left
        x: 22; y: 92
        width: parent.width * 0.53
        height: parent.height - y - bottom.height - 20
        Text { id: h1; text: "ANTEPRIMA"; color: pal.heading; font.family: pal.font; font.pixelSize: 12; font.letterSpacing: 1.5; font.weight: Font.Bold }
        Preview { id: homePv; ui: pal; theme: main.eng.draft; anchors.top: h1.bottom; anchors.topMargin: 10; width: parent.width; height: (parent.height - 120) * 0.62 }
        Preview { id: lockPv; ui: pal; theme: main.eng.draft; lock: true; anchors.top: homePv.bottom; anchors.topMargin: 12; width: parent.width; height: (parent.height - 120) * 0.38 }
        Row {
            anchors.top: lockPv.bottom; anchors.topMargin: 14
            spacing: 12
            Btn { ui: pal; text: "🖼  Carica sfondo…"; primary: true; onClicked: main.eng.chooseWallpaper("home") }
            Rectangle {                              // interruttore: blocco con lo stesso sfondo
                anchors.verticalCenter: parent.verticalCenter
                width: 38; height: 20; radius: 10
                readonly property bool on: main.eng.draft ? main.eng.draft.wallpaper.lock_same : true
                color: on ? pal.accent2 : pal.card
                border.width: 1; border.color: pal.line
                Rectangle { width: 16; height: 16; radius: 8; y: 2; x: parent.on ? parent.width - 18 : 2; color: "white"
                            Behavior on x { NumberAnimation { duration: 140 } } }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: main.eng.setLockSame(!parent.on) }
            }
            Text { anchors.verticalCenter: parent.verticalCenter; text: "Blocco: stesso sfondo, sfocato"; color: pal.fg; font.family: pal.font; font.pixelSize: 12 }
            Btn { ui: pal; visible: main.eng.draft && !main.eng.draft.wallpaper.lock_same; text: "Sfondo del blocco…"; onClicked: main.eng.chooseWallpaper("lock") }
        }
    }

    // ── colori ─────────────────────────────────────────
    Item {
        anchors.left: left.right; anchors.leftMargin: 22
        anchors.right: parent.right; anchors.rightMargin: 22
        y: 92
        height: left.height
        Text { id: h2; text: "COLORI"; color: pal.heading; font.family: pal.font; font.pixelSize: 12; font.letterSpacing: 1.5; font.weight: Font.Bold }
        Text { anchors.right: parent.right; anchors.verticalCenter: h2.verticalCenter; text: "le sfumature seguono da sole"; color: pal.muted; font.family: pal.font; font.pixelSize: 10 }
        Grid {
            id: grid
            anchors.top: h2.bottom; anchors.topMargin: 10
            width: parent.width
            columns: 3
            spacing: 12
            Repeater {
                model: main.roles
                Swatch {
                    required property var modelData
                    ui: pal
                    width: (grid.width - 24) / 3
                    label: modelData.label
                    hex: main.hexOf(modelData.key)
                    selected: editor.role === modelData.key
                    readonly property real ratio: modelData.against ? main.eng.contrast(hex, main.hexOf(modelData.against)) : 0
                    note: modelData.against ? (ratio >= 4.5 ? "leggibile ✓" : "poco leggibile ⚠") : ""
                    noteOk: ratio >= 4.5
                    onClicked: {
                        editor.label = modelData.label
                        editor.against = modelData.against ? main.hexOf(modelData.against) : (modelData.key === "glass" ? main.hexOf("text") : "")
                        editor.startHex = hex
                        editor.role = modelData.key
                    }
                }
            }
        }
        Btn {
            anchors.top: grid.bottom; anchors.topMargin: 16
            ui: pal
            text: "↺  Colori originali"
            onClicked: main.eng.resetColors()
        }
    }

    // ── barra in basso ─────────────────────────────────
    Rectangle {
        id: bottom
        anchors.bottom: parent.bottom
        width: parent.width
        height: 68
        color: "transparent"
        Rectangle { width: parent.width; height: 1; color: pal.line }
        Text {
            x: 22; anchors.verticalCenter: parent.verticalCenter
            width: parent.width - actions.width - 60
            elide: Text.ElideRight
            text: main.eng.error !== "" ? main.eng.error
                : main.eng.busy ? "Applico il tema…"
                : main.eng.dirty ? "Modifiche non ancora applicate"
                : "Il tema mostrato è quello in uso"
            color: main.eng.error !== "" ? pal.bad : pal.muted
            font.family: pal.font; font.pixelSize: 12
        }
        Row {
            id: actions
            anchors.right: parent.right; anchors.rightMargin: 22
            anchors.verticalCenter: parent.verticalCenter
            spacing: 10
            Btn { ui: pal; text: "Annulla modifiche"; enabledBtn: main.eng.dirty && !main.eng.busy; onClicked: main.eng.discard() }
            Btn { ui: pal; text: "Applica ✓"; primary: true; enabledBtn: main.eng.dirty && !main.eng.busy && !main.eng.awaitingKeep; onClicked: main.eng.apply() }
        }
    }

    // ── file modificati a mano ─────────────────────────
    Rectangle {
        visible: main.eng.conflicts.length > 0
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: bottom.top; anchors.bottomMargin: 12
        width: Math.min(parent.width - 44, cCol.implicitWidth + 40)
        height: cCol.implicitHeight + 28
        radius: 20
        color: pal.window
        border.width: 1.5; border.color: pal.bad
        Column {
            id: cCol
            x: 20; y: 14; spacing: 8
            Text { text: "Non ho applicato niente: questi file sono stati modificati a mano"; color: pal.bad; font.family: pal.font; font.pixelSize: 12; font.weight: Font.Bold }
            Repeater {
                model: main.eng.conflicts
                Row {
                    required property string modelData
                    spacing: 10
                    Text { anchors.verticalCenter: parent.verticalCenter; text: modelData.replace(main.eng.home, "~"); color: pal.fg; font.family: pal.font; font.pixelSize: 12 }
                    Btn { ui: pal; text: "Tieni le mie modifiche"; onClicked: main.eng.adoptAndRetry(parent.modelData) }
                }
            }
        }
    }

    Toast {
        ui: pal
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: bottom.verticalCenter
        active: main.eng.awaitingKeep
        onKeep: main.eng.keep()
        onRevert: main.eng.revert()
    }

    ColorEditor {
        id: editor
        ui: pal
        eng: main.eng
        onDone: (hex) => { main.eng.setColor(role, hex); role = "" }
        onCancel: role = ""
    }
}
