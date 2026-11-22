// riquadro di un colore del tema: anteprima, nome, #hex e (per il testo) controllo di leggibilità
import QtQuick

Rectangle {
    id: sw
    property var ui
    property string label: ""
    property string hex: "#000000"
    property string note: ""
    property bool noteOk: true
    property bool selected: false
    signal clicked()
    implicitHeight: 112
    radius: 16
    color: area.containsMouse ? ui.hover : ui.card
    border.width: 1.5
    border.color: selected ? ui.accent2 : ui.line
    Rectangle {
        id: chip
        x: 8; y: 8
        width: parent.width - 16
        height: 58
        radius: 10
        color: sw.hex
        border.width: 1
        border.color: Qt.rgba(0, 0, 0, 0.12)
    }
    Text {
        x: 10; anchors.top: chip.bottom; anchors.topMargin: 6
        width: parent.width - 20
        elide: Text.ElideRight
        text: sw.label
        color: ui.fg
        font.family: ui.font
        font.pixelSize: 12
    }
    Text {
        x: 10; anchors.bottom: parent.bottom; anchors.bottomMargin: 8
        text: sw.hex
        color: ui.muted
        font.family: ui.font
        font.pixelSize: 11
    }
    Text {
        visible: sw.note !== ""
        anchors.right: parent.right; anchors.rightMargin: 10
        anchors.bottom: parent.bottom; anchors.bottomMargin: 8
        text: sw.note
        color: sw.noteOk ? ui.ok : ui.bad
        font.family: ui.font
        font.pixelSize: 10
        font.weight: Font.Bold
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: sw.clicked()
    }
}
