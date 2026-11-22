// scelta di un colore: quadrato saturazione/luminosità dentro l'anello delle tinte, cursori R G B,
// #hex, colori presi dal tuo sfondo e dal tema, prima/dopo e controllo di leggibilità
import QtQuick
import "color.js" as C

Item {
    id: ed
    property var ui
    property var eng
    property string role: ""
    property string label: ""
    property string desc: ""                 // dove si vede questo colore
    property string startHex: "#000000"
    property string against: ""              // colore con cui controllare la leggibilità
    property string wallpaper: ""            // sfondo da cui proporre i colori
    property string hex: "#000000"
    property real hue: 0                     // 0..360
    property real sat: 0                     // 0..1
    property real val: 0                     // 0..1
    property var wallColors: []
    readonly property bool valid: C.normHex(hex) !== ""
    readonly property bool fieldOk: C.normHex(field.text) !== ""     // il campo contiene un #hex completo
    readonly property var rgb: C.hexToRgb(hex) || ({ r: 0, g: 0, b: 0 })
    signal done(string hex)
    signal cancel()
    anchors.fill: parent
    visible: role !== ""

    // tre modi di arrivare allo stesso colore: tutti aggiornano tinta/saturazione/luminosità e #hex
    function fromHex(h, keepField) {
        const n = C.normHex(h)
        if (!n) return
        const c = C.hexToRgb(n), v = C.rgbToHsv(c.r, c.g, c.b)
        if (v.s > 0 && v.v > 0) hue = v.h            // i grigi non hanno tinta: si tiene quella di prima
        sat = v.s; val = v.v; hex = n
        if (!keepField) field.text = n
    }
    function fromHsv(h, s, v) { hue = h; sat = s; val = v; hex = C.hsvToHex(h, s, v); field.text = hex }
    function fromRgb(r, g, b) { fromHex(C.rgbToHex(r, g, b)) }
    onStartHexChanged: fromHex(startHex)
    onRoleChanged: if (role !== "") fromHex(startHex)

    Rectangle { anchors.fill: parent; color: Qt.rgba(0.12, 0.08, 0.16, 0.45)
        MouseArea { anchors.fill: parent; onClicked: ed.cancel() } }

    Rectangle {
        id: card
        anchors.centerIn: parent
        width: 660; height: col.implicitHeight + 40
        radius: 26
        color: ui.window
        border.width: 1.5
        border.color: ui.line
        MouseArea { anchors.fill: parent }           // i clic sulla scheda non la chiudono
        Column {
            id: col
            x: 24; y: 20
            width: parent.width - 48
            spacing: 16
            Row {
                spacing: 12
                Rectangle { width: 30; height: 30; radius: 9; color: ed.startHex; border.width: 1; border.color: ui.line; anchors.verticalCenter: parent.verticalCenter }
                Column {
                    spacing: 2
                    Text { text: ed.label; color: ui.fg; font.family: ui.font; font.pixelSize: 16; font.weight: Font.ExtraBold }
                    Text { width: col.width - 44; text: ed.desc; visible: ed.desc !== ""; wrapMode: Text.WordWrap; color: ui.muted; font.family: ui.font; font.pixelSize: 11 }
                }
            }
            Row {
                spacing: 26
                // ── sinistra: anello + quadrato, colori del tema ──
                Column {
                    spacing: 10
                    Item {
                        id: pk
                        objectName: "picker"
                        width: 260; height: 260
                        readonly property real ro: width / 2
                        readonly property real ri: ro - 22
                        readonly property real sq: Math.floor((ri - 8) * Math.SQRT2)
                        Canvas {
                            anchors.fill: parent
                            onPaint: {
                                const ctx = getContext("2d")
                                ctx.reset()
                                const c = width / 2, r = (pk.ro + pk.ri) / 2
                                ctx.lineWidth = pk.ro - pk.ri
                                for (let i = 0; i < 360; i += 2) {
                                    ctx.beginPath()
                                    ctx.strokeStyle = C.hsvToHex(i, 1, 1)
                                    ctx.arc(c, c, r, (i - 1.5) * Math.PI / 180, (i + 1.5) * Math.PI / 180, false)
                                    ctx.stroke()
                                }
                            }
                        }
                        Rectangle {                          // pallino sulla tinta
                            readonly property real r: (pk.ro + pk.ri) / 2
                            width: 22; height: 22; radius: 11
                            x: pk.ro + r * Math.cos(ed.hue * Math.PI / 180) - 11
                            y: pk.ro + r * Math.sin(ed.hue * Math.PI / 180) - 11
                            color: C.hsvToHex(ed.hue, 1, 1)
                            border.width: 3; border.color: "white"
                        }
                        Rectangle {                          // saturazione (→) e luminosità (↓)
                            id: sqr
                            objectName: "svSquare"
                            anchors.centerIn: parent
                            width: pk.sq; height: pk.sq
                            radius: 6
                            gradient: Gradient { orientation: Gradient.Horizontal
                                GradientStop { position: 0; color: "#FFFFFF" }
                                GradientStop { position: 1; color: C.hsvToHex(ed.hue, 1, 1) } }
                            Rectangle { anchors.fill: parent; radius: 6
                                gradient: Gradient {
                                    GradientStop { position: 0; color: "#00000000" }
                                    GradientStop { position: 1; color: "#FF000000" } } }
                            Rectangle {
                                width: 18; height: 18; radius: 9
                                x: ed.sat * parent.width - 9; y: (1 - ed.val) * parent.height - 9
                                color: ed.hex
                                border.width: 3; border.color: "white"
                                Rectangle { anchors.fill: parent; anchors.margins: -1; radius: 10; color: "transparent"; border.width: 1; border.color: "#55000000" }
                            }
                        }
                        MouseArea {
                            anchors.fill: parent
                            preventStealing: true
                            cursorShape: Qt.CrossCursor
                            property string mode: ""
                            function handle(mx, my, start) {
                                const dx = mx - pk.ro, dy = my - pk.ro, d = Math.hypot(dx, dy)
                                if (start) {
                                    if (d >= pk.ri - 6 && d <= pk.ro + 4) mode = "hue"
                                    else if (mx >= sqr.x - 8 && mx <= sqr.x + sqr.width + 8 && my >= sqr.y - 8 && my <= sqr.y + sqr.height + 8) mode = "sv"
                                    else mode = ""
                                }
                                if (mode === "hue") {
                                    let a = Math.atan2(dy, dx) * 180 / Math.PI
                                    if (a < 0) a += 360
                                    ed.fromHsv(a, ed.sat, ed.val)
                                } else if (mode === "sv") {
                                    ed.fromHsv(ed.hue, C.clamp((mx - sqr.x) / sqr.width, 0, 1), 1 - C.clamp((my - sqr.y) / sqr.height, 0, 1))
                                }
                            }
                            onPressed: (m) => handle(m.x, m.y, true)
                            onPositionChanged: (m) => { if (pressed) handle(m.x, m.y, false) }
                        }
                    }
                    Text { text: ed.eng ? ed.eng.tr("editor.themeColors") : ""; color: ui.muted; font.family: ui.font; font.pixelSize: 11 }
                    Flow {
                        width: pk.width
                        spacing: 7
                        Repeater {
                            model: ed.eng && ed.eng.draft ? ["glass", "text", "accent", "accent2", "secondary", "borderFrom", "borderTo",
                                                    "success", "warning", "error", "secondaryDeep", "paper"].map(k => ed.eng.draft.colors[k]) : []
                            ColorDot { required property string modelData; ui: ed.ui; c: modelData; chosen: ed.hex === modelData; onPicked: (h) => ed.fromHex(h) }
                        }
                    }
                }
                // ── destra: prima/dopo, R G B, #hex, colori dello sfondo ──
                Column {
                    width: col.width - 260 - 26
                    spacing: 14
                    Row {
                        spacing: 10
                        Rectangle { width: (parent.parent.width - 10) / 2; height: 64; radius: 14; color: ed.startHex; border.width: 1; border.color: ui.line
                            Text { anchors.centerIn: parent; text: ed.eng ? ed.eng.tr("editor.before") : ""; color: ed.eng && ed.eng.contrast(ed.startHex, "#FFFFFF") > 3 ? "white" : "#1E1528"; font.family: ui.font; font.pixelSize: 11 } }
                        Rectangle { width: (parent.parent.width - 10) / 2; height: 64; radius: 14; color: ed.valid ? ed.hex : ed.startHex; border.width: 2; border.color: ui.accent2
                            Text { anchors.centerIn: parent; text: ed.eng ? ed.eng.tr("editor.after") : ""; color: ed.eng && ed.eng.contrast(ed.valid ? ed.hex : ed.startHex, "#FFFFFF") > 3 ? "white" : "#1E1528"; font.family: ui.font; font.pixelSize: 11 } }
                    }
                    ColorChannel { objectName: "chanR"; ui: ed.ui; current: ed.hex; width: parent.width; name: "R"; value: ed.rgb.r; from: C.rgbToHex(0, ed.rgb.g, ed.rgb.b); to: C.rgbToHex(255, ed.rgb.g, ed.rgb.b); onMoved: (v) => ed.fromRgb(v, ed.rgb.g, ed.rgb.b) }
                    ColorChannel { ui: ed.ui; current: ed.hex; width: parent.width; name: "G"; value: ed.rgb.g; from: C.rgbToHex(ed.rgb.r, 0, ed.rgb.b); to: C.rgbToHex(ed.rgb.r, 255, ed.rgb.b); onMoved: (v) => ed.fromRgb(ed.rgb.r, v, ed.rgb.b) }
                    ColorChannel { ui: ed.ui; current: ed.hex; width: parent.width; name: "B"; value: ed.rgb.b; from: C.rgbToHex(ed.rgb.r, ed.rgb.g, 0); to: C.rgbToHex(ed.rgb.r, ed.rgb.g, 255); onMoved: (v) => ed.fromRgb(ed.rgb.r, ed.rgb.g, v) }
                    Row {
                        spacing: 10
                        Rectangle {
                            width: 130; height: 36; radius: 18
                            color: ui.input
                            border.width: 1.5
                            border.color: ed.fieldOk ? ui.line : ui.bad
                            TextInput {
                                id: field
                                objectName: "hexField"
                                anchors.fill: parent; anchors.leftMargin: 14; anchors.rightMargin: 14
                                verticalAlignment: TextInput.AlignVCenter
                                maximumLength: 7
                                color: ui.fg
                                font.family: ui.font; font.pixelSize: 14; font.weight: Font.Bold
                                selectByMouse: true
                                validator: RegularExpressionValidator { regularExpression: /#?[0-9A-Fa-f]{0,6}/ }
                                onTextEdited: ed.fromHex(text, true)
                                // Invio conferma solo un #hex completo (con "12" non riusa il colore di prima)
                                onAccepted: if (ed.fieldOk) ed.done(C.normHex(text))
                            }
                        }
                        Rectangle {
                            visible: ed.against !== "" && ed.valid
                            readonly property real ratio: ed.eng ? ed.eng.contrast(ed.hex, ed.against) : 1
                            anchors.verticalCenter: parent.verticalCenter
                            width: cl.implicitWidth + 20; height: 26; radius: 13
                            color: "transparent"
                            border.width: 1
                            border.color: ratio >= 4.5 ? ui.ok : ui.bad
                            Text { id: cl; anchors.centerIn: parent; color: parent.ratio >= 4.5 ? ui.ok : ui.bad; font.family: ui.font; font.pixelSize: 11; font.weight: Font.Bold
                                   text: (ed.eng ? ed.eng.tr(parent.ratio >= 4.5 ? "editor.readable" : "editor.unreadable") : "") + " " + parent.ratio.toFixed(1) + ":1" }
                        }
                    }
                    Text { visible: ed.wallpaper !== ""; text: ed.eng ? ed.eng.tr("editor.fromWall") : ""; color: ui.muted; font.family: ui.font; font.pixelSize: 11 }
                    Row {
                        visible: ed.wallpaper !== ""
                        spacing: 10
                        Canvas {                             // miniatura dello sfondo: da qui si leggono i colori
                            id: thumb
                            width: 64; height: 40
                            property string src: ed.wallpaper !== "" ? "file://" + ed.wallpaper : ""
                            onSrcChanged: { ed.wallColors = []; if (src !== "") { if (isImageLoaded(src)) requestPaint(); else loadImage(src) } }
                            Component.onCompleted: if (src !== "") loadImage(src)
                            onImageLoaded: requestPaint()
                            onPaint: {
                                const ctx = getContext("2d")
                                ctx.reset()
                                if (src === "" || !isImageLoaded(src)) return
                                ctx.drawImage(src, 0, 0, width, height)
                                try { ed.wallColors = C.palette(ctx.getImageData(0, 0, width, height).data, 8) }
                                catch (e) { ed.wallColors = [] }
                            }
                        }
                        Flow {
                            width: parent.parent.width - 74
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 7
                            Repeater { model: ed.wallColors; ColorDot { required property string modelData; ui: ed.ui; c: modelData; chosen: ed.hex === modelData; onPicked: (h) => ed.fromHex(h) } }
                        }
                    }
                }
            }
            Row {
                anchors.right: parent.right
                spacing: 8
                Btn { ui: ed.ui; text: ed.eng ? ed.eng.tr("editor.cancel") : ""; onClicked: ed.cancel() }
                Btn { objectName: "useColor"; ui: ed.ui; text: ed.eng ? ed.eng.tr("editor.use") : ""; primary: true; enabledBtn: ed.valid && ed.fieldOk; onClicked: if (ed.valid && ed.fieldOk) ed.done(ed.hex) }
            }
        }
    }
}
