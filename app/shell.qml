//@ pragma ShellId camenix
// Camenix · app per il tema del desktop (si avvia con il comando `camenix`)
import QtQuick
import Quickshell
import Quickshell.Io

ShellRoot {
    Engine { id: eng; fader: fader }
    Fader { id: fader; engine: eng.engine }

    FloatingWindow {
        id: win
        title: "Camenix"
        implicitWidth: 1180
        implicitHeight: 760
        color: "transparent"
        Main { anchors.fill: parent; eng: eng }
        onVisibleChanged: if (!visible) Qt.quit()
    }

    // `camenix` lanciato di nuovo mentre l'app è aperta: la mostra invece di aprirne un'altra
    IpcHandler {
        target: "camenix"
        function show(): void { win.visible = true }
    }
}
