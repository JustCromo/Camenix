// Camenix · collegamento tra l'interfaccia e il motore (camenix-engine)
// Tiene il tema applicato (theme.json), la bozza che stai modificando e le preferenze dell'app.
// Ogni operazione passa dal motore, che valida tutto: l'app non scrive mai le config da sola.
import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: eng

    readonly property string home: Quickshell.env("HOME")
    readonly property string engine: Quickshell.shellDir + "/../bin/camenix-engine"
    readonly property string cfgDir: home + "/.config/camenix"

    property var current: null          // tema applicato
    property var draft: null            // tema in modifica (quello mostrato nell'anteprima)
    readonly property bool dirty: !!current && !!draft && JSON.stringify(current) !== JSON.stringify(draft)
    property string mode: "light"       // tema dell'app: "light" | "dark"
    property bool busy: false
    readonly property var baseRoles: ["text", "glass", "accent", "accent2", "secondary", "success", "warning", "error", "borderFrom", "borderTo"]
    property string error: ""           // messaggio da mostrare (una frase)
    property var conflicts: []          // file modificati a mano che bloccano "Applica"
    property bool awaitingKeep: false   // paracadute attivo
    property bool firstRun: false       // nessun tema ancora: si parte dai colori trovati sul desktop
    property var detected: null         // { theme, found, will_manage } letti al primo avvio
    property var managedKinds: []       // programmi collegati (hyprland, kitty, mako…)
    property var original: null         // "colori iniziali" (quelli del desktop al primo avvio)
    signal applied()
    signal reverted()

    function clone(o) { return JSON.parse(JSON.stringify(o)) }
    function validHex(v) { return typeof v === "string" && /^#[0-9A-Fa-f]{6}$/.test(v) }

    // ── tema applicato ─────────────────────────────────
    property FileView themeFile: FileView {
        path: eng.cfgDir + "/theme.json"
        watchChanges: true
        onFileChanged: reload()
        onLoaded: eng.statusProc.running = true
        onLoadFailed: eng.statusProc.running = true
    }
    // la lettura passa dal motore, che normalizza il file (valori mancanti o ostili -> predefiniti)
    property Process statusProc: Process {
        command: [eng.engine, "status", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const d = JSON.parse(text)
                    eng.managedKinds = d.managed_kinds || []
                    eng.original = d.original || null
                    eng.firstRun = !!d.first_run
                    if (eng.firstRun) { eng.detectProc.running = true; return }
                    const wasClean = !eng.dirty
                    eng.current = d.theme
                    if (!eng.draft || wasClean) eng.draft = eng.clone(d.theme)
                } catch (e) { eng.error = "Non riesco a leggere il tema." }
            }
        }
    }

    // ── primo avvio ────────────────────────────────────
    // si leggono i colori del desktop (senza scrivere niente); "Inizia" li salva e collega i file
    property Process detectProc: Process {
        command: [eng.engine, "detect", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const d = JSON.parse(text)
                    eng.detected = d
                    eng.current = d.theme
                    eng.draft = eng.clone(d.theme)
                } catch (e) { eng.error = "Non riesco a leggere i colori del desktop." }
            }
        }
    }
    function start() { if (!startProc.running) { busy = true; error = ""; startProc.running = true } }
    property Process startProc: Process {
        command: [eng.engine, "first-run", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                eng.busy = false
                let r = null
                try { r = JSON.parse(text) } catch (e) {}
                if (!r || (!r.ok && r.why !== "already")) { eng.error = "Non sono riuscito a preparare Camenix: le copie dei file sono in ~/.config/camenix/backups."; return }
                eng.firstRun = false
                eng.draft = null
                eng.statusProc.running = true
            }
        }
    }

    // ── preferenze dell'app (chiaro/scuro) ─────────────
    property FileView prefsFile: FileView {
        path: eng.cfgDir + "/app.json"
        onLoaded: {
            try { const p = JSON.parse(text()); if (p.mode === "dark" || p.mode === "light") eng.mode = p.mode } catch (e) {}
        }
    }
    function setMode(m) {
        if (m !== "dark" && m !== "light") return
        mode = m
        prefsFile.setText(JSON.stringify({ mode: m }) + "\n")
    }

    // ── modifiche alla bozza ───────────────────────────
    // la bozza viaggia come argomento del motore: nessun file intermedio da aspettare

    function setColor(role, hex) { const m = {}; m[role] = hex; return setColors(m) }
    // più colori insieme (es. una palette): tutto o niente, poi le sfumature
    function setColors(map) {
        if (!draft || !map) return false
        const d = clone(draft)
        for (const role in map) {
            const hex = map[role]
            if (!validHex(hex)) return false
            if (role.indexOf("terminal.") === 0 && (role.slice(9) in d.terminal)) d.terminal[role.slice(9)] = hex.toUpperCase()
            else if (role in d.colors) d.colors[role] = hex.toUpperCase()
            else return false
        }
        draft = d
        deriveProc.command = [engine, "derive", JSON.stringify(d)]
        deriveProc.running = true        // le sfumature seguono il colore principale
        return true
    }
    property Process deriveProc: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const d = JSON.parse(text)
                    // risposta di una modifica superata (es. due colori cambiati di fila): si ignora
                    if (d && d.colors && JSON.stringify(d.colors) !== JSON.stringify(eng.draft.colors)) {
                        const mine = eng.draft.colors, keep = {}
                        for (const k in mine) keep[k] = mine[k]
                        for (const k in d.colors) if (eng.baseRoles.indexOf(k) < 0) keep[k] = d.colors[k]
                        const nd = eng.clone(eng.draft); nd.colors = keep; eng.draft = nd
                    }
                } catch (e) {}
            }
        }
    }

    function discard() { if (current) draft = clone(current); error = ""; conflicts = [] }

    // ── sfondo ─────────────────────────────────────────
    property string pickingFor: "home"
    property Process pickProc: Process {
        command: ["sh", "-c", "if command -v zenity >/dev/null; then exec zenity --file-selection --title='Scegli uno sfondo' --file-filter='Immagini | *.png *.jpg *.jpeg *.webp *.PNG *.JPG *.JPEG *.WEBP'; elif command -v kdialog >/dev/null; then exec kdialog --getopenfilename \"$HOME\" 'image/png image/jpeg image/webp'; else exit 3; fi"]
        stdout: StdioCollector {
            onStreamFinished: {
                const p = text.trim()
                if (p.length) { eng.importProc.command = [eng.engine, "import-wallpaper", p]; eng.importProc.running = true }
            }
        }
        onExited: (code) => { if (code === 3) eng.error = "Per scegliere un file serve zenity (o kdialog)." }
    }
    function chooseWallpaper(kind) { if (!pickProc.running) { pickingFor = kind; pickProc.running = true } }
    property Process importProc: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const r = JSON.parse(text)
                    if (!r.ok) { eng.error = "Questo file non è un'immagine PNG, JPEG o WebP."; return }
                    const d = eng.clone(eng.draft)
                    if (eng.pickingFor === "lock") { d.wallpaper.lock = r.path; d.wallpaper.lock_same = false }
                    else d.wallpaper.home = r.path
                    eng.draft = d
                } catch (e) { eng.error = "Non sono riuscito a importare l'immagine." }
            }
        }
    }
    function setLockSame(same) {
        const d = clone(draft); d.wallpaper.lock_same = same; draft = d
    }

    // ── applica, paracadute, annulla ───────────────────
    function apply() {
        if (busy || !draft) return
        busy = true; error = ""; conflicts = []
        applyProc.command = [engine, "apply-draft", JSON.stringify(draft), "--json"]
        applyProc.running = true
    }
    property Process applyProc: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                eng.busy = false
                let r = null
                try { r = JSON.parse(text) } catch (e) { eng.error = "Il motore non ha risposto."; return }
                if (r.ok) { eng.awaitingKeep = true; eng.applied() }
                else if (r.conflicts && r.conflicts.length) eng.conflicts = r.conflicts.map(c => c.file)
                else eng.error = "Non ho applicato niente: un file collegato non è utilizzabile."
            }
        }
    }
    function keep() { awaitingKeep = false }
    function revert() {
        awaitingKeep = false
        busy = true
        undoProc.running = true
    }
    property Process undoProc: Process {
        command: [eng.engine, "undo", "--json"]
        stdout: StdioCollector { onStreamFinished: { eng.busy = false; eng.draft = null; eng.reverted() } }
    }
    // "tieni le mie modifiche": il file modificato a mano diventa il nuovo modello, poi riprova
    function adoptAndRetry(file) {
        adoptProc.command = [eng.engine, "adopt", file]
        adoptProc.running = true
    }
    property Process adoptProc: Process {
        onExited: (code) => { eng.conflicts = []; if (code === 0) eng.apply(); else eng.error = "Non sono riuscito a usare quel file." }
    }
    function resetColors() { busy = true; error = ""; resetProc.running = true }
    property Process resetProc: Process {
        command: [eng.engine, "reset-colors", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                eng.busy = false
                try { const r = JSON.parse(text); if (!r.ok) eng.conflicts = (r.conflicts || []).map(c => c.file) } catch (e) {}
                eng.draft = null
            }
        }
    }

    // ── contrasto (WCAG) ───────────────────────────────
    function luminance(hex) {
        const ch = [1, 3, 5].map(i => parseInt(hex.substr(i, 2), 16) / 255)
                             .map(c => c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4))
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]
    }
    function contrast(a, b) {
        if (!validHex(a) || !validHex(b)) return 1
        const la = luminance(a), lb = luminance(b)
        return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)
    }

    Component.onCompleted: prefsFile.reload()
}
