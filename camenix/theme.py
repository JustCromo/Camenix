"""Formato del tema di Camenix: lettura sicura, validazione e scrittura atomica.

Il tema vive in ~/.config/camenix/theme.json:
  {"format": "camenix-theme", "version": 1, "name": "...",
   "colors": {"text": "#1E1528", ...},
   "wallpaper": {"home": null|"/percorso", "lock": null|"/percorso", "lock_same": true, "lock_blur": true}}

Regola d'oro: un tema rotto non deve mai rompere il desktop. Ogni valore non valido
viene sostituito con quello predefinito e segnalato come "problema"."""
import json
import os
import re
import stat
import tempfile
from importlib import resources

FORMAT = "camenix-theme"
VERSION = 1
MAX_BYTES = 64 * 1024
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
WALLPAPER_KEYS = ("home", "lock")
# terminale: valori predefiniti di kitty, con lo sfondo nero che usi ora
TERMINAL_DEFAULTS = {
    "background": "#000000", "foreground": "#DDDDDD", "cursor": "#CCCCCC",
    "selection_background": "#FFFACD", "selection_foreground": "#000000",
    "color0": "#000000", "color1": "#CC0403", "color2": "#19CB00", "color3": "#CECB00",
    "color4": "#0D73CC", "color5": "#CB1ED1", "color6": "#0DCDCD", "color7": "#DDDDDD",
    "color8": "#767676", "color9": "#F2201F", "color10": "#23FD00", "color11": "#FFFD00",
    "color12": "#1A8FFF", "color13": "#FD28FF", "color14": "#14FFFF", "color15": "#FFFFFF",
}
WALLPAPER_EXT = (".png", ".jpg", ".jpeg", ".webp")


def config_dir():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "camenix")


def theme_path():
    return os.path.join(config_dir(), "theme.json")


def roles():
    data = json.loads(resources.files("camenix.data").joinpath("roles.json").read_text(encoding="utf-8"))
    return data["roles"]


def defaults():
    return {r["key"]: r["default"].upper() for r in roles()}


def default_theme(name="Gudetama"):
    return {"format": FORMAT, "version": VERSION, "name": name, "colors": defaults(),
            "terminal": dict(TERMINAL_DEFAULTS),
            "wallpaper": {"home": None, "lock": None, "lock_same": True, "lock_blur": True}}


def _valid_wallpaper(value):
    """Percorso assoluto di un'immagine, senza caratteri di controllo: finisce dentro altre config
    (es. hyprlock), quindi un "a capo" nel nome potrebbe iniettare righe nuove."""
    if value is None:
        return True
    return (isinstance(value, str) and 0 < len(value) < 4096 and os.path.isabs(value)
            and not re.search(r"[\x00-\x1f\x7f]", value) and value.lower().endswith(WALLPAPER_EXT))


def normalize(data):
    """Dato qualsiasi (anche ostile) -> (tema completo e valido, lista di problemi).
    I problemi sono tuple (chiave_testo, parametri) da tradurre con i18n.t."""
    problems = []
    theme = default_theme()
    if not isinstance(data, dict):
        return theme, [("problem.not_object", {})]
    if data.get("format") != FORMAT or data.get("version") != VERSION:
        problems.append(("problem.bad_format", {}))
    name = data.get("name")
    if isinstance(name, str) and name.strip():
        theme["name"] = re.sub(r"[\x00-\x1f\x7f]", "", name.strip())[:60] or theme["name"]
    colors = data.get("colors") if isinstance(data.get("colors"), dict) else {}
    known = theme["colors"]
    for key, value in colors.items():
        if key not in known:
            problems.append(("problem.unknown_role", {"role": str(key)[:40]}))
        elif isinstance(value, str) and HEX.match(value):
            known[key] = value.upper()
        else:
            problems.append(("problem.bad_color", {"role": key}))
    term = data.get("terminal") if isinstance(data.get("terminal"), dict) else {}
    for key, value in term.items():
        if key not in theme["terminal"]:
            problems.append(("problem.unknown_role", {"role": "terminal." + str(key)[:30]}))
        elif isinstance(value, str) and HEX.match(value):
            theme["terminal"][key] = value.upper()
        else:
            problems.append(("problem.bad_color", {"role": "terminal." + key}))
    wp = data.get("wallpaper") if isinstance(data.get("wallpaper"), dict) else {}
    for key in WALLPAPER_KEYS:
        if key in wp and wp[key] is not None:
            if _valid_wallpaper(wp[key]):
                theme["wallpaper"][key] = wp[key]
            else:
                problems.append(("problem.bad_wallpaper", {"key": key}))
    for key in ("lock_same", "lock_blur"):
        if isinstance(wp.get(key), bool):
            theme["wallpaper"][key] = wp[key]
    return theme, problems


class UnsafePath(Exception):
    pass


def read(path=None):
    """-> (tema, problemi, esiste). Non segue collegamenti e non legge file enormi."""
    path = path or theme_path()
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return default_theme(), [], False
    if not stat.S_ISREG(st.st_mode):
        raise UnsafePath(path)
    if st.st_size > MAX_BYTES:
        return default_theme(), [("problem.too_big", {})], True
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read(MAX_BYTES + 1)
    try:
        data = json.loads(raw)
    except ValueError:
        return default_theme(), [("problem.not_json", {})], True
    theme, problems = normalize(data)
    return theme, problems, True


def write(theme, path=None):
    """Scrittura atomica: file temporaneo nella stessa cartella, poi rename (mai a metà)."""
    path = path or theme_path()
    theme, _ = normalize(theme)
    folder = os.path.dirname(path)
    os.makedirs(folder, mode=0o700, exist_ok=True)
    try:
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode):
            raise UnsafePath(path)
    except FileNotFoundError:
        pass
    fd, tmp = tempfile.mkstemp(prefix=".theme-", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(theme, f, indent=2, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return theme
