// sole o luna disegnati (non caratteri di un font: così sono sempre centrati e uguali su ogni sistema)
import QtQuick

Canvas {
    id: mi
    property bool moon: false
    property color ink: "black"
    width: 16; height: 16
    onInkChanged: requestPaint()
    onMoonChanged: requestPaint()
    onPaint: {
        const c = getContext("2d"), cx = width / 2, cy = height / 2
        c.reset()
        c.fillStyle = ink; c.strokeStyle = ink; c.lineCap = "round"; c.lineWidth = 1.6
        if (moon) {
            // falce: cerchio pieno meno un cerchio spostato in alto a destra
            c.beginPath(); c.arc(cx, cy, 6.2, 0, Math.PI * 2); c.fill()
            c.globalCompositeOperation = "destination-out"
            c.beginPath(); c.arc(cx + 3.2, cy - 2.6, 5.2, 0, Math.PI * 2); c.fill()
            c.globalCompositeOperation = "source-over"
        } else {
            c.beginPath(); c.arc(cx, cy, 3.4, 0, Math.PI * 2); c.fill()
            for (let i = 0; i < 8; i++) {
                const a = i * Math.PI / 4
                c.beginPath()
                c.moveTo(cx + Math.cos(a) * 5.4, cy + Math.sin(a) * 5.4)
                c.lineTo(cx + Math.cos(a) * 7.2, cy + Math.sin(a) * 7.2)
                c.stroke()
            }
        }
    }
}
