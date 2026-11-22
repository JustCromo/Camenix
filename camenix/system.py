"""Programmi in esecuzione e comandi esterni (sempre con argv fisso, mai tramite shell)."""
import os
import shutil
import subprocess


def own_processes(name):
    """[(pid, argv)] dei processi dell'utente corrente con quel nome (letti da /proc, niente pgrep)."""
    out = []
    uid = os.getuid()
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return out
    for pid in pids:
        try:
            if os.stat(f"/proc/{pid}").st_uid != uid:
                continue
            with open(f"/proc/{pid}/comm", encoding="utf-8", errors="replace") as f:
                if f.read().strip() != name:
                    continue
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                argv = [a.decode("utf-8", "surrogateescape") for a in f.read().split(b"\0") if a]
            out.append((int(pid), argv))
        except OSError:
            continue
    return out


def has(program):
    return shutil.which(program) is not None


def run(argv, timeout=10):
    """-> (ok, output). Non solleva eccezioni: un programma che manca o fallisce è solo 'non ok'."""
    if not argv or not has(argv[0]):
        return False, ""
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        return r.returncode == 0, r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return False, ""


def spawn(argv):
    """Avvia un programma staccato (sopravvive a Camenix)."""
    if not argv or not has(argv[0]):
        return False
    try:
        subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except OSError:
        return False


def signal_own(name, sig):
    import signal as _s
    n = 0
    for pid, _ in own_processes(name):
        try:
            os.kill(pid, getattr(_s, sig))
            n += 1
        except OSError:
            pass
    return n
