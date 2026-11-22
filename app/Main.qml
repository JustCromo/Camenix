// Camenix · una schermata sola: anteprima in alto, sotto sfondo, palette e colori, in basso Applica.
// Si adatta alla grandezza della finestra (anche affiancata alle altre).
import QtQuick
import "color.js" as C

Rectangle {
    id: main
    property var eng
    property bool showLock: false
    property bool more: false               // "Altri colori" aperto
    property var hoverZones: []             // zone dell'anteprima da illuminare
    property var wallColors: []             // colori principali dello sfondo (per le palette proposte)
    // finestra larga: anteprima a sinistra e comandi a destra; stretta: uno sotto l'altro
    readonly property bool wide: width >= 1280

    // colori dell'app: fissi (chiaro o scuro), non dipendono dal tema del desktop
    readonly property bool dark: eng.mode === "dark"
    QtObject {
        id: pal
        readonly property string font: "JetBrainsMono Nerd Font"
        readonly property color window: main.dark ? "#1F1729" : "#FBF8FF"
        readonly property color panel: main.dark ? "#271E33" : "#F3EFFD"
        readonly property color fg: main.dark ? "#FBF8FF" : "#1E1528"
        readonly property color muted: main.dark ? "#B4A9C9" : "#6F6585"
        readonly property color line: main.dark ? "#43375A" : "#DCD2F7"
        readonly property color card: main.dark ? "#2C2238" : "#FFFFFF"
        readonly property color hover: main.dark ? "#362A45" : "#FFF8E6"
        readonly property color button: main.dark ? "#2C2238" : "#FFFFFF"
        readonly property color input: main.dark ? "#2C2238" : "#FFFFFF"
        readonly property color accent: "#FFD25A"
        readonly property color accentHover: "#FFE08A"
        readonly property color accent2: "#E8892A"
        readonly property color accentInk: "#1E1528"
        readonly property color heading: main.dark ? "#B9A6F5" : "#8E78E0"
        readonly property color ok: main.dark ? "#7DE1A5" : "#2F7A4B"
        readonly property color bad: main.dark ? "#FF8FA0" : "#C2384F"
    }
    color: pal.window

    // i colori principali (sempre visibili) e gli altri (in "Altri colori")
    readonly property var mainColors: [
        { key: "glass", label: "Sfondo", against: "text", zones: ["pills", "menu", "lock"],
          title: "Sfondo di isole, menu e notifiche", desc: "Il fondo delle isole, dei menu e delle notifiche." },
        { key: "text", label: "Testo", against: "glass", zones: ["pills", "menu", "clock"],
          title: "Testo", desc: "Le scritte su isole, menu e notifiche, e l'orologio del blocco." },
        { key: "accent", label: "Accento", zones: ["pills", "menu", "lock"],
          title: "Accento", desc: "Il contorno delle isole, la voce scelta nei menu e il campo password del blocco." },
        { key: "borderFrom", label: "Bordo 1", zones: ["border"],
          title: "Bordo delle finestre · inizio", desc: "Il bordo della finestra attiva parte da questo colore…" },
        { key: "borderTo", label: "Bordo 2", zones: ["border"],
          title: "Bordo delle finestre · fine", desc: "…e sfuma fino a questo." },
        { key: "terminal.background", label: "Terminale", zones: ["term"],
          title: "Sfondo del terminale", desc: "Lo sfondo di kitty." }
    ]
    readonly property var otherColors: [
        { key: "accent2", label: "Risalto", zones: ["menu"], title: "Risalto", desc: "La riga sotto la voce scelta e i dettagli in risalto." },
        { key: "secondary", label: "Dettagli", zones: ["menu"], title: "Dettagli", desc: "Il contorno dei menu e le parti secondarie." },
        { key: "success", label: "Ok", zones: [], title: "Tutto ok", desc: "Conferme e stati positivi (es. batteria in carica)." },
        { key: "warning", label: "Avviso", zones: [], title: "Avviso", desc: "Cose da tenere d'occhio (es. batteria bassa)." },
        { key: "error", label: "Errore", zones: [], title: "Errore", desc: "Errori e notifiche urgenti." }
    ]
    readonly property var paletteKeys: ["glass", "text", "accent", "accent2", "secondary", "borderFrom", "borderTo"]

    function hexIn(theme, key) {
        if (!theme) return "#000000"
        return key.indexOf("terminal.") === 0 ? theme.terminal[key.slice(9)] : theme.colors[key]
    }
    function hexOf(key) { return hexIn(eng.draft, key) }
    function pick(theme) {                              // i colori di una palette presi da un tema
        if (!theme) return null
        const o = {}
        for (const k of paletteKeys) o[k] = theme.colors[k]
        return o
    }
    // palette da cliccare: quella in uso, quella iniziale, e due ricavate dallo sfondo
    readonly property var palettes: {
        const out = [], seen = {}
        function add(name, c) {
            if (!c) return
            const id = paletteKeys.map(k => c[k]).join()
            if (seen[id]) return
            seen[id] = true
            out.push({ name: name, c: c })
        }
        add("In uso", pick(eng.current))
        add("Sfondo chiaro", C.suggest(wallColors, false))
        add("Sfondo scuro", C.suggest(wallColors, true))
        return out
    }
    function isDraft(c) { return !!eng.draft && paletteKeys.every(k => eng.draft.colors[k] === c[k]) }
    readonly property int changes: {
        const c = eng.current, d = eng.draft
        if (!c || !d) return 0
        let n = 0
        for (const it of mainColors.concat(otherColors)) if (hexIn(c, it.key) !== hexIn(d, it.key)) n++
        if (c.wallpaper.home !== d.wallpaper.home) n++
        if (c.wallpaper.lock_same !== d.wallpaper.lock_same || c.wallpaper.lock !== d.wallpaper.lock) n++
        return n
    }
    readonly property bool lockZonesOnly: hoverZones.length > 0 && hoverZones.every(z => z === "lock" || z === "clock")

    function edit(it) {
        hoverZones = []
        editor.label = it.title
        editor.desc = it.desc
        editor.against = it.against ? hexOf(it.against) : ""
        editor.startHex = hexOf(it.key)
        editor.role = it.key
    }

    focus: true
    Keys.onEscapePressed: if (editor.role !== "") editor.role = ""; else Qt.quit()

    // ── intestazione ───────────────────────────────────
    Item {
        id: header
        width: parent.width; height: 60
        Row {
            x: 24; anchors.verticalCenter: parent.verticalCenter
            spacing: 10
            Image { width: 34; height: 34; source: Qt.resolvedUrl("assets/camenix.svg"); sourceSize.width: 68; sourceSize.height: 68 }
            Text { anchors.verticalCenter: parent.verticalCenter; text: "Camenix"; color: pal.fg; font.family: pal.font; font.pixelSize: 18; font.weight: Font.ExtraBold }
        }
        Rectangle {                                 // chiaro / scuro (solo l'app)
            anchors.right: closeBtn.left; anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            width: 64; height: 30; radius: 15
            color: pal.card
            border.width: 1.5; border.color: pal.line
            Rectangle {
                width: 26; height: 24; radius: 12; y: 3
                x: main.dark ? parent.width - width - 3 : 3
                color: pal.accent
                Behavior on x { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
            }
            Text { x: 9; anchors.verticalCenter: parent.verticalCenter; text: "☀"; color: main.dark ? pal.fg : pal.accentInk; font.pixelSize: 13 }
            Text { anchors.right: parent.right; anchors.rightMargin: 9; anchors.verticalCenter: parent.verticalCenter; text: "☾"; color: main.dark ? pal.accentInk : pal.fg; font.pixelSize: 13 }
            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: main.eng.setMode(main.dark ? "light" : "dark") }
        }
        Item {
            id: closeBtn
            anchors.right: parent.right; anchors.rightMargin: 16
            anchors.verticalCenter: parent.verticalCenter
            width: 32; height: 32
            Rectangle { anchors.fill: parent; radius: 16; color: closeArea.containsMouse ? Qt.rgba(0.76, 0.22, 0.31, 0.14) : "transparent" }
            Text { anchors.centerIn: parent; text: "✕"; color: closeArea.containsMouse ? pal.bad : pal.muted; font.pixelSize: 15 }
            MouseArea { id: closeArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: Qt.quit() }
        }
    }

    // ── contenuto (scorre se la finestra è bassa) ───────
    Flickable {
        id: body
        anchors.top: header.bottom
        anchors.bottom: bottom.top
        width: parent.width
        contentHeight: content.implicitHeight + 24
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        Grid {
            id: content
            columns: main.wide ? 2 : 1
            columnSpacing: 32
            rowSpacing: 18
            width: Math.min(body.width - 48, main.wide ? 1760 : 1080)
            x: (body.width - width) / 2
            y: Math.max(0, (body.height - implicitHeight - 12) / 2)    // avanza spazio in altezza: tutto al centro
            topPadding: main.wide ? 12 : 4

            // anteprima con le proporzioni del tuo schermo: da larga prende lo spazio a sinistra,
            // da stretta non spinge fuori i comandi; se avanza spazio resta centrata
            Item {
                id: previewBox
                readonly property real aspect: main.eng.lockInfo && main.eng.lockInfo.screen ? main.eng.lockInfo.screen[0] / main.eng.lockInfo.screen[1] : 16 / 9
                readonly property real maxW: main.wide ? content.width - controls.width - content.columnSpacing : content.width
                readonly property real maxH: main.wide ? body.height - 36 : body.height - controls.implicitHeight - 46
                width: maxW
                height: preview.height
            Preview {
                id: preview
                ui: pal
                anchors.horizontalCenter: parent.horizontalCenter
                width: Math.max(320, Math.min(previewBox.maxW, Math.max(200, previewBox.maxH) * previewBox.aspect))
                height: width / previewBox.aspect
                theme: main.eng.draft
                highlight: main.hoverZones
                lockInfo: main.eng.lockInfo
                user: main.eng.user
                lock: main.showLock || main.lockZonesOnly
                Rectangle {                             // effetto di "Applica": un'onda del nuovo accento
                    id: wave
                    z: 70
                    anchors.centerIn: parent
                    width: Math.hypot(parent.width, parent.height); height: width
                    radius: width / 2
                    color: main.hexOf("accent")
                    opacity: 0; scale: 0
                }                Row {                                   // scrivania | blocco schermo
                    anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.margins: 12
                    z: 60
                    spacing: 6
                    Repeater {
                        model: [{ t: "Scrivania", lock: false }, { t: "Blocco schermo", lock: true }]
                        Rectangle {
                            required property var modelData
                            readonly property bool on: main.showLock === modelData.lock
                            width: tt.implicitWidth + 24; height: 28; radius: 14
                            color: on ? Qt.rgba(0.12, 0.08, 0.16, 0.85) : Qt.rgba(1, 1, 1, 0.85)
                            border.width: 1; border.color: Qt.rgba(0.12, 0.08, 0.16, 0.35)
                            Text { id: tt; anchors.centerIn: parent; text: parent.modelData.t; color: parent.on ? "white" : "#1E1528"
                                   font.family: pal.font; font.pixelSize: 11; font.weight: Font.Bold }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: main.showLock = parent.modelData.lock }
                        }
                    }
                }
            }
            }

            Column {
                id: controls
                width: main.wide ? 540 : content.width
                spacing: 18
                readonly property bool stacked: width < 600          // poco spazio: titoletti sopra, non a sinistra
                readonly property real inner: stacked ? width : width - 110

                component Label: Text {
                    width: controls.stacked ? controls.width : 110
                    color: pal.muted
                    font.family: pal.font; font.pixelSize: 12; font.weight: Font.Bold
                }

                // Sfondo
                Grid {
                    columns: controls.stacked ? 1 : 2
                    rowSpacing: 8
                    verticalItemAlignment: Grid.AlignVCenter
                    Label { text: "Sfondo" }
                    Row {
                        spacing: 14
                        Rectangle {
                            width: 150; height: 86; radius: 12; clip: true
                            color: pal.panel; border.width: 1; border.color: pal.line
                            Canvas {                    // miniatura: da qui si leggono anche i colori per le palette
                                id: thumb
                                anchors.fill: parent; anchors.margins: 1
                                property string src: main.eng.draft && main.eng.draft.wallpaper.home ? "file://" + main.eng.draft.wallpaper.home : ""
                                onSrcChanged: { main.wallColors = []; if (src !== "") { if (isImageLoaded(src)) requestPaint(); else loadImage(src) } else requestPaint() }
                                onImageLoaded: requestPaint()
                                onPaint: {
                                    const ctx = getContext("2d")
                                    ctx.reset()
                                    if (src === "" || !isImageLoaded(src)) return
                                    ctx.drawImage(src, 0, 0, width, height)
                                    try { main.wallColors = C.palette(ctx.getImageData(0, 0, width, height).data, 8) } catch (e) { main.wallColors = [] }
                                }
                            }
                            Text { anchors.centerIn: parent; visible: thumb.src === ""; text: "nessuno"; color: pal.muted; font.family: pal.font; font.pixelSize: 10 }
                        }
                        Column {                        // a destra della miniatura: cambia sfondo, e sotto il blocco
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 10
                            Btn { ui: pal; width: sameLock.width; text: "Cambia sfondo…"; onClicked: main.eng.chooseWallpaper("home") }
                            Rectangle {                 // blocco: stesso sfondo sì/no
                                id: sameLock
                                readonly property bool on: main.eng.draft ? main.eng.draft.wallpaper.lock_same : true
                                width: sameRow.implicitWidth + 24; height: 38; radius: 19
                                color: sameArea.containsMouse ? pal.hover : "transparent"
                                border.width: 1.5; border.color: pal.line
                                Row {
                                    id: sameRow
                                    anchors.centerIn: parent
                                    spacing: 8
                                    Rectangle { width: 18; height: 18; radius: 5; anchors.verticalCenter: parent.verticalCenter
                                                color: sameLock.on ? pal.accent2 : "transparent"; border.width: 2; border.color: sameLock.on ? pal.accent2 : pal.muted
                                                Text { anchors.centerIn: parent; text: "✓"; visible: sameLock.on; color: "white"; font.pixelSize: 11; font.bold: true } }
                                    Text { anchors.verticalCenter: parent.verticalCenter; text: "Stesso sfondo nel blocco schermo"; color: pal.fg; font.family: pal.font; font.pixelSize: 12 }
                                }
                                MouseArea { id: sameArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                            onClicked: { main.showLock = true; if (sameLock.on) main.eng.chooseWallpaper("lock"); else main.eng.setLockSame(true) } }
                            }
                        }
                    }
                }

                // Palette
                Grid {
                    columns: controls.stacked ? 1 : 2
                    rowSpacing: 8
                    verticalItemAlignment: Grid.AlignVCenter
                    Label { text: "Palette" }
                    Flow {
                        width: controls.inner
                        spacing: 10
                        Repeater {
                            model: main.palettes
                            Rectangle {
                                id: chip
                                required property var modelData
                                readonly property bool on: main.isDraft(modelData.c)
                                objectName: "palette-" + modelData.name
                                width: 150; height: 58; radius: 16
                                color: modelData.c.glass
                                border.width: on ? 3 : 1.5
                                border.color: on ? pal.accent2 : (chipArea.containsMouse ? pal.muted : pal.line)
                                Row {
                                    x: 12; y: 10
                                    spacing: 5
                                    Repeater {
                                        model: ["accent", "accent2", "secondary", "borderFrom", "borderTo"]
                                        Rectangle { required property string modelData; width: 18; height: 18; radius: 9
                                                    color: chip.modelData.c[modelData]; border.width: 1; border.color: Qt.rgba(0, 0, 0, 0.15) }
                                    }
                                }
                                Text { x: 12; anchors.bottom: parent.bottom; anchors.bottomMargin: 8
                                       text: chip.modelData.name; color: chip.modelData.c.text; font.family: pal.font; font.pixelSize: 11; font.weight: Font.Bold }
                                MouseArea { id: chipArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                            onClicked: main.eng.setColors(chip.modelData.c) }
                            }
                        }
                    }
                }

                // Colori
                Grid {
                    columns: controls.stacked ? 1 : 2
                    rowSpacing: 8
                    Label { text: "Colori"; topPadding: controls.stacked ? 0 : 16 }
                    Column {
                        spacing: 4
                        Flow {
                            width: controls.inner
                            spacing: 6
                            Repeater {
                                model: main.mainColors
                                ColorCircle {
                                    required property var modelData
                                    objectName: "color-" + modelData.key
                                    ui: pal
                                    label: modelData.label
                                    hex: main.hexOf(modelData.key)
                                    selected: editor.role === modelData.key
                                    onHoveredChanged: main.hoverZones = hovered ? modelData.zones : []
                                    onClicked: main.edit(modelData)
                                }
                            }
                        }
                        Text {
                            id: moreBtn
                            text: (main.more ? "▾" : "▸") + "  Altri colori"
                            color: moreArea.containsMouse ? pal.accent2 : pal.muted
                            font.family: pal.font; font.pixelSize: 12; font.weight: Font.Bold
                            MouseArea { id: moreArea; anchors.fill: parent; anchors.margins: -6; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                        onClicked: main.more = !main.more }
                        }
                        Flow {
                            visible: main.more
                            width: controls.inner
                            spacing: 6
                            Repeater {
                                model: main.otherColors
                                ColorCircle {
                                    required property var modelData
                                    objectName: "color-" + modelData.key
                                    ui: pal
                                    label: modelData.label
                                    hex: main.hexOf(modelData.key)
                                    selected: editor.role === modelData.key
                                    onHoveredChanged: main.hoverZones = hovered ? modelData.zones : []
                                    onClicked: main.edit(modelData)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Applica: l'anteprima fa un piccolo "pop" (come le finestre) e un'onda del nuovo accento la attraversa
    ParallelAnimation {
        id: applyFx
        NumberAnimation { target: wave; property: "scale"; from: 0; to: 1; duration: 700; easing.type: Easing.OutCubic }
        NumberAnimation { target: wave; property: "opacity"; from: 0.5; to: 0; duration: 700; easing.type: Easing.OutQuad }
        SequentialAnimation {
            NumberAnimation { target: preview; property: "scale"; to: 0.97; duration: 120; easing.type: Easing.OutQuad }
            NumberAnimation { target: preview; property: "scale"; to: 1; duration: 450; easing.type: Easing.OutBack }
        }
    }
    Connections { target: main.eng; function onApplied() { applyFx.restart() } }

    // ── barra in basso: stato e Applica ─────────────────
    Rectangle {
        id: bottom
        anchors.bottom: parent.bottom
        width: parent.width
        height: 68
        color: pal.panel
        Rectangle { width: parent.width; height: 1; color: pal.line }
        Row {
            x: 24; anchors.verticalCenter: parent.verticalCenter
            spacing: 8
            Rectangle { width: 9; height: 9; radius: 5; anchors.verticalCenter: parent.verticalCenter
                        color: main.eng.error !== "" ? pal.bad : main.eng.dirty ? pal.accent2 : pal.ok }
            Text {
                width: main.width - actions.width - 90
                elide: Text.ElideRight
                text: main.eng.error !== "" ? main.eng.error
                    : main.eng.busy ? "Un momento…"
                    : main.eng.dirty ? "Anteprima modificata: premi Applica per portarla sul desktop"
                    : "Il desktop è uguale all'anteprima"
                color: main.eng.error !== "" ? pal.bad : pal.fg
                font.family: pal.font; font.pixelSize: 12
            }
        }
        Row {
            id: actions
            anchors.right: parent.right; anchors.rightMargin: 24
            anchors.verticalCenter: parent.verticalCenter
            spacing: 10
            Btn { ui: pal; visible: main.eng.dirty; text: "Annulla"; enabledBtn: !main.eng.busy; onClicked: main.eng.discard() }
            Btn { ui: pal; text: "Applica ✓"; primary: true
                  enabledBtn: main.eng.dirty && !main.eng.busy && !main.eng.awaitingKeep; onClicked: main.eng.apply() }
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

    Welcome { ui: pal; eng: main.eng; kindNames: ({ hyprland: "Bordi delle finestre (Hyprland)", kitty: "Terminale (kitty)",
                                                    mako: "Notifiche (mako)", rofi: "Menu (rofi)", hyprlock: "Blocco schermo (hyprlock)",
                                                    quickshell: "Isole (Quickshell)", other: "Altre config" })
              visible: main.eng.firstRun }

    ColorEditor {
        id: editor
        ui: pal
        eng: main.eng
        wallpaper: main.eng.draft && main.eng.draft.wallpaper.home ? main.eng.draft.wallpaper.home : ""
        onDone: (hex) => { main.eng.setColor(role, hex); role = "" }
        onCancel: role = ""
    }
}
