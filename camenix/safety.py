"""Paracadute e dissolvenza.

Paracadute: dopo "Applica" il motore lancia un piccolo guardiano staccato dall'app. Se entro il tempo
nessuno dice "tieni", il guardiano torna al tema di prima, anche se l'app è stata chiusa o si è bloccata
(come le impostazioni dello schermo). Chi arriva primo tra "tieni" e il guardiano "prende" l'attesa
con un rename atomico: non possono vincere tutti e due.

Dissolvenza: prima di applicare si fotografa ogni monitor con grim nella cartella privata della sessione
($XDG_RUNTIME_DIR/camenix, 0700); l'app mette le foto sopra a tutto e le sfuma. Poi si cancellano."""
import json
import os
import re
import secrets
import stat
import sys
import time

from camenix import files, system, theme as th

GUARD_SECONDS = 16          # un secondo in più dei 15 dell'app: decide prima la persona
TOKEN = re.compile(r"^[0-9a-f]{32}$")
OUTPUT = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def pending_path():
    return os.path.join(th.config_dir(), "pending.json")


def arm(seconds=GUARD_SECONDS, spawn=True):
    """Dopo un "Applica" riuscito: segna l'attesa e lancia il guardiano. -> token."""
    token = secrets.token_hex(16)
    files.atomic_write(pending_path(), json.dumps({"token": token, "deadline": time.time() + seconds}) + "\n",
                       default_mode=0o600)
    if spawn:
        engine = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "bin", "camenix-engine")
        system.spawn([sys.executable, engine, "guard", token])
    return token


def _take():
    """Prende l'attesa (una volta sola). -> dati dell'attesa, o None se non c'era o l'ha presa un altro."""
    src = pending_path()
    taken = src + f".{os.getpid()}.taken"
    try:
        os.rename(src, taken)
    except OSError:
        return None
    try:
        return json.loads(files.read_text(taken, limit=4096))
    except (files.UnsafeFile, OSError, ValueError):
        return None
    finally:
        try:
            os.unlink(taken)
        except OSError:
            pass


def keep():
    """La persona ha detto "tieni": il guardiano non farà niente. -> True se c'era un'attesa."""
    return _take() is not None


def guard(token, undo, sleep=time.sleep):
    """Il guardiano: aspetta la scadenza e, se l'attesa è ancora la sua, torna indietro."""
    if not TOKEN.match(token or ""):
        return False
    try:
        data = json.loads(files.read_text(pending_path(), limit=4096))
        wait = max(0.0, min(60.0, float(data.get("deadline", 0)) - time.time()))
    except (files.UnsafeFile, OSError, ValueError, TypeError):
        return False
    sleep(wait)
    try:                                           # ancora la stessa attesa? (non un "Applica" più recente)
        if json.loads(files.read_text(pending_path(), limit=4096)).get("token") != token:
            return False
    except (files.UnsafeFile, OSError, ValueError, AttributeError):
        return False
    data = _take()
    if not data:
        return False
    if data.get("token") != token:                 # nel frattempo è arrivato un "Applica" nuovo: la rimetto
        files.atomic_write(pending_path(), json.dumps(data) + "\n", default_mode=0o600)
        return False
    undo()
    return True


# ── dissolvenza ──────────────────────────────────────────
def runtime_dir():
    """Cartella privata della sessione per le foto, o None se non è sicura."""
    base = os.environ.get("XDG_RUNTIME_DIR", "")
    if not base or not os.path.isabs(base):
        return None
    d = os.path.join(base, "camenix")
    try:
        os.makedirs(d, mode=0o700, exist_ok=True)
        st = os.lstat(d)
    except OSError:
        return None
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        return None                                # link, di un altro, o leggibile da altri: no
    return d


def outputs():
    ok, out = system.run(["hyprctl", "monitors", "-j"])
    try:
        names = [m.get("name", "") for m in json.loads(out)] if ok else []
    except (ValueError, AttributeError, TypeError):
        names = []
    return [n for n in names if isinstance(n, str) and OUTPUT.match(n)][:8]


def snapshot():
    """Foto di ogni monitor. -> {"ok": bool, "shots": [{"name", "path"}]}"""
    d = runtime_dir()
    if not d or not system.has("grim"):
        return {"ok": False, "shots": []}
    clean()
    shots = []
    for name in outputs():
        path = os.path.join(d, f"fade-{name}.png")
        ok, _ = system.run(["grim", "-l", "0", "-o", name, path], timeout=5)
        if ok and os.path.isfile(path) and not os.path.islink(path):
            os.chmod(path, 0o600)
            shots.append({"name": name, "path": path})
    return {"ok": bool(shots), "shots": shots}


def clean():
    d = runtime_dir()
    if not d:
        return 0
    n = 0
    for f in os.listdir(d):
        if f.startswith("fade-") and f.endswith(".png"):
            try:
                os.unlink(os.path.join(d, f))
                n += 1
            except OSError:
                pass
    return n
