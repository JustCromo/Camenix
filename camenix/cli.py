"""Comando `camenix` (stile Erinix: un solo comando, --json stabile, uscita 0/1/2)."""
import json
import locale
import os
import sys

from camenix import __version__, apply as ap, files, theme as th, wallpaper as wpm
from camenix.i18n import t

USAGE = 2
PROBLEM = 1
OK = 0


class Out:
    """Colori a ruoli; si spengono con NO_COLOR o se l'output non è un terminale."""
    def __init__(self, stream):
        self.s = stream
        try:                                     # terminale senza UTF-8: "è" diventa "?" invece di un crash
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
        self.color = stream.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"
        enc = (getattr(stream, "encoding", None) or locale.getpreferredencoding(False) or "").lower()
        self.utf8 = "utf" in enc

    def role(self, text, role):
        if not self.color:
            return text
        code = {"ok": "32", "err": "31", "warn": "33", "dim": "2", "title": "1"}.get(role, "0")
        return f"\033[{code}m{text}\033[0m"

    def swatch(self, hex_color):
        block = "██" if self.utf8 else "##"
        if not self.color:
            return block
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
        return f"\033[38;2;{r};{g};{b}m{block}\033[0m"

    def line(self, text=""):
        print(text, file=self.s)


def _problems_text(problems):
    return [t(key, **params) for key, params in problems]


def cmd_status(args, out, err):
    try:
        theme, problems, exists = th.read()
    except th.UnsafePath as e:
        return _fail(err, t("err.unsafe_path", path=str(e)), t("err.unsafe_hint"))
    if "--json" in args:
        print(json.dumps({"version": __version__, "path": th.theme_path(), "exists": exists, "theme": theme,
                          "managed": [f["target"] for f in ap.load_state()["files"]],
                          "problems": _problems_text(problems)}, ensure_ascii=False))
        return PROBLEM if problems else OK
    out.line(out.role(t("status.title", name=theme["name"]), "title"))
    out.line(out.role(t("status.file", path=th.theme_path()), "dim"))
    if not exists:
        out.line(t("status.default"))
        out.line(out.role(t("status.hint_init"), "dim"))
    out.line()
    for group in ("base", "derived"):
        out.line(out.role(t(f"group.{group}"), "title"))
        for r in th.roles():
            if r["group"] == group:
                label = t(f"role.{r['key']}") if group == "base" else r["key"]
                out.line(f"  {out.swatch(theme['colors'][r['key']])} {theme['colors'][r['key']]}  {label}")
        out.line()
    managed = [f["target"] for f in ap.load_state()["files"]]
    if managed:
        out.line(out.role(t("status.managed"), "title"))
        for f in managed:
            out.line(f"  {f}")
        out.line()
    if problems:
        out.line(out.role(t("status.problems", n=len(problems)), "warn"))
        for p in _problems_text(problems):
            out.line(f"  - {p}")
        return PROBLEM
    return OK


def cmd_init(args, out, err):
    path = th.theme_path()
    if os.path.lexists(path) and "--force" not in args:
        return _fail(err, t("init.exists", path=path), t("init.exists_hint"), code=PROBLEM)
    try:
        th.write(th.default_theme(), path)
    except th.UnsafePath:
        return _fail(err, t("err.unsafe_path", path=path), t("err.unsafe_hint"))
    except OSError as e:
        return _fail(err, t("err.write", reason=e.strerror or str(e)), t("err.write_hint"))
    if "--json" in args:
        print(json.dumps({"ok": True, "path": path}))
    else:
        out.line(out.role(t("init.done", path=path), "ok"))
    return OK


def cmd_check(args, out, err):
    try:
        _, problems, _ = th.read()
    except th.UnsafePath as e:
        return _fail(err, t("err.unsafe_path", path=str(e)), t("err.unsafe_hint"))
    if "--json" in args:
        print(json.dumps({"ok": not problems, "problems": _problems_text(problems)}, ensure_ascii=False))
    elif problems:
        out.line(out.role(t("check.bad", n=len(problems)), "warn"))
        for p in _problems_text(problems):
            out.line(f"  - {p}")
    else:
        out.line(out.role(t("check.ok"), "ok"))
    return PROBLEM if problems else OK


def _fail(err, message, hint, code=USAGE):
    err.line(err.role(message, "err"))
    err.line(err.role(hint, "dim"))
    return code


def _print_report(rep, args, out, err, changed=False):
    if "--json" in args:
        print(json.dumps(rep.as_dict(), ensure_ascii=False))
    else:
        for c in rep.conflicts:
            err.line(err.role(t("apply.conflict", file=c["file"]), "err"))
            err.line(err.role(t("apply.conflict_hint", file=c["file"]), "dim"))
        for e in rep.errors:
            err.line(err.role(t("apply.error", file=e["file"], why=e["why"]), "err"))
            err.line(err.role(t("apply.error_hint", file=e["file"]), "dim"))
        if not (rep.conflicts or rep.errors):
            for f in rep.written:
                out.line("  " + t("apply.written", file=f))
            for r in rep.reloaded:
                out.line("  " + t("apply.reloaded", what=r))
            if rep.wallpaper:
                key = "apply.wallpaper" if rep.wallpaper["ok"] else "apply.wallpaper_fail"
                out.line("  " + t(key, path=rep.wallpaper["path"]))
            done = changed or rep.written or rep.reloaded or rep.wallpaper
            out.line(out.role(t("apply.ok") if done else t("apply.nothing"), "ok"))
    return PROBLEM if (rep.conflicts or rep.errors) else OK


def cmd_apply(args, out, err):
    rep = ap.apply(dry_run="--dry-run" in args)
    return _print_report(rep, args, out, err)


def _warn_changed(out, err):
    n = ap.changed_from_defaults(th.read()[0])
    if n:
        err.line(err.role(t("warn.theme_changed", n=n), "warn"))
        err.line(err.role(t("warn.theme_changed_hint"), "dim"))
    return n


def cmd_setup(args, out, err):
    dry = "--dry-run" in args
    if "--json" not in args:
        _warn_changed(out, err)
    act = ap.setup(dry_run=dry)
    if "--json" in args:
        print(json.dumps(act, ensure_ascii=False))
        return OK
    out.line(out.role(t("setup.title"), "title"))
    if act["theme"]:
        out.line("  " + t("setup.theme", path=act["theme"]))
    if act["wallpaper"]:
        out.line("  " + t("setup.wallpaper", path=act["wallpaper"]))
    if act["kitty"]:
        out.line("  " + t("setup.kitty"))
    for a in act["adopted"]:
        if a["colors"]:
            out.line("  " + t("setup.would_adopt" if dry else "setup.adopted", file=a["file"], n=a["colors"]))
        else:
            out.line(out.role("  " + t("setup.nothing", file=a["file"]), "dim"))
    for f in act["skipped"]:
        out.line(out.role("  " + t("setup.skipped", file=f), "warn"))
    if act["quickshell"]:
        out.line("  " + t("setup.quickshell"))
    out.line(out.role(t("setup.dry") if dry else t("setup.backups", path=ap.cfg("backups")), "dim"))
    if not dry:
        out.line(out.role(t("setup.next"), "ok"))
    return OK


def cmd_set(args, out, err):
    pos = [a for a in args if not a.startswith("--")]
    if len(pos) != 2:
        return _fail(err, t("err.usage", cmd="set"), t("set.bad_role_hint"))
    role, color = pos
    theme, _, _ = th.read()
    target = theme["terminal"] if role.startswith("terminal.") else theme["colors"]
    key = role.split(".", 1)[1] if role.startswith("terminal.") else role
    if key not in target:
        return _fail(err, t("set.bad_role", role=role[:40]), t("set.bad_role_hint"))
    if not th.HEX.match(color):
        return _fail(err, t("set.bad_color", color=color[:20]), t("set.bad_color_hint"))
    target[key] = color.upper()
    return _print_report(ap.change_theme(theme), args, out, err, changed=True)


def cmd_wallpaper(args, out, err):
    pos = [a for a in args if not a.startswith("--")]
    theme, _, _ = th.read()
    if pos[:1] == ["set"] and len(pos) == 2:
        path = os.path.realpath(os.path.expanduser(pos[1]))
        if not wpm.is_image(path) or not th._valid_wallpaper(path):
            return _fail(err, t("wallpaper.bad", path=pos[1][:200]), t("wallpaper.bad_hint"))
        theme["wallpaper"]["home"] = path
        return _print_report(ap.change_theme(theme), args, out, err, changed=True)
    path = theme["wallpaper"]["home"]                # avvio: mostra lo sfondo del tema
    if not path:
        return _fail(err, t("wallpaper.none"), t("wallpaper.none_hint"), code=PROBLEM)
    ok, backend = wpm.set_wallpaper(path)
    if "--json" in args:
        print(json.dumps({"ok": ok, "path": path, "backend": backend}))
    elif ok:
        out.line(t("apply.wallpaper", path=path))
    else:
        return _fail(err, t("apply.wallpaper_fail", path=path), t("wallpaper.bad_hint"), code=PROBLEM)
    return OK if ok else PROBLEM


def cmd_undo(args, out, err):
    rep = ap.undo()
    if rep is None:
        return _fail(err, t("undo.empty"), t("undo.empty_hint"), code=PROBLEM)
    return _print_report(rep, args, out, err, changed=True)


def cmd_adopt(args, out, err):
    pos = [a for a in args if not a.startswith("--")]
    if len(pos) != 1:
        return _fail(err, t("err.usage", cmd="adopt"), t("adopt.unsafe_hint"))
    _warn_changed(out, err)
    theme, _, _ = th.read()
    state = ap.load_state()
    try:
        files.backup(pos[0], ap.cfg("backups"))
        n = ap.adopt_file(pos[0], theme, state)
    except (files.UnsafeFile, OSError):
        return _fail(err, t("adopt.unsafe", file=pos[0][:200]), t("adopt.unsafe_hint"))
    ap.save_state(state)
    if n:
        out.line(out.role(t("adopt.done", file=pos[0], n=n), "ok"))
        return OK
    return _fail(err, t("adopt.none", file=pos[0]), t("adopt.none_hint"), code=PROBLEM)


def cmd_forget(args, out, err):
    pos = [a for a in args if not a.startswith("--")]
    if len(pos) != 1:
        return _fail(err, t("err.usage", cmd="forget"), t("forget.none_hint"))
    state = ap.load_state()
    if ap.forget_file(pos[0], state):
        ap.save_state(state)
        out.line(out.role(t("forget.done", file=pos[0]), "ok"))
        return OK
    return _fail(err, t("forget.none", file=pos[0][:200]), t("forget.none_hint"), code=PROBLEM)


def _draft_arg(args, err):
    pos = [a for a in args if not a.startswith("--")]
    return pos[0] if len(pos) == 1 else None


def cmd_derive(args, out, err):
    path = _draft_arg(args, err)
    try:
        print(json.dumps(ap.derive_draft(path), ensure_ascii=False))
        return OK
    except (TypeError, files.UnsafeFile, OSError, ValueError):
        print(json.dumps({"ok": False}))
        return USAGE


def cmd_apply_file(args, out, err):
    path = _draft_arg(args, err)
    try:
        draft = ap.read_draft(path)
    except (TypeError, files.UnsafeFile, OSError, ValueError):
        print(json.dumps({"ok": False, "conflicts": [], "errors": [{"file": "draft", "why": "invalid"}]}))
        return USAGE
    return _print_report(ap.change_theme(draft), args + ["--json"], out, err, changed=True)


def cmd_import(args, out, err):
    path = _draft_arg(args, err)
    dest = ap.import_wallpaper(path) if path else None
    print(json.dumps({"ok": bool(dest), "path": dest}))
    return OK if dest else PROBLEM


def cmd_reset_colors(args, out, err):
    rep = ap.reset_colors()
    if "--json" not in args and rep.as_dict()["ok"]:
        out.line(out.role(t("reset.done"), "ok"))
        return OK
    return _print_report(rep, args, out, err, changed=True)


def cmd_install(args, out, err):
    root = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
    path = ap.install_desktop_entry(root)
    print(json.dumps({"ok": True, "desktop": path}) if "--json" in args else path)
    return OK


COMMANDS = {"derive": cmd_derive, "apply-file": cmd_apply_file, "import-wallpaper": cmd_import,
            "reset-colors": cmd_reset_colors, "install": cmd_install,
            "status": cmd_status, "init": cmd_init, "check": cmd_check, "setup": cmd_setup, "apply": cmd_apply,
            "set": cmd_set, "wallpaper": cmd_wallpaper, "undo": cmd_undo, "adopt": cmd_adopt, "forget": cmd_forget}


def main(argv):
    try:
        return _main(argv)
    except BrokenPipeError:                      # es. `camenix status | head`
        try:
            sys.stdout = open(os.devnull, "w")
        except OSError:
            pass
        return OK
    except KeyboardInterrupt:
        return PROBLEM


def _main(argv):
    out, err = Out(sys.stdout), Out(sys.stderr)
    if argv and argv[0] in ("--version", "-V"):
        print(__version__)
        return OK
    cmd = argv[0] if argv and not argv[0].startswith("-") else "status"
    args = argv[1:] if argv and not argv[0].startswith("-") else argv
    if cmd not in COMMANDS:
        safe = "".join(ch for ch in cmd if ch.isprintable())[:40]
        return _fail(err, t("err.usage", cmd=safe), t("err.usage_hint"))
    return COMMANDS[cmd](args, out, err)
