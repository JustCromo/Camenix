// pulsante a pillola, nello stile delle isole
import QtQuick

Rectangle {
    id: b
    property string text: ""
    property bool primary: false
    property bool enabledBtn: true
    property var ui
    signal clicked()
    implicitWidth: label.implicitWidth + 32
    implicitHeight: 38
    radius: height / 2
    opacity: enabledBtn ? 1 : 0.45
    color: primary ? (area.containsMouse ? ui.accentHover : ui.accent) : (area.containsMouse ? ui.hover : ui.button)
    border.width: 1.5
    border.color: primary ? ui.accent2 : ui.line
    Behavior on color { ColorAnimation { duration: 120 } }
    Text {
        id: label
        anchors.centerIn: parent
        text: b.text
        color: b.primary ? ui.onAccent : ui.fg
        font.family: ui.font
        font.pixelSize: 13
        font.weight: Font.Bold
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        enabled: b.enabledBtn
        cursorShape: Qt.PointingHandCursor
        onClicked: b.clicked()
    }
}
