// Camenix · finestra principale in tre passi: ① Sfondo ② Colori ③ Applica
// A sinistra l'anteprima (scrivania o blocco), a destra il passo attuale, in basso avanti/indietro.
import QtQuick

Rectangle {
    id: main
    property var eng
    property int step: 1
    property bool showLock: false
    property var hoverZones: []             // zone dell'anteprima da illuminare

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

    // colori raggruppati per zona del desktop: nome concreto, dove si vede, cosa illuminare nell'anteprima
    readonly property var sections: [
        { title: "Isole e menu", icon: "islands", hint: "barre, menu, notifiche", items: [
            { key: "glass", label: "Sfondo", against: "text", zones: ["pills", "menu", "lock"],
              desc: "Lo sfondo delle isole, dei menu e delle notifiche." },
            { key: "text", label: "Testo", against: "glass", zones: ["pills", "menu", "clock"],
              desc: "Le scritte su isole, menu e notifiche, e l'orologio del blocco." },
            { key: "accent", label: "Evidenziato", zones: ["pills", "menu", "lock"],
              desc: "Il contorno delle isole, la voce scelta nei menu e il campo password del blocco." },
            { key: "accent2", label: "Risalto", zones: ["menu"],
              desc: "La riga sotto la voce scelta e i dettagli in risalto (pulsanti attivi, avanzamento)." },
            { key: "secondary", label: "Dettagli", zones: ["menu"],
              desc: "Il contorno dei menu e le parti secondarie (con le sue sfumature chiare e scure)." } ] },
        { title: "Bordi delle finestre", icon: "borders", hint: "sfumano dall'inizio alla fine", items: [
            { key: "borderFrom", label: "Inizio", zones: ["border"], desc: "Il bordo della finestra attiva parte da questo colore…" },
            { key: "borderTo", label: "Fine", zones: ["border"], desc: "…e sfuma fino a questo." } ] },
        { title: "Terminale", icon: "terminal", hint: "kitty", items: [
            { key: "terminal.background", label: "Sfondo", zones: ["term"], desc: "Lo sfondo di kitty." } ] },
        { title: "Avvisi", icon: "alerts", hint: "notifiche e stati", items: [
            { key: "success", label: "Tutto ok", zones: [], desc: "Conferme e stati positivi (es. batteria in carica)." },
            { key: "warning", label: "Attenzione", zones: [], desc: "Avvisi da tenere d'occhio (es. batteria bassa)." },
            { key: "error", label: "Errore", zones: [], desc: "Errori e notifiche urgenti." } ] }
    ]
    readonly property var kindNames: ({ hyprland: "Bordi delle finestre (Hyprland)", kitty: "Terminale (kitty)",
                                        mako: "Notifiche (mako)", rofi: "Menu (rofi)", hyprlock: "Blocco schermo (hyprlock)",
                                        quickshell: "Isole (Quickshell)", other: "Altre config" })
    function hexIn(theme, key) {
        if (!theme) return "#000000"
        return key.indexOf("terminal.") === 0 ? theme.terminal[key.slice(9)] : theme.colors[key]
    }
    function hexOf(key) { return hexIn(eng.draft, key) }
    function fileName(p) { return p ? p.split("/").pop() : "" }

    // cosa cambierà premendo Applica (per il passo ③)
    readonly property var changes: {
        const c = eng.current, d = eng.draft, out = []
        if (!c || !d) return out
        for (const s of sections)
            for (const it of s.items) {
                const a = hexIn(c, it.key), b = hexIn(d, it.key)
                if (a !== b) out.push({ label: s.title + " · " + it.label, from: a, to: b })
            }
        if (c.wallpaper.home !== d.wallpaper.home) out.push({ label: "Sfondo della scrivania", image: d.wallpaper.home || "" })
        if (c.wallpaper.lock_same !== d.wallpaper.lock_same || (!d.wallpaper.lock_same && c.wallpaper.lock !== d.wallpaper.lock))
            out.push({ label: "Schermata di blocco", note: d.wallpaper.lock_same ? "stesso sfondo, sfocato" : "un'altra immagine" })
        return out
    }
    // passando sopra un colore che si vede solo nel blocco, l'anteprima passa al blocco
    readonly property bool lockZonesOnly: hoverZones.length > 0 && hoverZones.every(z => z === "lock" || z === "clock")

    focus: true
    Keys.onEscapePressed: if (editor.role !== "") editor.role = ""; else Qt.quit()

    // ── intestazione: logo, passi, chiaro/scuro, chiudi ─────────
    Item {
        id: header
        width: parent.width; height: 72
        Row {
            x: 22; anchors.verticalCenter: parent.verticalCenter
            spacing: 12
            Image { width: 40; height: 40; source: Qt.resolvedUrl("assets/camenix.svg"); sourceSize.width: 80; sourceSize.height: 80 }
            Column {
                anchors.verticalCenter: parent.verticalCenter
                Text { text: "Camenix"; color: pal.fg; font.family: pal.font; font.pixelSize: 19; font.weight: Font.ExtraBold }
                Text { text: "sfondo e colori del desktop"; color: pal.muted; font.family: pal.font; font.pixelSize: 11 }
            }
        }
        Row {                                       // ① Sfondo ── ② Colori ── ③ Applica
            anchors.centerIn: parent
            spacing: 8
            Repeater {
                model: ["Sfondo", "Colori", "Applica"]
                Row {
                    id: stepItem
                    required property string modelData
                    required property int index
                    readonly property int n: index + 1
                    readonly property bool on: main.step === n
                    spacing: 8
                    Rectangle {
                        visible: stepItem.index > 0
                        anchors.verticalCenter: parent.verticalCenter
                        width: 26; height: 2; radius: 1
                        color: main.step >= stepItem.n ? pal.accent2 : pal.line
                    }
                    Rectangle {
                        objectName: "step" + stepItem.n
                        width: stepRow.implicitWidth + 24; height: 36; radius: 18
                        color: stepItem.on ? pal.accent : (stepArea.containsMouse ? pal.hover : "transparent")
                        border.width: 1.5
                        border.color: stepItem.on ? pal.accent2 : pal.line
                        Behavior on color { ColorAnimation { duration: 120 } }
                        Row {
                            id: stepRow
                            anchors.centerIn: parent
                            spacing: 8
                            Rectangle {
                                width: 22; height: 22; radius: 11
                                anchors.verticalCenter: parent.verticalCenter
                                color: stepItem.on ? pal.accentInk : (main.step > stepItem.n ? pal.accent2 : pal.line)
                                Text { anchors.centerIn: parent; text: main.step > stepItem.n ? "✓" : stepItem.n
                                       color: stepItem.on ? pal.accent : (main.step > stepItem.n ? "white" : pal.fg)
                                       font.family: pal.font; font.pixelSize: 11; font.weight: Font.ExtraBold }
                            }
                            Text { anchors.verticalCenter: parent.verticalCenter; text: stepItem.modelData
                                   color: stepItem.on ? pal.accentInk : pal.fg; font.family: pal.font; font.pixelSize: 13; font.weight: Font.Bold }
                        }
                        MouseArea { id: stepArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    onClicked: main.step = stepItem.n }
                    }
                }
            }
        }
        Rectangle {                                 // chiaro / scuro (solo l'app)
            id: modeBtn
            anchors.right: closeBtn.left; anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            width: 74; height: 32; radius: 16
            color: pal.card
            border.width: 1.5; border.color: pal.line
            Rectangle {
                width: 28; height: 26; radius: 13; y: 3
                x: main.dark ? parent.width - width - 3 : 3
                color: pal.accent
                Behavior on x { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
            }
            Text { x: 10; anchors.verticalCenter: parent.verticalCenter; text: "☀"; color: main.dark ? pal.fg : pal.accentInk; font.pixelSize: 14 }
            Text { anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: "☾"; color: main.dark ? pal.accentInk : pal.fg; font.pixelSize: 14 }
            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: main.eng.setMode(main.dark ? "light" : "dark") }
        }
        Item {                                      // chiudi l'app: una ✕ leggera, rossa al passaggio
            id: closeBtn
            anchors.right: parent.right; anchors.rightMargin: 16
            anchors.verticalCenter: parent.verticalCenter
            width: 32; height: 32
            Rectangle { anchors.fill: parent; radius: 16; color: closeArea.containsMouse ? Qt.rgba(0.76, 0.22, 0.31, 0.14) : "transparent" }
            Text { anchors.centerIn: parent; text: "✕"; color: closeArea.containsMouse ? pal.bad : pal.muted; font.pixelSize: 15 }
            MouseArea { id: closeArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: Qt.quit() }
        }
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: pal.line }
    }

    // ── anteprima (sinistra) ───────────────────────────
    Item {
        id: previewCol
        x: 24; y: header.height + 18
        width: Math.round(parent.width * 0.55)
        height: bottom.y - y - 18
        Row {                                       // scrivania | blocco
            id: tabs
            spacing: 0
            Repeater {
                model: [{ t: "Scrivania", lock: false }, { t: "Blocco schermo", lock: true }]
                Rectangle {
                    required property var modelData
                    required property int index
                    readonly property bool on: main.showLock === modelData.lock
                    width: tabText.implicitWidth + 32; height: 32
                    radius: 16
                    color: on ? pal.fg : "transparent"
                    border.width: 1.5; border.color: on ? pal.fg : pal.line
                    Text { id: tabText; anchors.centerIn: parent; text: parent.modelData.t; color: parent.on ? pal.window : pal.fg
                           font.family: pal.font; font.pixelSize: 12; font.weight: Font.Bold }
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: main.showLock = parent.modelData.lock }
                }
            }
        }
        Text {
            anchors.right: parent.right; anchors.verticalCenter: tabs.verticalCenter
            text: "anteprima · il desktop cambia solo con Applica"
            color: pal.muted; font.family: pal.font; font.pixelSize: 10
        }
        Preview {
            id: preview
            ui: pal
            anchors.top: tabs.bottom; anchors.topMargin: 12
            width: parent.width; height: parent.height - tabs.height - 12
            theme: main.eng.draft
            highlight: main.hoverZones
            lock: main.showLock || main.lockZonesOnly
        }
    }

    // ── passo attuale (destra) ─────────────────────────
    Item {
        id: stepPanel
        anchors.left: previewCol.right; anchors.leftMargin: 26
        anchors.right: parent.right; anchors.rightMargin: 24
        y: previewCol.y
        height: previewCol.height

        component StepTitle: Column {
            property string title: ""
            property string sub: ""
            width: parent ? parent.width : 0             // (nota: «right»/«left» sono nomi riservati degli Item, mai usarli come id)
            spacing: 4
            Text { text: parent.title; color: pal.fg; font.family: pal.font; font.pixelSize: 18; font.weight: Font.ExtraBold }
            Text { width: parent.width; text: parent.sub; wrapMode: Text.WordWrap; color: pal.muted; font.family: pal.font; font.pixelSize: 11 }
        }
        component Card: Rectangle {
            width: parent ? parent.width : 0
            radius: 18
            color: pal.card
            border.width: 1.5; border.color: pal.line
        }

        // ① Sfondo
        Column {
            visible: main.step === 1
            width: parent.width
            spacing: 16
            StepTitle { title: "Scegli lo sfondo"; sub: "Un'immagine PNG, JPEG o WebP. Camenix ne tiene una copia, così puoi spostare o cancellare l'originale." }
            Card {
                height: 132
                Row {
                    x: 16; anchors.verticalCenter: parent.verticalCenter
                    spacing: 16
                    Rectangle {
                        width: 160; height: 100; radius: 12; clip: true
                        color: pal.panel; border.width: 1; border.color: pal.line
                        Image { anchors.fill: parent; anchors.margins: 1; fillMode: Image.PreserveAspectCrop; asynchronous: true
                                sourceSize.width: 320
                                source: main.eng.draft && main.eng.draft.wallpaper.home ? "file://" + main.eng.draft.wallpaper.home : "" }
                        Text { anchors.centerIn: parent; visible: !(main.eng.draft && main.eng.draft.wallpaper.home); text: "nessuno sfondo"
                               color: pal.muted; font.family: pal.font; font.pixelSize: 11 }
                    }
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 10
                        Row { spacing: 8
                            Icon { ui: pal; kind: "image"; width: 26; height: 26 }
                            Text { anchors.verticalCenter: parent.verticalCenter; text: "Scrivania"; color: pal.fg; font.family: pal.font; font.pixelSize: 14; font.weight: Font.Bold } }
                        Btn { ui: pal; text: "Scegli immagine…"; primary: true; onClicked: main.eng.chooseWallpaper("home") }
                    }
                }
            }
            Card {
                height: lockCol.implicitHeight + 32
                Column {
                    id: lockCol
                    x: 16; y: 16
                    width: parent.width - 32
                    spacing: 10
                    Row { spacing: 8
                        Icon { ui: pal; kind: "lock"; width: 26; height: 26 }
                        Text { anchors.verticalCenter: parent.verticalCenter; text: "Schermata di blocco"; color: pal.fg; font.family: pal.font; font.pixelSize: 14; font.weight: Font.Bold } }
                    Repeater {
                        model: [{ t: "Lo stesso sfondo, sfocato", same: true }, { t: "Un'altra immagine", same: false }]
                        Rectangle {
                            required property var modelData
                            readonly property bool on: main.eng.draft ? main.eng.draft.wallpaper.lock_same === modelData.same : modelData.same
                            width: lockCol.width; height: 40; radius: 12
                            color: on ? pal.hover : "transparent"
                            border.width: 1.5; border.color: on ? pal.accent2 : pal.line
                            Rectangle { x: 12; anchors.verticalCenter: parent.verticalCenter; width: 18; height: 18; radius: 9
                                        color: "transparent"; border.width: 2; border.color: parent.on ? pal.accent2 : pal.muted
                                        Rectangle { anchors.centerIn: parent; width: 8; height: 8; radius: 4; color: pal.accent2; visible: parent.parent.on } }
                            Text { x: 40; anchors.verticalCenter: parent.verticalCenter; text: parent.modelData.t; color: pal.fg; font.family: pal.font; font.pixelSize: 12 }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                        onClicked: { main.showLock = true; if (parent.modelData.same) main.eng.setLockSame(true); else main.eng.chooseWallpaper("lock") } }
                        }
                    }
                    Btn { ui: pal; visible: main.eng.draft && !main.eng.draft.wallpaper.lock_same; text: "Cambia immagine del blocco…"
                          onClicked: main.eng.chooseWallpaper("lock") }
                }
            }
        }

        // ② Colori
        Column {
            id: colorsStep
            visible: main.step === 2
            width: parent.width
            spacing: 12
            StepTitle { title: "Scegli i colori"; sub: "Passa sopra un colore per vedere dove compare, cliccalo per cambiarlo. Le sfumature si adattano da sole." }
            Repeater {
                model: main.sections
                Column {
                    id: sec
                    required property var modelData
                    width: colorsStep.width
                    spacing: 6
                    Row {
                        spacing: 8
                        Icon { ui: pal; kind: sec.modelData.icon; width: 24; height: 24; radius: 8 }
                        Text { anchors.verticalCenter: parent.verticalCenter; text: sec.modelData.title; color: pal.fg; font.family: pal.font; font.pixelSize: 13; font.weight: Font.ExtraBold }
                        Text { anchors.verticalCenter: parent.verticalCenter; text: sec.modelData.hint; color: pal.muted; font.family: pal.font; font.pixelSize: 10 }
                    }
                    Grid {
                        columns: 3
                        spacing: 8
                        Repeater {
                            model: sec.modelData.items
                            Swatch {
                                required property var modelData
                                ui: pal
                                width: (colorsStep.width - 16) / 3
                                label: modelData.label
                                hex: main.hexOf(modelData.key)
                                selected: editor.role === modelData.key
                                onHoveredChanged: main.hoverZones = hovered ? modelData.zones : []
                                onClicked: {
                                    main.hoverZones = []
                                    editor.label = sec.modelData.title + " · " + modelData.label
                                    editor.desc = modelData.desc
                                    editor.against = modelData.against ? main.hexOf(modelData.against) : ""
                                    editor.startHex = hex
                                    editor.role = modelData.key
                                }
                            }
                        }
                        Rectangle {                  // il gradiente dei bordi, accanto ai suoi due colori
                            visible: sec.modelData.icon === "borders"
                            width: (colorsStep.width - 16) / 3; height: 56; radius: 14
                            gradient: Gradient { orientation: Gradient.Horizontal
                                GradientStop { position: 0; color: main.hexOf("borderFrom") }
                                GradientStop { position: 1; color: main.hexOf("borderTo") } }
                            Rectangle { anchors.fill: parent; anchors.margins: 4; radius: 10; color: pal.card
                                Text { anchors.centerIn: parent; text: "finestra attiva"; color: pal.muted; font.family: pal.font; font.pixelSize: 10 } }
                        }
                    }
                }
            }
            Text {
                text: "↺  Torna ai colori iniziali"
                color: resetArea.containsMouse ? pal.accent2 : pal.muted
                font.family: pal.font; font.pixelSize: 11; font.underline: resetArea.containsMouse
                MouseArea { id: resetArea; anchors.fill: parent; anchors.margins: -6; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: main.eng.resetColors() }
            }
        }

        // ③ Applica
        Column {
            id: applyStep
            visible: main.step === 3
            width: parent.width
            spacing: 14
            StepTitle { title: "Controlla e applica"
                        sub: main.changes.length ? "Ecco cosa cambia sul desktop." : "Nessuna modifica: il desktop è già così. Torna a ① Sfondo o ② Colori per cambiare qualcosa." }
            Card {
                visible: main.changes.length > 0
                height: Math.min(changeList.implicitHeight + 24, 250)
                clip: true
                Flickable {
                    anchors.fill: parent; anchors.margins: 12
                    contentHeight: changeList.implicitHeight
                    boundsBehavior: Flickable.StopAtBounds
                    Column {
                        id: changeList
                        width: parent.width
                        spacing: 6
                        Repeater {
                            model: main.changes
                            Item {
                                required property var modelData
                                width: changeList.width; height: 28
                                Text { anchors.verticalCenter: parent.verticalCenter; width: parent.width - 120; elide: Text.ElideRight
                                       text: parent.modelData.label; color: pal.fg; font.family: pal.font; font.pixelSize: 12 }
                                Row {
                                    anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                                    spacing: 6
                                    visible: !!parent.modelData.from
                                    Rectangle { width: 26; height: 20; radius: 6; color: parent.parent.modelData.from || "transparent"; border.width: 1; border.color: pal.line }
                                    Text { anchors.verticalCenter: parent.verticalCenter; text: "→"; color: pal.muted; font.pixelSize: 12 }
                                    Rectangle { width: 26; height: 20; radius: 6; color: parent.parent.modelData.to || "transparent"; border.width: 1; border.color: pal.line }
                                }
                                Text { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; visible: !parent.modelData.from
                                       text: parent.modelData.note || "nuova immagine"; color: pal.muted; font.family: pal.font; font.pixelSize: 11 }
                            }
                        }
                    }
                }
            }
            Text { text: "Dove arriva"; color: pal.fg; font.family: pal.font; font.pixelSize: 13; font.weight: Font.ExtraBold }
            Flow {
                width: parent.width
                spacing: 6
                Repeater {
                    model: ["wallpaper"].concat(main.eng.managedKinds)
                    Rectangle {
                        required property string modelData
                        width: kindText.implicitWidth + 22; height: 28; radius: 14
                        color: pal.panel; border.width: 1; border.color: pal.line
                        Text { id: kindText; anchors.centerIn: parent; text: parent.modelData === "wallpaper" ? "Sfondo" : (main.kindNames[parent.modelData] || parent.modelData)
                               color: pal.fg; font.family: pal.font; font.pixelSize: 11 }
                    }
                }
            }
            Rectangle {
                width: parent.width; height: safeText.implicitHeight + 20; radius: 14
                color: pal.panel
                Text { id: safeText; x: 12; y: 10; width: parent.width - 24; wrapMode: Text.WordWrap
                       text: "Dopo aver premuto Applica hai 15 secondi per decidere: se non premi «Tieni», il desktop torna com'era. Prima di cambiare un file Camenix ne salva una copia."
                       color: pal.muted; font.family: pal.font; font.pixelSize: 11 }
            }
        }
    }

    // ── barra in basso ─────────────────────────────────
    Rectangle {
        id: bottom
        anchors.bottom: parent.bottom
        width: parent.width
        height: 70
        color: "transparent"
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
                    : main.eng.dirty ? (main.changes.length === 1 ? "1 modifica da applicare" : main.changes.length + " modifiche da applicare")
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
            Btn { ui: pal; visible: main.eng.dirty; text: "Annulla modifiche"; enabledBtn: !main.eng.busy; onClicked: main.eng.discard() }
            Btn { ui: pal; visible: main.step > 1; text: "← Indietro"; onClicked: main.step-- }
            Btn { ui: pal; visible: main.step < 3; text: "Avanti →"; primary: true; onClicked: main.step++ }
            Btn { ui: pal; visible: main.step === 3; text: "Applica ✓"; primary: true
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

    Welcome { ui: pal; eng: main.eng; kindNames: main.kindNames; visible: main.eng.firstRun }

    ColorEditor {
        id: editor
        ui: pal
        eng: main.eng
        wallpaper: main.eng.draft && main.eng.draft.wallpaper.home ? main.eng.draft.wallpaper.home : ""
        onDone: (hex) => { main.eng.setColor(role, hex); role = "" }
        onCancel: role = ""
    }
}
