// iconcine disegnate a mano (niente font di icone: funzionano su qualsiasi sistema)
import QtQuick

Rectangle {
    id: ic
    property var ui
    property string kind: "image"          // image | islands | borders | terminal | alerts | lock
    property color ink: ui ? ui.heading : "#8E78E0"
    width: 32; height: 32; radius: 10
    color: ui ? ui.card : "white"
    border.width: 1; border.color: ui ? ui.line : "#D4C8FA"
    onInkChanged: cv.requestPaint()
    onKindChanged: cv.requestPaint()
    Canvas {
        id: cv
        anchors.fill: parent
        anchors.margins: 7
        onPaint: {
            const c = getContext("2d"), w = width, h = height
            c.reset()
            c.strokeStyle = ic.ink; c.fillStyle = ic.ink
            c.lineWidth = 1.8; c.lineCap = "round"; c.lineJoin = "round"
            function rr(x, y, ww, hh, r) { c.beginPath(); c.roundedRect(x, y, ww, hh, r, r) }
            if (ic.kind === "image") {
                rr(1, 2, w - 2, h - 4, 3); c.stroke()
                c.beginPath(); c.moveTo(3, h - 4); c.lineTo(w * 0.4, h * 0.45); c.lineTo(w * 0.62, h * 0.7); c.lineTo(w * 0.75, h * 0.55); c.lineTo(w - 3, h - 4); c.stroke()
                c.beginPath(); c.arc(w * 0.7, h * 0.3, 1.8, 0, Math.PI * 2); c.fill()
            } else if (ic.kind === "islands") {
                rr(1, 2, w * 0.38, 5, 2.5); c.stroke()
                rr(w * 0.5, 2, w * 0.48, 5, 2.5); c.stroke()
                rr(1, h * 0.5, w - 2, h * 0.45, 3); c.stroke()
            } else if (ic.kind === "borders") {
                rr(1, 1, w - 2, h - 2, 3); c.lineWidth = 2.6; c.stroke()
                c.lineWidth = 1.4; c.beginPath(); c.moveTo(1, 5.5); c.lineTo(w - 1, 5.5); c.stroke()
            } else if (ic.kind === "terminal") {
                rr(1, 2, w - 2, h - 4, 3); c.stroke()
                c.beginPath(); c.moveTo(4, h * 0.38); c.lineTo(7.5, h * 0.52); c.lineTo(4, h * 0.66); c.stroke()
                c.beginPath(); c.moveTo(9.5, h * 0.68); c.lineTo(w - 4, h * 0.68); c.stroke()
            } else if (ic.kind === "alerts") {
                c.beginPath(); c.moveTo(w / 2, 1); c.lineTo(w - 1, h - 2); c.lineTo(1, h - 2); c.closePath(); c.stroke()
                c.beginPath(); c.moveTo(w / 2, h * 0.38); c.lineTo(w / 2, h * 0.62); c.stroke()
                c.beginPath(); c.arc(w / 2, h * 0.78, 1.2, 0, Math.PI * 2); c.fill()
            } else if (ic.kind === "lock") {
                rr(2, h * 0.45, w - 4, h * 0.52, 3); c.stroke()
                c.beginPath(); c.arc(w / 2, h * 0.42, w * 0.26, Math.PI, 0); c.stroke()
            }
        }
    }
}
