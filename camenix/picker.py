"""Finestra per scegliere un'immagine (zenity o kdialog), sempre in primo piano.

Su Hyprland una finestra nuova può finire dietro: se l'app è flottante o a tutto schermo, la finestra di
scelta (che di base si affianca) resta sotto e non si vede. Appena compare, la facciamo diventare
flottante, centrata, in primo piano e attiva. Si tocca solo la finestra del processo che abbiamo
avviato noi (riconosciuta dal suo pid), nient'altro."""
import json
import os
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


def bring_to_front(pid, tries=60, wait=0.1, sleep=time.sleep):
    """Aspetta che la finestra del processo `pid` compaia e la porta davanti a tutto. -> True se trovata."""
    for _ in range(tries):
        ok, out = system.run(["hyprctl", "clients", "-j"])
        try:
            clients = json.loads(out) if ok else []
        except ValueError:
            clients = []
        for c in clients if isinstance(clients, list) else []:
            if isinstance(c, dict) and c.get("pid") == pid:
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


def pick(title):
    """-> {"ok": bool, "path": str, "why": ""|"cancel"|"no-picker"}"""
    argv = command(title)
    if not argv:
        return {"ok": False, "path": "", "why": "no-picker"}
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True)
    except OSError:
        return {"ok": False, "path": "", "why": "no-picker"}
    watcher = threading.Thread(target=bring_to_front, args=(proc.pid,), daemon=True)
    watcher.start()
    out, _ = proc.communicate()
    watcher.join(timeout=0.5)                    # (se la finestra non è mai comparsa, non si aspetta oltre)
    path = (out or "").strip().splitlines()[0] if (out or "").strip() else ""
    if proc.returncode != 0 or not path:
        return {"ok": False, "path": "", "why": "cancel"}
    return {"ok": True, "path": path, "why": ""}
