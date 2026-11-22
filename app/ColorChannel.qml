// cursore di un canale (R, G o B) del selettore: la barra mostra come cambierebbe il colore
import QtQuick
import "color.js" as C

Item {
    id: ch
    property var ui
    property string name: ""
    property int value: 0
    property string current: "#000000"
    property string from: "#000000"
    property string to: "#FFFFFF"
    signal moved(int v)
    width: 300; height: 24
    Text { anchors.verticalCenter: parent.verticalCenter; text: ch.name; color: ui.muted; font.family: ui.font; font.pixelSize: 12; font.weight: Font.Bold }
    Rectangle {
        id: track
        objectName: "track"
        x: 22; anchors.verticalCenter: parent.verticalCenter
        width: parent.width - 22 - 42; height: 12; radius: 6
        border.width: 1; border.color: ui.line
        gradient: Gradient { orientation: Gradient.Horizontal
            GradientStop { position: 0; color: ch.from }
            GradientStop { position: 1; color: ch.to } }
        Rectangle { width: 16; height: 16; radius: 8; anchors.verticalCenter: parent.verticalCenter
                    x: ch.value / 255 * track.width - 8; color: ch.current; border.width: 3; border.color: "white" }
        MouseArea {
            anchors.fill: parent; anchors.margins: -8
            cursorShape: Qt.PointingHandCursor
            preventStealing: true
            function set(mx) { ch.moved(Math.round(C.clamp((mx - 8) / track.width, 0, 1) * 255)) }
            onPressed: (m) => set(m.x)
            onPositionChanged: (m) => { if (pressed) set(m.x) }
        }
    }
    Text { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; text: ch.value; color: ui.fg; font.family: ui.font; font.pixelSize: 12 }
}
