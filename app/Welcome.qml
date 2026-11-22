// primo avvio: "questi sono i colori che usi adesso" + cosa Camenix collegherà, poi "Inizia"
import QtQuick

Item {
    id: wl
    property var ui
    property var eng
    readonly property var d: eng.detected
    readonly property var colors: d ? [
        { k: "glass", t: "color.glass" }, { k: "text", t: "color.text" }, { k: "accent", t: "color.accent" },
        { k: "borderFrom", t: "welcome.borderStart" }, { k: "borderTo", t: "welcome.borderEnd" }, { k: "terminal", t: "color.terminal" }
    ] : []
    readonly property var kinds: {
        if (!d) return []
        const seen = {}, out = []
        for (const f of d.will_manage) if (!seen[f.kind]) { seen[f.kind] = true; out.push(f.kind) }
        return out
    }
    anchors.fill: parent
    z: 100

    Rectangle { anchors.fill: parent; color: Qt.rgba(0.12, 0.08, 0.16, 0.55); MouseArea { anchors.fill: parent } }

    Rectangle {
        anchors.centerIn: parent
        width: 600; height: col.implicitHeight + 56
        radius: 28
        color: ui.window
        border.width: 1.5; border.color: ui.line
        Column {
            id: col
            x: 32; y: 28
            width: parent.width - 64
            spacing: 16
            Row {
                spacing: 14
                Image { width: 56; height: 56; source: Qt.resolvedUrl("assets/camenix.svg"); sourceSize.width: 112; sourceSize.height: 112 }
                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3
                    Text { text: wl.eng.tr("welcome.title"); color: ui.fg; font.family: ui.font; font.pixelSize: 20; font.weight: Font.ExtraBold }
                    Text { text: wl.eng.tr("app.tagline"); color: ui.muted; font.family: ui.font; font.pixelSize: 12 }
                }
            }
            Text {
                width: parent.width; wrapMode: Text.WordWrap
                text: !wl.d ? wl.eng.tr("welcome.looking")
                    : wl.eng.tr("welcome.found")
                color: ui.fg; font.family: ui.font; font.pixelSize: 12
            }
            Row {
                visible: !!wl.d
                spacing: 10
                Repeater {
                    model: wl.colors
                    Column {
                        required property var modelData
                        spacing: 4
                        width: 80
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: 44; height: 44; radius: 12
                            color: !wl.d ? "transparent" : parent.modelData.k === "terminal" ? wl.d.theme.terminal.background : wl.d.theme.colors[parent.modelData.k]
                            border.width: 1; border.color: ui.line
                        }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: wl.eng.tr(parent.modelData.t); color: ui.muted; font.family: ui.font; font.pixelSize: 10 }
                    }
                }
            }
            Text {
                visible: !!wl.d
                width: parent.width; wrapMode: Text.WordWrap
                text: wl.kinds.length ? wl.eng.tr("welcome.manage") : wl.eng.tr("welcome.none")
                color: ui.fg; font.family: ui.font; font.pixelSize: 12; font.weight: Font.Bold
            }
            Flow {
                visible: wl.kinds.length > 0
                width: parent.width
                spacing: 6
                Repeater {
                    model: ["wallpaper"].concat(wl.kinds)
                    Rectangle {
                        required property string modelData
                        width: kt.implicitWidth + 22; height: 28; radius: 14
                        color: ui.panel; border.width: 1; border.color: ui.line
                        Text { id: kt; anchors.centerIn: parent; text: wl.eng.tr("kind." + parent.modelData)
                               color: ui.fg; font.family: ui.font; font.pixelSize: 11 }
                    }
                }
            }
            Text {
                width: parent.width; wrapMode: Text.WordWrap
                text: wl.eng.tr("welcome.safe")
                color: ui.muted; font.family: ui.font; font.pixelSize: 11
            }
            Text { visible: wl.eng.error !== ""; width: parent.width; wrapMode: Text.WordWrap; text: wl.eng.error; color: ui.bad; font.family: ui.font; font.pixelSize: 11 }
            Row {
                anchors.right: parent.right
                spacing: 10
                Btn { ui: wl.ui; text: wl.eng.tr("welcome.quit"); onClicked: Qt.quit() }
                Btn { objectName: "startBtn"; ui: wl.ui; text: wl.eng.busy ? wl.eng.tr("welcome.starting") : wl.eng.tr("welcome.start"); primary: true
                      enabledBtn: !!wl.d && !wl.eng.busy; onClicked: wl.eng.start() }
            }
        }
    }
}
