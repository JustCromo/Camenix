// paracadute: "Tenere il nuovo tema?" con conto alla rovescia; se scade, torna il tema di prima
import QtQuick

Rectangle {
    id: toast
    property var ui
    property int seconds: 15
    property int remaining: seconds
    property bool active: false
    signal keep()
    signal revert()
    visible: active
    width: row.implicitWidth + 36
    height: 54
    radius: 27
    color: ui.window
    border.width: 1.5
    border.color: ui.accent
    onActiveChanged: if (active) { remaining = seconds; tick.restart() } else tick.stop()
    Timer {
        id: tick
        interval: 1000; repeat: true
        onTriggered: { toast.remaining--; if (toast.remaining <= 0) { stop(); toast.revert() } }
    }
    Row {
        id: row
        anchors.centerIn: parent
        spacing: 14
        Item {
            width: 34; height: 34
            anchors.verticalCenter: parent.verticalCenter
            Canvas {
                id: ring
                anchors.fill: parent
                property real frac: toast.remaining / toast.seconds
                onFracChanged: requestPaint()
                onPaint: {
                    const ctx = getContext("2d"); ctx.reset()
                    ctx.lineWidth = 4; ctx.lineCap = "round"
                    ctx.strokeStyle = Qt.rgba(0.5, 0.5, 0.5, 0.2)
                    ctx.beginPath(); ctx.arc(17, 17, 14, 0, Math.PI * 2); ctx.stroke()
                    ctx.strokeStyle = String(toast.ui.accent2)
                    ctx.beginPath(); ctx.arc(17, 17, 14, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * frac); ctx.stroke()
                }
            }
            Text { anchors.centerIn: parent; text: toast.remaining; color: ui.fg; font.family: ui.font; font.pixelSize: 12; font.weight: Font.Bold }
        }
        Text { anchors.verticalCenter: parent.verticalCenter; text: "Tenere il nuovo tema?"; color: ui.fg; font.family: ui.font; font.pixelSize: 14; font.weight: Font.Bold }
        Btn { ui: toast.ui; text: "Annulla"; anchors.verticalCenter: parent.verticalCenter; onClicked: toast.revert() }
        Btn { ui: toast.ui; text: "Tieni ✓"; primary: true; anchors.verticalCenter: parent.verticalCenter; onClicked: toast.keep() }
    }
}
