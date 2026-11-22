// Camenix · una schermata sola: anteprima, poi sfondo, tema e colori, in basso "Applica al desktop".
// Si adatta alla grandezza della finestra (anche affiancata alle altre). Tutti i testi vengono da i18n/<lingua>.json.
import QtQuick
import "color.js" as C

Rectangle {
    id: main
    property var eng
    property bool showLock: false
    property bool more: false               // "Altri colori" aperto
    property bool comparing: false          // "tieni premuto per vedere com'era"
    property bool matchPending: false       // nuovo sfondo scelto: appena ne leggo i colori, adatto il tema
    property var hoverZones: []             // zone dell'anteprima da illuminare
    property var wallColors: []             // colori principali dello sfondo
    readonly property bool wide: width >= 1280
    function tr(k, v) { return eng.tr(k, v) }

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

    // colori principali e "altri colori": chiave del tema, zone dell'anteprima, contrasto da controllare
    readonly property var mainColors: [
        { key: "glass", against: "text", zones: ["pills", "menu", "lock"] },
        { key: "text", against: "glass", zones: ["pills", "menu", "clock"] },
        { key: "accent", zones: ["pills", "menu", "lock"] },
        { key: "border", zones: ["border"] },
        { key: "terminal.background", name: "terminal", zones: ["term"] }
    ]
    readonly property var otherColors: [
        { key: "accent2", zones: ["menu"] },
        { key: "secondary", zones: ["menu"] },
        { key: "success", zones: [] },
        { key: "warning", zones: [] },
        { key: "error", zones: [] }
    ]
    readonly property var paletteKeys: ["glass", "text", "accent", "accent2", "secondary", "borderFrom", "borderTo"]
    function nameOf(key) { return key === "terminal.background" ? "terminal" : key }

    function hexIn(theme, key) {
        if (!theme) return "#000000"
        return key.indexOf("terminal.") === 0 ? theme.terminal[key.slice(9)] : theme.colors[key]
    }
    function hexOf(key) { return hexIn(eng.draft, key) }
    function pick(colors) {
        if (!colors) return null
        const o = {}
        for (const k of paletteKeys) o[k] = colors[k]
        return o
    }
    // temi da cliccare: quello attuale, due ricavati dallo sfondo, poi quelli pronti
    readonly property var themes: {
        const out = [], seen = {}
        function add(name, c) {
            if (!c) return
            const id = paletteKeys.map(k => c[k]).join()
            if (seen[id]) return
            seen[id] = true
            out.push({ name: name, c: c })
        }
        add(tr("theme.current"), pick(eng.current ? eng.current.colors : null))
        add(tr("theme.fromWallLight"), C.suggest(wallColors, false))
        add(tr("theme.fromWallDark"), C.suggest(wallColors, true))
        for (const p of eng.presets) add(p.name, pick(p.colors))
        return out
    }
    function isDraft(c) { return !!eng.draft && paletteKeys.every(k => eng.draft.colors[k] === c[k]) }
    readonly property int changes: {
        const c = eng.current, d = eng.draft
        if (!c || !d) return 0
        let n = 0
        const keys = paletteKeys.concat(["success", "warning", "error", "terminal.background"])
        for (const k of keys) if (hexIn(c, k) !== hexIn(d, k)) n++
        if (c.wallpaper.home !== d.wallpaper.home) n++
        if (c.wallpaper.lock_same !== d.wallpaper.lock_same || c.wallpaper.lock !== d.wallpaper.lock) n++
        return n
    }
    readonly property bool lockZonesOnly: hoverZones.length > 0 && hoverZones.every(z => z === "lock" || z === "clock")

    // nuovo sfondo: appena ne conosco i colori, il tema si adatta (chiaro o scuro come lo sfondo)
    onWallColorsChanged: {
        if (!matchPending || !wallColors.length) return
        matchPending = false
        const darkWall = C.lum(wallColors[0]) < 0.2
        const s = C.suggest(wallColors, darkWall)
        if (s) eng.setColors(s)
    }
    function chooseHome() { matchPending = eng.autoMatch; eng.chooseWallpaper("home") }

    function edit(key, against) {
        hoverZones = []
        editor.label = tr("color." + nameOf(key) + ".title")
        editor.desc = tr("color." + nameOf(key) + ".desc")
        editor.against = against ? hexOf(against) : ""
        editor.startHex = hexOf(key)
        editor.role = key
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
            Column {
                anchors.verticalCenter: parent.verticalCenter
                Text { text: "Camenix"; color: pal.fg; font.family: pal.font; font.pixelSize: 18; font.weight: Font.ExtraBold }
                Text { text: main.tr("app.tagline"); color: pal.muted; font.family: pal.font; font.pixelSize: 11 }
            }
        }
        Row {
            anchors.right: parent.right; anchors.rightMargin: 16
            anchors.verticalCenter: parent.verticalCenter
            spacing: 10
            Rectangle {                             // lingua dell'app
                objectName: "langBtn"
                anchors.verticalCenter: parent.verticalCenter
                width: 46; height: 30; radius: 15
                color: langArea.containsMouse ? pal.hover : pal.card
                border.width: 1.5; border.color: pal.line
                Text { anchors.centerIn: parent; text: main.tr("lang.toggle"); color: pal.fg; font.family: pal.font; font.pixelSize: 12; font.weight: Font.Bold }
                MouseArea { id: langArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: main.eng.setLang(main.eng.lang === "it" ? "en" : "it") }
            }
            Rectangle {                             // chiaro / scuro (solo l'app)
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
                width: 32; height: 32
                Rectangle { anchors.fill: parent; radius: 16; color: closeArea.containsMouse ? Qt.rgba(0.76, 0.22, 0.31, 0.14) : "transparent" }
                Text { anchors.centerIn: parent; text: "✕"; color: closeArea.containsMouse ? pal.bad : pal.muted; font.pixelSize: 15 }
                MouseArea { id: closeArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: Qt.quit() }
            }
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
            y: Math.max(0, (body.height - implicitHeight - 12) / 2)
            topPadding: main.wide ? 12 : 4

            // anteprima con le proporzioni del tuo schermo
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
                    theme: main.comparing && main.eng.current ? main.eng.current : main.eng.draft
                    highlight: main.hoverZones
                    lockInfo: main.eng.lockInfo
                    user: main.eng.user
                    emptyText: main.tr("preview.empty")
                    lock: main.showLock || main.lockZonesOnly
                    Rectangle {                         // effetto di "Applica": un'onda del nuovo accento
                        id: wave
                        z: 70
                        anchors.centerIn: parent
                        width: Math.hypot(parent.width, parent.height); height: width
                        radius: width / 2
                        color: main.hexOf("accent")
                        opacity: 0; scale: 0
                    }
                    Row {                               // scrivania | blocco schermo
                        anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.margins: 12
                        z: 95
                        spacing: 6
                        Repeater {
                            model: [{ t: "preview.desktop", lock: false }, { t: "preview.lock", lock: true }]
                            Rectangle {
                                required property var modelData
                                readonly property bool on: main.showLock === modelData.lock
                                width: tt.implicitWidth + 24; height: 28; radius: 14
                                color: on ? Qt.rgba(0.12, 0.08, 0.16, 0.85) : Qt.rgba(1, 1, 1, 0.85)
                                border.width: 1; border.color: Qt.rgba(0.12, 0.08, 0.16, 0.35)
                                Text { id: tt; anchors.centerIn: parent; text: main.tr(parent.modelData.t); color: parent.on ? "white" : "#1E1528"
                                       font.family: pal.font; font.pixelSize: 11; font.weight: Font.Bold }
                                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: main.showLock = parent.modelData.lock }
                            }
                        }
                    }
                    Rectangle {                         // tieni premuto: com'era prima
                        objectName: "compareBtn"
                        visible: main.eng.dirty
                        anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 12
                        anchors.topMargin: Math.round(54 * preview.k)          // sotto le barre dell'anteprima
                        z: 95
                        width: cmpText.implicitWidth + 28; height: 28; radius: 14
                        color: main.comparing ? Qt.rgba(0.12, 0.08, 0.16, 0.85) : Qt.rgba(1, 1, 1, 0.85)
                        border.width: 1; border.color: Qt.rgba(0.12, 0.08, 0.16, 0.35)
                        Text { id: cmpText; anchors.centerIn: parent; text: "◐  " + main.tr("preview.compare"); color: main.comparing ? "white" : "#1E1528"
                               font.family: pal.font; font.pixelSize: 11; font.weight: Font.Bold }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                    onPressed: main.comparing = true; onReleased: main.comparing = false; onCanceled: main.comparing = false }
                    }
                }
            }

            Column {
                id: controls
                width: main.wide ? 540 : content.width
                spacing: 20
                readonly property bool stacked: width < 600
                readonly property real inner: stacked ? width : width - 110

                component Label: Text {
                    width: controls.stacked ? controls.width : 110
                    color: pal.muted
                    font.family: pal.font; font.pixelSize: 12; font.weight: Font.Bold
                }
                component Check: Rectangle {            // casella con testo
                    id: chk
                    property bool on: false
                    property string label: ""
                    signal toggled()
                    width: chkRow.implicitWidth + 24; height: 38; radius: 19
                    color: chkArea.containsMouse ? pal.hover : "transparent"
                    border.width: 1.5; border.color: pal.line
                    Row {
                        id: chkRow
                        anchors.centerIn: parent
                        spacing: 8
                        Rectangle { width: 18; height: 18; radius: 5; anchors.verticalCenter: parent.verticalCenter
                                    color: chk.on ? pal.accent2 : "transparent"; border.width: 2; border.color: chk.on ? pal.accent2 : pal.muted
                                    Text { anchors.centerIn: parent; text: "✓"; visible: chk.on; color: "white"; font.pixelSize: 11; font.bold: true } }
                        Text { anchors.verticalCenter: parent.verticalCenter; text: chk.label; color: pal.fg; font.family: pal.font; font.pixelSize: 12 }
                    }
                    MouseArea { id: chkArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: chk.toggled() }
                }

                // Sfondo
                Grid {
                    columns: controls.stacked ? 1 : 2
                    rowSpacing: 8
                    Label { text: main.tr("wall.title"); topPadding: controls.stacked ? 0 : 30 }
                    Row {
                        spacing: 14
                        Rectangle {
                            width: 150; height: 86; radius: 12
                            color: pal.panel; border.width: 1; border.color: pal.line
                            anchors.verticalCenter: parent.verticalCenter
                            Canvas {                    // miniatura: da qui si leggono anche i colori dello sfondo
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
                                    ctx.globalCompositeOperation = "destination-in"
                                    ctx.beginPath(); ctx.roundedRect(0, 0, width, height, 11, 11); ctx.fill()
                                }
                            }
                            Text { anchors.centerIn: parent; visible: thumb.src === ""; text: main.tr("wall.none"); color: pal.muted; font.family: pal.font; font.pixelSize: 10 }
                        }
                        Column {
                            spacing: 8
                            Btn { objectName: "chooseWall"; ui: pal; primary: true; width: Math.max(implicitWidth, matchChk.width); text: main.tr("wall.choose"); onClicked: main.chooseHome() }
                            Check { id: matchChk; objectName: "matchChk"; on: main.eng.autoMatch; label: main.tr("wall.match"); onToggled: main.eng.setAutoMatch(!on) }
                            Check {
                                readonly property bool same: main.eng.draft ? main.eng.draft.wallpaper.lock_same : true
                                on: same; label: main.tr("wall.sameLock")
                                onToggled: { main.showLock = true; if (same) main.eng.chooseWallpaper("lock"); else main.eng.setLockSame(true) }
                            }
                        }
                    }
                }

                // Tema
                Grid {
                    columns: controls.stacked ? 1 : 2
                    rowSpacing: 8
                    Label { text: main.tr("theme.title"); topPadding: controls.stacked ? 0 : 16 }
                    Flow {
                        width: controls.inner
                        spacing: 8
                        Repeater {
                            model: main.themes
                            Rectangle {
                                id: chip
                                required property var modelData
                                required property int index
                                readonly property bool on: main.isDraft(modelData.c)
                                objectName: "theme-" + index
                                width: 124; height: 54; radius: 14
                                color: modelData.c.glass
                                border.width: on ? 3 : 1.5
                                border.color: on ? pal.accent2 : (chipArea.containsMouse ? pal.muted : pal.line)
                                Row {
                                    x: 10; y: 9
                                    spacing: 4
                                    Repeater {
                                        model: ["accent", "accent2", "secondary", "borderFrom", "borderTo"]
                                        Rectangle { required property string modelData; width: 15; height: 15; radius: 8
                                                    color: chip.modelData.c[modelData]; border.width: 1; border.color: Qt.rgba(0, 0, 0, 0.15) }
                                    }
                                }
                                Text { x: 10; anchors.bottom: parent.bottom; anchors.bottomMargin: 7; width: parent.width - 16; elide: Text.ElideRight
                                       text: chip.modelData.name; color: chip.modelData.c.text; font.family: pal.font; font.pixelSize: 10; font.weight: Font.Bold }
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
                    Label { text: main.tr("colors.title"); topPadding: controls.stacked ? 0 : 16 }
                    Column {
                        spacing: 6
                        Flow {
                            width: controls.inner
                            spacing: 4
                            Repeater {
                                model: main.mainColors
                                Item {
                                    id: cell
                                    required property var modelData
                                    readonly property bool isBorder: modelData.key === "border"
                                    width: isBorder ? 110 : 80; height: 96
                                    ColorCircle {
                                        visible: !cell.isBorder
                                        objectName: cell.isBorder ? "" : "color-" + cell.modelData.key
                                        ui: pal
                                        label: main.tr("color." + main.nameOf(cell.modelData.key))
                                        hex: cell.isBorder ? "#000000" : main.hexOf(cell.modelData.key)
                                        selected: editor.role === cell.modelData.key
                                        onHoveredChanged: main.hoverZones = hovered ? cell.modelData.zones : []
                                        onClicked: main.edit(cell.modelData.key, cell.modelData.against)
                                    }
                                    BorderCircle {
                                        visible: cell.isBorder
                                        objectName: cell.isBorder ? "color-border" : ""
                                        ui: pal
                                        label: main.tr("color.border")
                                        from: main.hexOf("borderFrom")
                                        to: main.hexOf("borderTo")
                                        selectedKey: editor.role
                                        onHoveredChanged: main.hoverZones = hovered ? ["border"] : []
                                        onPicked: (key) => main.edit(key, "")
                                    }
                                }
                            }
                        }
                        Text {
                            text: main.tr("colors.hint")
                            width: controls.inner; wrapMode: Text.WordWrap
                            color: pal.muted; font.family: pal.font; font.pixelSize: 10
                        }
                        Text {
                            text: (main.more ? "▾" : "▸") + "  " + main.tr("colors.more")
                            color: moreArea.containsMouse ? pal.accent2 : pal.muted
                            font.family: pal.font; font.pixelSize: 12; font.weight: Font.Bold
                            MouseArea { id: moreArea; anchors.fill: parent; anchors.margins: -6; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                        onClicked: main.more = !main.more }
                        }
                        Flow {
                            visible: main.more
                            width: controls.inner
                            spacing: 4
                            Repeater {
                                model: main.otherColors
                                ColorCircle {
                                    required property var modelData
                                    objectName: "color-" + modelData.key
                                    ui: pal
                                    label: main.tr("color." + modelData.key)
                                    hex: main.hexOf(modelData.key)
                                    selected: editor.role === modelData.key
                                    onHoveredChanged: main.hoverZones = hovered ? modelData.zones : []
                                    onClicked: main.edit(modelData.key, "")
                                }
                            }
                        }
                    }
                }

                // Si applica a
                Grid {
                    columns: controls.stacked ? 1 : 2
                    rowSpacing: 8
                    Label { text: main.tr("linked.title"); topPadding: controls.stacked ? 0 : 5 }
                    Flow {
                        width: controls.inner
                        spacing: 6
                        Repeater {
                            model: ["wallpaper"].concat(main.eng.managedKinds)
                            Rectangle {
                                required property string modelData
                                width: kt.implicitWidth + 20; height: 26; radius: 13
                                color: pal.panel; border.width: 1; border.color: pal.line
                                Text { id: kt; anchors.centerIn: parent; text: main.tr("kind." + parent.modelData); color: pal.fg; font.family: pal.font; font.pixelSize: 10 }
                            }
                        }
                    }
                }
            }
        }
    }

    // Applica: l'anteprima fa un piccolo "pop" e un'onda del nuovo accento la attraversa
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

    // ── barra in basso: cosa succede, e Applica ─────────
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
                objectName: "statusText"
                width: main.width - actions.width - 90
                elide: Text.ElideRight
                text: main.eng.error !== "" ? main.eng.error
                    : main.eng.busy ? main.tr("status.applying")
                    : main.eng.dirty ? (main.changes === 1 ? main.tr("status.pending.one") : main.tr("status.pending.many", { n: Math.max(1, main.changes) }))
                    : main.eng.justReverted ? main.tr("status.reverted")
                    : main.eng.lastApplied !== "" ? main.tr("status.applied", { time: main.eng.lastApplied })
                    : main.tr("status.start")
                color: main.eng.error !== "" ? pal.bad : pal.fg
                font.family: pal.font; font.pixelSize: 12
            }
        }
        Row {
            id: actions
            anchors.right: parent.right; anchors.rightMargin: 24
            anchors.verticalCenter: parent.verticalCenter
            spacing: 10
            Btn { ui: pal; visible: main.eng.dirty; text: main.tr("btn.discard"); enabledBtn: !main.eng.busy; onClicked: main.eng.discard() }
            Btn { objectName: "applyBtn"; ui: pal; text: main.tr("btn.apply"); primary: true
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
            Text { text: main.tr("conflict.title"); color: pal.bad; font.family: pal.font; font.pixelSize: 12; font.weight: Font.Bold }
            Repeater {
                model: main.eng.conflicts
                Row {
                    required property string modelData
                    spacing: 10
                    Text { anchors.verticalCenter: parent.verticalCenter; text: modelData.replace(main.eng.home, "~"); color: pal.fg; font.family: pal.font; font.pixelSize: 12 }
                    Btn { ui: pal; text: main.tr("conflict.keep"); onClicked: main.eng.adoptAndRetry(parent.modelData) }
                }
            }
        }
    }

    Toast {
        ui: pal
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: bottom.verticalCenter
        question: main.tr("toast.question")
        revertText: main.tr("toast.revert")
        keepText: main.tr("toast.keep")
        active: main.eng.awaitingKeep
        onKeep: main.eng.keep()
        onRevert: main.eng.revert()
    }

    Welcome { ui: pal; eng: main.eng; visible: main.eng.firstRun }

    ColorEditor {
        id: editor
        ui: pal
        eng: main.eng
        wallpaper: main.eng.draft && main.eng.draft.wallpaper.home ? main.eng.draft.wallpaper.home : ""
        onDone: (hex) => { main.eng.setColor(role, hex); role = "" }
        onCancel: role = ""
    }
}
