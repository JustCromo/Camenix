"""Lettura e scrittura sicura dei file dell'utente.

- Solo file normali dentro la home, di proprietà dell'utente (anche se raggiunti da un collegamento,
  come con GNU Stow: si scrive sul file vero, mai fuori dalla home).
- Scrittura atomica (file temporaneo + rename) che conserva i permessi originali.
- Copia di sicurezza prima della prima modifica."""
import hashlib
import os
import shutil
import stat
import tempfile
import time

MAX_CONFIG_BYTES = 1024 * 1024


class UnsafeFile(Exception):
    """Il percorso non è un file su cui Camenix può lavorare in sicurezza."""


def home():
    return os.path.realpath(os.path.expanduser("~"))


def inside_home(path):
    h = home()
    return path == h or path.startswith(h + os.sep)


def resolve(path, must_exist=True):
    """Percorso reale e sicuro, oppure UnsafeFile."""
    real = os.path.realpath(os.path.expanduser(path))
    if not inside_home(real):
        raise UnsafeFile(path)
    try:
        st = os.stat(real)
    except FileNotFoundError:
        if must_exist:
            raise UnsafeFile(path)
        return real
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
        raise UnsafeFile(path)
    return real


def read_text(path, limit=MAX_CONFIG_BYTES):
    real = resolve(path)
    if os.path.getsize(real) > limit:
        raise UnsafeFile(path)
    with open(real, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
        return f.read()


def atomic_write(path, text, default_mode=0o644):
    real = resolve(path, must_exist=False)
    folder = os.path.dirname(real)
    os.makedirs(folder, exist_ok=True)
    try:
        mode = stat.S_IMODE(os.stat(real).st_mode)
    except FileNotFoundError:
        mode = default_mode
    fd, tmp = tempfile.mkstemp(prefix=".camenix-", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, real)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return real


def sha256(text):
    return hashlib.sha256(text.encode("utf-8", errors="surrogateescape")).hexdigest()


def backup(path, backups_dir, stamp=None):
    """Copia il file in backups_dir/<data>/<percorso relativo alla home>. Restituisce la copia."""
    real = resolve(path)
    stamp = stamp or time.strftime("%Y%m%d-%H%M%S")
    rel = os.path.relpath(real, home())
    dest = os.path.join(backups_dir, stamp, rel)
    os.makedirs(os.path.dirname(dest), mode=0o700, exist_ok=True)
    os.chmod(backups_dir, 0o700)
    shutil.copy2(real, dest)
    return dest
