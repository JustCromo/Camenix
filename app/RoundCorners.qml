// angoli arrotondati per un'anteprima: copre gli angoli col colore di fondo e disegna il bordo.
// (Il "clip" di Qt taglia solo rettangoli dritti; così funziona ovunque, senza effetti grafici.)
import QtQuick

Canvas {
    id: rc
    property real radius: 22
    property color bg: "white"
    property color line: "transparent"
    property real lineWidth: 1.5
    anchors.fill: parent
    z: 90
    onBgChanged: requestPaint()
    onLineChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const c = getContext("2d"), r = Math.min(radius, width / 2, height / 2), t = lineWidth
        c.reset()
        c.fillStyle = bg
        c.beginPath()
        c.rect(0, 0, width, height)
        c.roundedRect(0, 0, width, height, r, r)
        c.fillRule = Qt.OddEvenFill
        c.fill()
        if (t > 0) {
            c.beginPath(); c.roundedRect(t / 2, t / 2, width - t, height - t, r - t / 2, r - t / 2)
            c.lineWidth = t; c.strokeStyle = line; c.stroke()
        }
    }
}
