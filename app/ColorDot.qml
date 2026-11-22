// pallino di un colore da scegliere con un clic (nel selettore)
import QtQuick

Rectangle {
    id: dot
    property var ui
    property string c: "#000000"
    property bool chosen: false
    signal picked(string hex)
    width: 28; height: 28; radius: 14
    color: c
    border.width: 2
    border.color: chosen ? ui.accent2 : (area.containsMouse ? ui.fg : "white")
    MouseArea {
        id: area
        anchors.fill: parent; anchors.margins: -2
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: dot.picked(dot.c)
    }
}
