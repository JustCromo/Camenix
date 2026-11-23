"""Finestra per scegliere un'immagine (zenity o kdialog), sempre in primo piano.

Su Hyprland una finestra nuova può finire dietro: se l'app è flottante o a tutto schermo, la finestra di
scelta (che di base si affianca) resta sotto e non si vede. Appena compare, la facciamo diventare
flottante, centrata, in primo piano e attiva. Si tocca solo la finestra del processo che abbiamo
avviato noi (riconosciuta dal suo pid), nient'altro."""
import ctypes
import json
import os
import signal
import subprocess
import threading
import time

from camenix import system

FILTER = "PNG, JPEG, WebP | *.png *.jpg *.jpeg *.webp *.PNG *.JPG *.JPEG *.WEBP"


def _clean_title(title):
    return "".join(ch for ch in (title or "") if ch.isprintable())[:80] or "Camenix"


def command(title):
    """-> argv del programma per scegliere un file, o None se non ce n'è nessuno."""
    t = _clean_title(title)
    if system.has("zenity"):
        return ["zenity", "--file-selection", "--title", t, "--file-filter", FILTER]
    if system.has("kdialog"):
        return ["kdialog", "--title", t, "--getopenfilename", os.path.expanduser("~"), "image/png image/jpeg image/webp"]
    return None


def _ours(c, pid, title):
    """La finestra è quella che abbiamo aperto noi? Stesso pid, oppure stesso titolo e programma di scelta
    file (quando la finestra la apre un altro processo)."""
    if c.get("pid") == pid:
        return True
    # zenity e kdialog spesso chiedono la finestra al "portale" del desktop (xdg-desktop-portal-gtk/kde):
    # allora la finestra è del portale, con il nostro titolo
    cls = str(c.get("class", "")).lower()
    return bool(title) and c.get("title") == title and any(k in cls for k in ("zenity", "kdialog", "xdg-desktop-portal"))


def bring_to_front(pid, tries=60, wait=0.1, sleep=time.sleep, title=""):
    """Aspetta che la finestra del processo `pid` compaia e la porta davanti a tutto. -> True se trovata."""
    for _ in range(tries):
        ok, out = system.run(["hyprctl", "clients", "-j"])
        try:
            clients = json.loads(out) if ok else []
        except ValueError:
            clients = []
        for c in clients if isinstance(clients, list) else []:
            if isinstance(c, dict) and _ours(c, pid, title):
                addr = str(c.get("address", ""))
                if not addr.startswith("0x") or not all(ch in "0123456789abcdefx" for ch in addr.lower()):
                    return False
                steps = [f"dispatch focuswindow address:{addr}"]
                if not c.get("floating"):
                    steps.append(f"dispatch setfloating address:{addr}")
                steps += [f"dispatch resizewindowpixel exact 960 640,address:{addr}",
                          "dispatch centerwindow",
                          f"dispatch alterzorder top,address:{addr}"]
                system.run(["hyprctl", "--batch", " ; ".join(steps)])
                return True
        sleep(wait)
    return False


PR_SET_PDEATHSIG = 1


def _die_with_parent():
    """Linux: se il processo che ci ha avviato muore, riceviamo SIGTERM (così niente finestre orfane)."""
    try:
        ctypes.CDLL(None, use_errno=True).prctl(PR_SET_PDEATHSIG, signal.SIGTERM, 0, 0, 0)
    except (OSError, AttributeError):
        pass


def child_env():
    """zenity/kdialog disegnano la finestra da soli invece di chiederla al portale del desktop:
    così è davvero loro (pid giusto) e si chiude con loro."""
    env = dict(os.environ)
    env["GTK_USE_PORTAL"] = "0"                       # GTK 3
    env["GDK_DEBUG"] = "no-portals"                   # GTK 4
    return env


def pick(title):
    """-> {"ok": bool, "path": str, "why": ""|"cancel"|"no-picker"}"""
    argv = command(title)
    if not argv:
        return {"ok": False, "path": "", "why": "no-picker"}
    _die_with_parent()                                # Camenix chiusa -> il motore se ne va...
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True, env=child_env(),
                                preexec_fn=_die_with_parent)          # ...e con lui la finestra di scelta
    except OSError:
        return {"ok": False, "path": "", "why": "no-picker"}

    def stop(signum, frame):
        proc.terminate()
        os._exit(1)
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, stop)
    watcher = threading.Thread(target=bring_to_front, args=(proc.pid,), kwargs={"title": _clean_title(title)}, daemon=True)
    watcher.start()
    out, _ = proc.communicate()
    watcher.join(timeout=0.5)                    # (se la finestra non è mai comparsa, non si aspetta oltre)
    path = (out or "").strip().splitlines()[0] if (out or "").strip() else ""
    if proc.returncode != 0 or not path:
        return {"ok": False, "path": "", "why": "cancel"}
    return {"ok": True, "path": path, "why": ""}
