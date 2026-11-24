"""Sfondo della schermata di accesso (SDDM e simili).

Il gestore di accesso gira con un suo utente e non può leggere la home. Quindi, una sola volta e con
sudo, l'utente crea una cartella pubblica di sua proprietà (/var/lib/camenix) e indica al tema di
accesso di prendere lo sfondo da lì. Da quel momento Camenix ci copia lo sfondo a ogni applicazione,
senza permessi di amministratore. Se la cartella non c'è, non succede nulla.

Sicurezza: si scrive solo se la cartella è una cartella vera (non un collegamento), è dell'utente e
nessun altro può scriverci. La copia è atomica (file temporaneo + rename dentro la cartella) e un
collegamento lasciato al posto del file viene sostituito, mai seguito."""
import hashlib
import os
import secrets
import stat

from camenix import wallpaper

DIR = "/var/lib/camenix"
NAME = "login-wallpaper"


def target():
    return os.path.join(DIR, NAME)


def _open_dir():
    """-> descrittore della cartella se è sicura, altrimenti None."""
    try:
        fd = os.open(DIR, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError:
        return None
    st = os.fstat(fd)
    if st.st_uid != os.getuid() or st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        os.close(fd)
        return None
    return fd


def enabled():
    fd = _open_dir()
    if fd is None:
        return False
    os.close(fd)
    return True


def _digest_fd(fd):
    h = hashlib.sha256()
    for block in iter(lambda: os.read(fd, 1 << 20), b""):
        h.update(block)
    return h.hexdigest()


def sync(image):
    """Copia `image` come sfondo di accesso. -> "copied", "same", "off" (cartella assente o non sicura)
    oppure "bad" (non è un'immagine valida o la copia non è riuscita)."""
    fd = _open_dir()
    if fd is None:
        return "off"
    tmp = None
    try:
        if not image or not os.path.isabs(image) or not wallpaper.is_image(image):
            return "bad"
        src = os.open(image, os.O_RDONLY | os.O_CLOEXEC)
        try:
            data = b"".join(iter(lambda: os.read(src, 1 << 20), b""))
        finally:
            os.close(src)
        if len(data) > wallpaper.MAX_IMAGE_BYTES:
            return "bad"
        try:
            old = os.open(NAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            try:
                if stat.S_ISREG(os.fstat(old).st_mode) and _digest_fd(old) == hashlib.sha256(data).hexdigest():
                    return "same"
            finally:
                os.close(old)
        except OSError:
            pass
        tmp = f".{NAME}.{secrets.token_hex(6)}"
        out = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o644, dir_fd=fd)
        try:
            os.fchmod(out, 0o644)
            view = memoryview(data)
            while view:
                view = view[os.write(out, view):]
            os.fsync(out)
        finally:
            os.close(out)
        os.replace(tmp, NAME, src_dir_fd=fd, dst_dir_fd=fd)
        tmp = None
        return "copied"
    except OSError:
        return "bad"
    finally:
        if tmp:
            try:
                os.unlink(tmp, dir_fd=fd)
            except OSError:
                pass
        os.close(fd)


def image_for(theme):
    """Lo sfondo della schermata di blocco (o quello del desktop, se il blocco usa lo stesso)."""
    wp = theme.get("wallpaper", {}) if isinstance(theme, dict) else {}
    home = wp.get("home")
    return home if wp.get("lock_same", True) or not wp.get("lock") else wp.get("lock")
