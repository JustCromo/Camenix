// dissolvenza di tutto il desktop quando si applica un tema:
// foto di ogni monitor -> la foto copre lo schermo -> si applica -> la foto sfuma e si vede il tema nuovo.
// Senza grim (o se qualcosa va storto) si applica e basta.
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

Scope {
    id: fd
    property string engine: ""
    readonly property bool available: true
    property bool active: false
    property real level: 1                  // opacità delle foto
    property var shots: ({})                // nome monitor -> percorso della foto
    property var then: null

    function begin(fn) {
        then = fn
        snapProc.running = true
    }
    function finish() { if (active) outTimer.restart() }
    function go() { const f = then; then = null; if (f) f() }

    Process {
        id: snapProc
        command: [fd.engine, "snapshot", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                let r = null
                try { r = JSON.parse(text) } catch (e) {}
                if (!r || !r.ok) { fd.go(); return }
                const m = {}
                for (const s of r.shots) m[s.name] = s.path
                fd.shots = m
                fd.level = 1
                fd.active = true
                inTimer.restart()           // il tempo di mostrare le foto, poi si applica
            }
        }
    }
    Timer { id: inTimer; interval: 220; onTriggered: fd.go() }
    // i programmi ricaricano (sfondo, kitty, Hyprland): si aspetta un attimo, poi si sfuma
    Timer { id: outTimer; interval: 450; onTriggered: fade.restart() }
    Timer { id: safetyTimer; interval: 10000; running: fd.active; onTriggered: { fd.active = false; cleanProc.running = true } }
    NumberAnimation {
        id: fade
        target: fd; property: "level"; from: 1; to: 0
        duration: 750; easing.type: Easing.InOutCubic
        onFinished: { fd.active = false; fd.shots = ({}); cleanProc.running = true }
    }
    Process { id: cleanProc; command: [fd.engine, "snapshot", "--clean"] }

    Variants {
        model: Quickshell.screens
        PanelWindow {
            required property var modelData
            readonly property string shot: fd.shots[modelData.name] || ""
            screen: modelData
            visible: fd.active && shot !== ""
            color: "transparent"
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.namespace: "camenix-fade"
            mask: Region {}                 // i clic passano sotto: non blocca niente
            Image {
                anchors.fill: parent
                source: parent.shot !== "" ? "file://" + parent.shot : ""
                cache: false
                asynchronous: false
                smooth: false
                opacity: fd.level
            }
        }
    }
}
