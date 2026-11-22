// scelta di un colore (tappa 3: #hex e colori del tema; la ruota cromatica arriva nella tappa 4)
import QtQuick

Item {
    id: ed
    property var ui
    property var eng
    property string role: ""
    property string label: ""
    property string startHex: "#000000"
    property string against: ""             // colore con cui controllare la leggibilità
    property string hex: startHex
    readonly property bool valid: /^#[0-9A-Fa-f]{6}$/.test(hex)
    signal done(string hex)
    signal cancel()
    anchors.fill: parent
    visible: role !== ""
    onStartHexChanged: { hex = startHex; field.text = startHex }

    Rectangle { anchors.fill: parent; color: Qt.rgba(0.12, 0.08, 0.16, 0.35)
        MouseArea { anchors.fill: parent; onClicked: ed.cancel() } }

    Rectangle {
        id: card
        anchors.centerIn: parent
        width: 440; height: col.implicitHeight + 40
        radius: 26
        color: ui.window
        border.width: 1.5
        border.color: ui.line
        MouseArea { anchors.fill: parent }
        Column {
            id: col
            x: 22; y: 20
            width: parent.width - 44
            spacing: 14
            Row {
                spacing: 10
                Rectangle { width: 26; height: 26; radius: 8; color: ed.startHex; border.width: 1; border.color: ui.line }
                Text { anchors.verticalCenter: parent.verticalCenter; text: ed.label; color: ui.fg; font.family: ui.font; font.pixelSize: 15; font.weight: Font.ExtraBold }
            }
            Row {
                spacing: 10
                Rectangle { width: (col.width - 10) / 2; height: 90; radius: 14; color: ed.startHex; border.width: 1; border.color: ui.line
                    Text { anchors.centerIn: parent; text: "prima"; color: ed.eng.contrast(ed.startHex, "#FFFFFF") > 3 ? "white" : "#1E1528"; font.family: ui.font; font.pixelSize: 11 } }
                Rectangle { width: (col.width - 10) / 2; height: 90; radius: 14; color: ed.valid ? ed.hex : ed.startHex; border.width: 2; border.color: ui.accent2
                    Text { anchors.centerIn: parent; text: "dopo"; color: ed.eng.contrast(ed.valid ? ed.hex : ed.startHex, "#FFFFFF") > 3 ? "white" : "#1E1528"; font.family: ui.font; font.pixelSize: 11 } }
            }
            Text { text: "Colori del tema"; color: ui.muted; font.family: ui.font; font.pixelSize: 11 }
            Flow {
                width: col.width
                spacing: 7
                Repeater {
                    model: ed.eng.draft ? ["glass", "text", "accent", "accent2", "secondary", "success", "warning", "error",
                                            "accentSoft", "secondaryLight", "secondaryDeep", "paper"].map(k => ed.eng.draft.colors[k]) : []
                    Rectangle {
                        required property string modelData
                        width: 26; height: 26; radius: 13
                        color: modelData
                        border.width: 2
                        border.color: ed.hex.toUpperCase() === modelData ? ui.accent2 : "white"
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { ed.hex = parent.modelData; field.text = parent.modelData } }
                    }
                }
            }
            Row {
                spacing: 10
                Rectangle {
                    width: 180; height: 36; radius: 18
                    color: ui.input
                    border.width: 1.5
                    border.color: ed.valid ? ui.line : ui.bad
                    TextInput {
                        id: field
                        anchors.fill: parent; anchors.leftMargin: 14; anchors.rightMargin: 14
                        verticalAlignment: TextInput.AlignVCenter
                        text: ed.startHex
                        maximumLength: 7
                        color: ui.fg
                        font.family: ui.font; font.pixelSize: 14; font.weight: Font.Bold
                        selectByMouse: true
                        validator: RegularExpressionValidator { regularExpression: /#?[0-9A-Fa-f]{0,6}/ }
                        onTextEdited: ed.hex = (text.charAt(0) === "#" ? text : "#" + text).toUpperCase()
                        onAccepted: if (ed.valid) ed.done(ed.hex)
                    }
                }
                Rectangle {
                    visible: ed.against !== "" && ed.valid
                    readonly property real ratio: ed.eng.contrast(ed.hex, ed.against)
                    anchors.verticalCenter: parent.verticalCenter
                    width: cl.implicitWidth + 20; height: 26; radius: 13
                    color: "transparent"
                    border.width: 1
                    border.color: ratio >= 4.5 ? ui.ok : ui.bad
                    Text { id: cl; anchors.centerIn: parent; color: parent.ratio >= 4.5 ? ui.ok : ui.bad; font.family: ui.font; font.pixelSize: 11; font.weight: Font.Bold
                           text: (parent.ratio >= 4.5 ? "leggibile ✓ " : "poco leggibile ⚠ ") + parent.ratio.toFixed(1) + ":1" }
                }
            }
            Row {
                anchors.right: parent.right
                spacing: 8
                Btn { ui: ed.ui; text: "Annulla"; onClicked: ed.cancel() }
                Btn { ui: ed.ui; text: "Usa colore"; primary: true; enabledBtn: ed.valid; onClicked: ed.done(ed.hex) }
            }
        }
    }
}
