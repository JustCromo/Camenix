// riquadro di un colore: pallino, nome e #hex (per il testo anche la leggibilità)
import QtQuick

Rectangle {
    id: sw
    property var ui
    property string label: ""
    property string hex: "#000000"
    property string note: ""
    property bool noteOk: true
    property bool selected: false
    readonly property alias hovered: area.containsMouse
    signal clicked()
    implicitHeight: 56
    radius: 14
    color: area.containsMouse ? ui.hover : ui.card
    border.width: 1.5
    border.color: selected || area.containsMouse ? ui.accent2 : ui.line
    Behavior on color { ColorAnimation { duration: 100 } }
    Rectangle {
        id: chip
        x: 8; anchors.verticalCenter: parent.verticalCenter
        width: 38; height: 38
        radius: 10
        color: sw.hex
        border.width: 1
        border.color: Qt.rgba(0, 0, 0, 0.15)
    }
    Column {
        anchors.left: chip.right; anchors.leftMargin: 9
        anchors.right: parent.right; anchors.rightMargin: 8
        anchors.verticalCenter: parent.verticalCenter
        spacing: 2
        Text { width: parent.width; elide: Text.ElideRight; text: sw.label; color: ui.fg; font.family: ui.font; font.pixelSize: 12; font.weight: Font.Bold }
        Row {
            spacing: 6
            Text { text: sw.hex; color: ui.muted; font.family: ui.font; font.pixelSize: 10 }
            Text { visible: sw.note !== ""; text: sw.note; color: sw.noteOk ? ui.ok : ui.bad; font.family: ui.font; font.pixelSize: 10; font.weight: Font.Bold }
        }
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: sw.clicked()
    }
}
