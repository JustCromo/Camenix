// un colore del tema: cerchio grande, nome e #hex sotto
import QtQuick

Item {
    id: cc
    property var ui
    property string label: ""
    property string hex: "#000000"
    property bool selected: false
    readonly property alias hovered: area.containsMouse
    signal clicked()
    width: 80; height: 96
    Rectangle {
        id: ring
        anchors.horizontalCenter: parent.horizontalCenter
        width: 52; height: 52; radius: 26
        color: "transparent"
        border.width: cc.selected || area.containsMouse ? 3 : 0
        border.color: ui.accent2
        Rectangle {
            anchors.fill: parent; anchors.margins: 5
            radius: width / 2
            color: cc.hex
            border.width: 1; border.color: Qt.rgba(0, 0, 0, 0.18)
        }
        scale: area.containsMouse ? 1.06 : 1
        Behavior on scale { NumberAnimation { duration: 120 } }
    }
    Text {
        id: name
        anchors.top: ring.bottom; anchors.topMargin: 6
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight
        text: cc.label
        color: ui.fg
        font.family: ui.font; font.pixelSize: 11; font.weight: Font.Bold
    }
    Text {
        anchors.top: name.bottom; anchors.topMargin: 1
        anchors.horizontalCenter: parent.horizontalCenter
        text: cc.hex
        color: ui.muted
        font.family: ui.font; font.pixelSize: 10
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: cc.clicked()
    }
}
