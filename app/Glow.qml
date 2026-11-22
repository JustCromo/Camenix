// contorno che pulsa intorno a un pezzo dell'anteprima: "questo colore finisce qui"
import QtQuick

Rectangle {
    id: g
    property bool on: false
    property real r: 8
    anchors.fill: parent
    anchors.margins: -4
    radius: r + 4
    color: "transparent"
    border.width: 3.5
    border.color: "white"
    visible: on
    z: 50
    Rectangle { anchors.fill: parent; anchors.margins: 3.5; radius: Math.max(0, g.radius - 3.5); color: "transparent"; border.width: 2; border.color: "#1E1528" }
    SequentialAnimation on opacity {
        running: g.on
        loops: Animation.Infinite
        NumberAnimation { to: 0.5; duration: 550; easing.type: Easing.InOutSine }
        NumberAnimation { to: 1; duration: 550; easing.type: Easing.InOutSine }
    }
}
