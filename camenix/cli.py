"""Comando `camenix` (stile Erinix: un solo comando, --json stabile, uscita 0/1/2)."""
import json
import locale
import os
import sys

from camenix import __version__, theme as th
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
        print(json.dumps({"version": __version__, "path": th.theme_path(), "exists": exists,
                          "theme": theme, "problems": _problems_text(problems)}, ensure_ascii=False))
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


COMMANDS = {"status": cmd_status, "init": cmd_init, "check": cmd_check}


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
