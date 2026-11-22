"""Sfondo: legge quello in uso e lo cambia con il programma disponibile (swww, hyprpaper, swaybg)."""
import os
import re

from camenix import files, system

MAGIC = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")
MAX_IMAGE_BYTES = 64 * 1024 * 1024


def is_image(path):
    """File normale, leggibile, con l'intestazione di un PNG, JPEG o WebP."""
    try:
        if not os.path.isfile(path) or os.path.getsize(path) > MAX_IMAGE_BYTES:
            return False
        with open(path, "rb") as f:
            head = f.read(12)
    except OSError:
        return False
    return head.startswith(MAGIC) or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")


def current():
    """Percorso dello sfondo attuale, se si riesce a capirlo."""
    for _, argv in system.own_processes("swaybg"):
        for i, a in enumerate(argv):
            if a in ("-i", "--image") and i + 1 < len(argv):
                return os.path.realpath(os.path.expanduser(argv[i + 1]))
    conf = os.path.expanduser("~/.config/hypr/hyprpaper.conf")
    try:
        for line in files.read_text(conf).splitlines():
            m = re.match(r"\s*wallpaper\s*=\s*[^,]*,\s*(.+?)\s*$", line)
            if m:
                return os.path.realpath(os.path.expanduser(m.group(1)))
    except (files.UnsafeFile, OSError):
        pass
    ok, out = system.run(["swww", "query"])
    if ok:
        m = re.search(r"image:\s*(\S.*)$", out, re.M)
        if m:
            return m.group(1).strip()
    return None


def backend():
    if system.own_processes("swww-daemon"):
        return "swww"
    if system.own_processes("hyprpaper"):
        return "hyprpaper"
    if system.has("swaybg"):
        return "swaybg"
    if system.has("swww"):
        return "swww"
    return None


def set_wallpaper(path):
    """-> (ok, backend). Il percorso deve essere un'immagine vera e assoluta."""
    if not os.path.isabs(path) or not is_image(path):
        return False, None
    b = backend()
    if b == "swww":
        if not system.own_processes("swww-daemon"):
            system.spawn(["swww-daemon"])
        ok, _ = system.run(["swww", "img", path, "--transition-type", "fade"])
        return ok, b
    if b == "hyprpaper":
        ok, _ = system.run(["hyprctl", "hyprpaper", "reload", "," + path])
        return ok, b
    if b == "swaybg":
        system.signal_own("swaybg", "SIGTERM")
        return system.spawn(["swaybg", "-i", path, "-m", "fill"]), b
    return False, None
