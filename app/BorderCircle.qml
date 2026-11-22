// il bordo delle finestre: un cerchio diviso a metà (inizio | fine). Clic a sinistra o a destra.
import QtQuick

Item {
    id: bc
    property var ui
    property string label: ""
    property string from: "#000000"
    property string to: "#FFFFFF"
    property string selectedKey: ""
    readonly property bool hovered: area.containsMouse
    readonly property string side: area.mouseX < width / 2 ? "borderFrom" : "borderTo"
    signal picked(string key)
    width: 110; height: 96
    onFromChanged: cv.requestPaint()
    onToChanged: cv.requestPaint()
    Canvas {
        id: cv
        anchors.horizontalCenter: parent.horizontalCenter
        width: 52; height: 52
        scale: area.containsMouse ? 1.06 : 1
        Behavior on scale { NumberAnimation { duration: 120 } }
        readonly property string key: [bc.hovered, bc.side, bc.selectedKey].join()
        onKeyChanged: requestPaint()
        onPaint: {
            const c = getContext("2d"), r = 21, cx = width / 2, cy = height / 2
            c.reset()
            function half(start, end, color) { c.beginPath(); c.moveTo(cx, cy); c.arc(cx, cy, r, start, end); c.closePath(); c.fillStyle = color; c.fill() }
            half(Math.PI / 2, Math.PI * 1.5, bc.from)        // metà sinistra: inizio
            half(-Math.PI / 2, Math.PI / 2, bc.to)           // metà destra: fine
            c.beginPath(); c.arc(cx, cy, r, 0, Math.PI * 2); c.lineWidth = 1.5; c.strokeStyle = bc.ui.line; c.stroke()
            const hl = bc.hovered ? bc.side : bc.selectedKey     // anello sulla metà sotto il mouse (o scelta)
            if (hl === "borderFrom" || hl === "borderTo") {
                c.beginPath()
                if (hl === "borderFrom") c.arc(cx, cy, r + 3.5, Math.PI / 2, Math.PI * 1.5)
                else c.arc(cx, cy, r + 3.5, -Math.PI / 2, Math.PI / 2)
                c.lineWidth = 3; c.strokeStyle = bc.ui.accent2; c.stroke()
            }
        }
    }
    Text {
        id: name
        anchors.top: cv.bottom; anchors.topMargin: 6
        anchors.horizontalCenter: parent.horizontalCenter
        text: bc.label
        color: ui.fg
        font.family: ui.font; font.pixelSize: 11; font.weight: Font.Bold
    }
    Text {
        anchors.top: name.bottom; anchors.topMargin: 1
        anchors.horizontalCenter: parent.horizontalCenter
        text: bc.from + " → " + bc.to
        color: ui.muted
        font.family: ui.font; font.pixelSize: 9
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: bc.picked(bc.side)
    }
}
