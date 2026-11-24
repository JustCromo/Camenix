"""Applica il tema a tutto il desktop: tutto o niente.

1. calcola in memoria ogni file da scrivere (modelli, colori di kitty, Theme.qml);
2. se un file è stato modificato a mano o un modello non si può riempire, si ferma senza toccare nulla;
3. scrive tutto, poi avvisa i programmi (Hyprland, mako, kitty, sfondo)."""
import glob
import json
import os
import re
import time
from importlib import resources

from camenix import derive as dv, detect, files, login, render, system, theme as th, wallpaper
import shutil

KITTY_INCLUDE = "include ~/.config/camenix/generated/kitty.conf"
KITTY_MARK = "# Camenix: colori del tema (non togliere questa riga se usi Camenix)"
QML_MARK = "// Camenix · tema per Quickshell"
HISTORY_KEEP = 20


# ── percorsi di Camenix ──────────────────────────────────
def cfg(*parts):
    return os.path.join(th.config_dir(), *parts)


def state_path():
    return cfg("state.json")


def load_state():
    try:
        data = json.loads(files.read_text(state_path(), limit=256 * 1024))
        if isinstance(data, dict) and isinstance(data.get("files"), list):
            return data
    except (files.UnsafeFile, OSError, ValueError):
        pass
    return {"version": 1, "files": [], "wallpaper": None}


def save_state(state):
    os.makedirs(th.config_dir(), mode=0o700, exist_ok=True)
    files.atomic_write(state_path(), json.dumps(state, indent=2) + "\n", default_mode=0o600)


def reload_kind(path):
    p = path.replace(os.sep, "/")
    if "/hypr/" in p and (p.endswith(".lua") or p.endswith("hyprland.conf")):
        return "hyprland"
    if p.endswith("/mako/config"):
        return "mako"
    return "none"


def kind(path):
    """Che programma usa il file (per dire all'utente cosa cambia, in parole sue)."""
    p = path.replace(os.sep, "/")
    if p.endswith("/hyprlock.conf"):
        return "hyprlock"
    if reload_kind(path) == "hyprland":
        return "hyprland"
    if p.endswith("/mako/config"):
        return "mako"
    if p.endswith(".rasi"):
        return "rofi"
    if p.endswith("/kitty.conf"):
        return "kitty"
    if p.endswith("/Theme.qml"):
        return "quickshell"
    return "other"


PREFER = {
    "hyprland": ("borderFrom", "borderTo", "borderIdle"),
    "mako": ("glass", "text", "accent", "accent2", "error"),
    "hyprlock": ("accent", "glass", "text", "textAlt"),
}


# ── modelli ──────────────────────────────────────────────
def adopt_file(path, theme, state):
    """Crea (o ricrea) il modello di un file. -> numero di colori collegati al tema."""
    real = files.resolve(path)
    text = files.read_text(real)
    template, count = render.adopt(text, theme, PREFER.get(kind(real), ()))
    if count == 0:
        return 0
    os.makedirs(cfg("templates"), mode=0o700, exist_ok=True)
    name = files.sha256(real)[:16] + ".tmpl"
    files.atomic_write(cfg("templates", name), template, default_mode=0o600)
    rendered = render.render(template, theme)
    entry = {"target": real, "template": name, "reload": reload_kind(real), "last_hash": files.sha256(rendered)}
    state["files"] = [f for f in state["files"] if f.get("target") != real] + [entry]
    if rendered != text:                      # es. "~/sfondo.png" diventa il percorso completo
        files.backup(real, cfg("backups"))
        files.atomic_write(real, rendered)
    return count


def forget_file(path, state):
    real = os.path.realpath(os.path.expanduser(path))
    before = len(state["files"])
    for f in state["files"]:
        if f.get("target") == real:
            try:
                os.unlink(cfg("templates", os.path.basename(f["template"])))
            except OSError:
                pass
    state["files"] = [f for f in state["files"] if f.get("target") != real]
    return before != len(state["files"])


# ── file generati ────────────────────────────────────────
def kitty_conf(theme):
    t = theme["terminal"]
    lines = ["# Generato da Camenix: si riscrive a ogni \"Applica\", non modificarlo a mano."]
    for key in ("background", "foreground", "cursor", "selection_background", "selection_foreground"):
        lines.append(f"{key} {t[key]}")
    for i in range(16):
        lines.append(f"color{i} {t[f'color{i}']}")
    return "\n".join(lines) + "\n"


def quickshell_theme_qml():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(root, "integrations", "quickshell", "Theme.qml")
    with open(p, encoding="utf-8") as f:
        return f.read()


def quickshell_target():
    """Theme.qml installato dall'utente nella sua shell (solo se c'è già: non lo aggiungiamo noi)."""
    p = os.path.expanduser("~/.config/quickshell/Theme.qml")
    try:
        text = files.read_text(p)
    except (files.UnsafeFile, OSError):
        return None
    return p if QML_MARK in text[:400] else None


# ── applica ──────────────────────────────────────────────
class Report:
    def __init__(self):
        self.written, self.skipped, self.conflicts, self.errors, self.reloaded = [], [], [], [], []
        self.wallpaper = None
        self.login = None

    def as_dict(self):
        return {"ok": not (self.conflicts or self.errors), "written": self.written, "conflicts": self.conflicts,
                "errors": self.errors, "reloaded": self.reloaded, "wallpaper": self.wallpaper,
                "login": self.login}


def apply(theme=None, dry_run=False, do_reload=True):
    report = Report()
    if theme is None:
        theme, _, _ = th.read()
    state = load_state()
    plan = []                                   # (percorso, testo nuovo, voce di stato o None)

    for entry in state["files"]:
        target = entry.get("target", "")
        try:
            current = files.read_text(target)
            template = files.read_text(cfg("templates", os.path.basename(entry.get("template", ""))))
        except (files.UnsafeFile, OSError):
            report.errors.append({"file": target, "why": "missing"})
            continue
        if files.sha256(current) != entry.get("last_hash"):
            report.conflicts.append({"file": target})
            continue
        try:
            new = render.render(template, theme)
        except render.RenderError as e:
            report.errors.append({"file": target, "why": "unknown:" + e.key})
            continue
        if new != current:
            plan.append((target, new, entry))

    kitty_out = cfg("generated", "kitty.conf")
    new_kitty = kitty_conf(theme)
    try:
        old_kitty = files.read_text(kitty_out)
    except (files.UnsafeFile, OSError):
        old_kitty = None
    if new_kitty != old_kitty:
        plan.append((kitty_out, new_kitty, None))

    qml = quickshell_target()
    if qml:
        new_qml = quickshell_theme_qml()
        if files.read_text(qml) != new_qml:
            plan.append((qml, new_qml, None))

    if report.conflicts or report.errors or dry_run:
        report.written = [p for p, _, _ in plan] if dry_run else []
        return report

    for path, text, entry in plan:              # tutto controllato: ora si scrive
        os.makedirs(os.path.dirname(path), exist_ok=True)
        files.atomic_write(path, text)
        if entry is not None:
            entry["last_hash"] = files.sha256(text)
        report.written.append(path)

    wp = theme.get("wallpaper", {}).get("home")
    if wp and wp != state.get("wallpaper"):
        ok, backend = (wallpaper.set_wallpaper(wp) if do_reload else (True, None))
        report.wallpaper = {"path": wp, "ok": ok, "backend": backend}
        if ok:
            state["wallpaper"] = wp
    save_state(state)

    # sfondo della schermata di accesso: solo se l'utente ha preparato /var/lib/camenix
    if do_reload:
        img = login.image_for(theme)
        if img:
            report.login = login.sync(img)

    if do_reload:
        kinds = {e["reload"] for _, _, e in plan if e is not None}
        if "hyprland" in kinds and system.run(["hyprctl", "reload"])[0]:
            report.reloaded.append("hyprland")
        if "mako" in kinds and system.run(["makoctl", "reload"])[0]:
            report.reloaded.append("mako")
        if any(p == kitty_out for p, _, _ in plan) and system.signal_own("kitty", "SIGUSR1"):
            report.reloaded.append("kitty")
    return report


# ── storico (per "Annulla" e per il paracadute) ─────────
def save_history():
    src = th.theme_path()
    if not os.path.isfile(src) or os.path.islink(src):
        return None
    os.makedirs(cfg("history"), mode=0o700, exist_ok=True)
    # nome = nanosecondi a 20 cifre: l'ordine alfabetico è sempre l'ordine nel tempo, anche nello stesso secondo
    stamp = time.time_ns()
    while os.path.exists(cfg("history", f"{stamp:020d}.json")):
        stamp += 1
    dest = cfg("history", f"{stamp:020d}.json")
    files.atomic_write(dest, files.read_text(src, limit=th.MAX_BYTES + 1), default_mode=0o600)
    old = sorted(glob.glob(cfg("history", "*.json")))
    for p in old[:-HISTORY_KEEP]:
        os.unlink(p)
    return dest


def change_theme(new_theme):
    """Prima controlla che il tema si possa applicare ovunque; solo allora salva il precedente nello
    storico, scrive il nuovo e lo applica. Se qualcosa blocca, il tema resta quello di prima."""
    new_theme, _ = th.normalize(new_theme)
    check = apply(new_theme, dry_run=True)
    if check.conflicts or check.errors:
        check.written = []
        return check
    save_history()
    th.write(new_theme)
    return apply()


def undo():
    """Torna al tema precedente. -> Report, oppure None se lo storico è vuoto."""
    old = sorted(glob.glob(cfg("history", "*.json")))
    if not old:
        return None
    last = old[-1]
    data, _ = th.normalize(json.loads(files.read_text(last, limit=th.MAX_BYTES + 1)))
    check = apply(data, dry_run=True)
    if check.conflicts or check.errors:
        check.written = []
        return check
    th.write(data)
    os.unlink(last)
    return apply()


# ── per l'app ────────────────────────────────────────────
def parse_draft(text):
    """Bozza inviata dall'app (testo JSON) -> tema normalizzato. È input non fidato: stesse regole del tema."""
    if not isinstance(text, str) or len(text.encode("utf-8", "replace")) > th.MAX_BYTES:
        raise ValueError("draft too big")
    theme, _ = th.normalize(json.loads(text))
    return theme


def derive_draft(text):
    """Ricalcola le sfumature della bozza rispetto al tema attuale."""
    draft = parse_draft(text)
    current, _, _ = th.read()
    draft["colors"] = dv.derive(draft["colors"], current["colors"])
    return draft


def import_wallpaper(path):
    """Copia l'immagine scelta in ~/.config/camenix/wallpapers (il tema non si rompe se l'originale
    viene spostato o cancellato). -> percorso della copia, oppure None se non è un'immagine valida."""
    src = os.path.realpath(os.path.expanduser(path))
    if not wallpaper.is_image(src):
        return None
    with open(src, "rb") as f:
        head = f.read(12)
    ext = ".png" if head.startswith(b"\x89PNG") else ".webp" if head[:4] == b"RIFF" else ".jpg"
    folder = cfg("wallpapers")
    os.makedirs(folder, mode=0o700, exist_ok=True)
    import hashlib
    h = hashlib.sha256()
    with open(src, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    digest = h.hexdigest()[:16]
    dest = os.path.join(folder, digest + ext)
    if not os.path.exists(dest):
        tmp = dest + ".tmp"
        shutil.copyfile(src, tmp)
        os.chmod(tmp, 0o644)
        os.replace(tmp, dest)
    return dest if th._valid_wallpaper(dest) else None


def original_path():
    return cfg("original.json")


def original():
    """Colori trovati sul desktop al primo avvio (se Camenix è partito così), altrimenti None."""
    try:
        theme, _ = th.normalize(json.loads(files.read_text(original_path(), limit=64 * 1024)))
        return theme
    except (files.UnsafeFile, OSError, ValueError):
        return None


def reset_colors():
    """Colori iniziali (quelli del desktop al primo avvio, o quelli predefiniti), sfondo invariato."""
    current, _, _ = th.read()
    fresh = original() or th.default_theme(current["name"])
    fresh["name"] = current["name"]
    fresh["wallpaper"] = current["wallpaper"]
    return change_theme(fresh)


def changed_from_defaults(theme):
    d = th.default_theme()
    return sum(1 for k, v in d["colors"].items() if theme["colors"].get(k) != v)


def install_desktop_entry(repo_root):
    """Voce nel menu delle applicazioni (rofi, launcher). Percorsi assoluti, nessun comando di shell."""
    apps = os.path.expanduser("~/.local/share/applications")
    os.makedirs(apps, exist_ok=True)
    exe = os.path.join(repo_root, "bin", "camenix")
    icon = os.path.join(repo_root, "app", "assets", "camenix.svg")
    for p in (exe, icon):
        if any(c in p for c in "\n\r\"'`$ ;&|<>"):
            raise files.UnsafeFile(p)
    text = ("[Desktop Entry]\nType=Application\nName=Camenix\nGenericName=Tema del desktop\n"
            "Comment=Sfondo e colori del desktop Hyprland\n"
            f"Exec={exe}\nIcon={icon}\nTerminal=false\nCategories=Settings;DesktopSettings;\n"
            "Keywords=tema;sfondo;colori;wallpaper;theme;\n")
    path = os.path.join(apps, "camenix.desktop")
    files.atomic_write(path, text)
    return path


# ── prima configurazione ─────────────────────────────────
def candidates():
    """File di config noti che contengono colori."""
    c = [os.path.expanduser(p) for p in ("~/.config/hypr/hyprlock.conf", "~/.config/mako/config")]
    c += sorted(glob.glob(os.path.expanduser("~/.config/rofi/*.rasi")))
    for p in sorted(glob.glob(os.path.expanduser("~/.config/hypr/**/*.lua"), recursive=True)) + \
            [os.path.expanduser("~/.config/hypr/hyprland.conf")]:
        try:
            if re.search(r"active_border", files.read_text(p)):
                c.append(p)
        except (files.UnsafeFile, OSError):
            pass
    return [p for p in c if os.path.isfile(p)]


def will_manage():
    """File che Camenix userebbe al primo avvio, con il programma a cui appartengono."""
    out = [{"file": p, "kind": kind(p)} for p in candidates()]
    kitty = os.path.expanduser("~/.config/kitty/kitty.conf")
    if os.path.isfile(kitty) or system.has("kitty"):
        out.append({"file": kitty, "kind": "kitty"})
    if quickshell_target():
        out.append({"file": quickshell_target(), "kind": "quickshell"})
    return out


def first_run():
    """Primo avvio: il tema parte dai colori trovati sul desktop, che restano anche come "colori iniziali";
    poi Camenix collega i file (con copia di sicurezza). -> dict, oppure None se Camenix è già configurato."""
    if os.path.lexists(th.theme_path()):
        return None
    theme, found = detect.detect()
    th.write(theme)
    os.makedirs(th.config_dir(), mode=0o700, exist_ok=True)
    files.atomic_write(original_path(), json.dumps(theme, indent=2, ensure_ascii=False) + "\n", default_mode=0o600)
    actions = setup()
    rep = apply(theme)                                # crea i colori di kitty e avvisa i programmi
    return {"found": found, "setup": actions, "report": rep.as_dict()}


def setup(dry_run=False):
    """-> dict con le azioni fatte (o da fare con dry_run)."""
    actions = {"theme": None, "wallpaper": None, "kitty": None, "adopted": [], "skipped": [], "quickshell": None}
    theme, _, exists = th.read()
    if not exists:
        actions["theme"] = th.theme_path()
    if not theme["wallpaper"]["home"]:
        wp = wallpaper.current()
        if wp and wallpaper.is_image(wp):
            theme["wallpaper"]["home"] = wp
            actions["wallpaper"] = wp
    kitty = os.path.expanduser("~/.config/kitty/kitty.conf")
    if os.path.isfile(kitty):
        try:
            if KITTY_INCLUDE not in files.read_text(kitty):
                actions["kitty"] = kitty
        except files.UnsafeFile:
            actions["skipped"].append(kitty)
    elif not os.path.lexists(kitty) and system.has("kitty"):
        actions["kitty"] = kitty                       # kitty installato senza config: la crea con la sola riga
    state = load_state()
    managed = {f["target"] for f in state["files"]}
    todo = [p for p in candidates() if os.path.realpath(p) not in managed]
    if quickshell_target():
        actions["quickshell"] = quickshell_target()
    if dry_run:
        actions["adopted"] = [{"file": p, "colors": render.adopt(files.read_text(p), theme)[1]} for p in todo]
        return actions

    if actions["theme"] or actions["wallpaper"]:
        th.write(theme)
    if actions["wallpaper"]:
        state["wallpaper"] = actions["wallpaper"]      # è già quello sullo schermo: niente da riavviare
    if actions["kitty"]:
        if os.path.exists(kitty):
            files.backup(kitty, cfg("backups"))
            text = files.read_text(kitty).rstrip("\n") + "\n\n"
        else:
            text = ""
        files.atomic_write(kitty, text + f"{KITTY_MARK}\n{KITTY_INCLUDE}\n")
    for p in todo:
        try:
            files.backup(p, cfg("backups"))
            n = adopt_file(p, theme, state)
        except (files.UnsafeFile, OSError):
            actions["skipped"].append(p)
            continue
        if n:
            actions["adopted"].append({"file": p, "colors": n})
    save_state(state)
    return actions
