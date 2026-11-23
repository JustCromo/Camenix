"""Finestra di scelta dell'immagine: risultato, annullamento, mancanza del programma, primo piano."""
import json
import os
import stat
import tempfile
import unittest

from camenix import picker, system


class TestPicker(unittest.TestCase):
    def setUp(self):
        self.bin = tempfile.mkdtemp()
        self.old = (os.environ.get("PATH", ""), system.run, system.has)
        os.environ["PATH"] = self.bin
        self.calls = []
        self.addCleanup(self.restore)

    def restore(self):
        os.environ["PATH"], system.run, system.has = self.old

    def fake(self, name, body):
        p = os.path.join(self.bin, name)
        with open(p, "w") as f:
            f.write("#!/bin/sh\n" + body + "\n")
        os.chmod(p, stat.S_IRWXU)

    def test_choose_and_bring_to_front(self):
        self.fake("zenity", 'sleep 0.3; echo "/home/x/sfondo.png"')
        pid = {}

        def run(argv, timeout=10):
            self.calls.append(argv)
            if argv[:2] == ["hyprctl", "clients"]:
                # la finestra di un altro programma e la nostra (pid del processo avviato)
                import subprocess  # noqa: F401
                return True, json.dumps([{"pid": 1, "address": "0xdead", "floating": False},
                                         {"pid": pid.get("p", -1), "address": "0x55aa", "floating": False}])
            return True, ""
        system.run = run
        orig = picker.bring_to_front

        def spy(p, **kw):
            pid["p"] = p
            return orig(p, **kw)
        picker.bring_to_front = spy
        self.addCleanup(setattr, picker, "bring_to_front", orig)
        res = picker.pick("Scegli; rm -rf ~\n")
        self.assertEqual(res, {"ok": True, "path": "/home/x/sfondo.png", "why": ""})
        batch = [c for c in self.calls if c[:2] == ["hyprctl", "--batch"]]
        self.assertEqual(len(batch), 1)
        self.assertIn("address:0x55aa", batch[0][2])                    # solo la nostra finestra
        self.assertNotIn("0xdead", batch[0][2])
        self.assertIn("setfloating", batch[0][2])

    def test_title_is_an_argument_never_a_command(self):
        system.has = lambda p: p == "zenity"
        argv = picker.command('x" ; touch /tmp/pwn ; "\x1b[31m' + "a" * 500)
        self.assertEqual(argv[0], "zenity")
        title = argv[argv.index("--title") + 1]
        self.assertLessEqual(len(title), 80)
        self.assertNotIn("\x1b", title)

    def test_cancel(self):
        self.fake("zenity", "exit 1")
        system.run = lambda argv, timeout=10: (False, "")
        self.assertEqual(picker.pick("t"), {"ok": False, "path": "", "why": "cancel"})

    def test_kdialog_fallback_and_none(self):
        system.has = lambda p: p == "kdialog"
        self.assertEqual(picker.command("t")[0], "kdialog")
        system.has = lambda p: False
        self.assertIsNone(picker.command("t"))
        self.assertEqual(picker.pick("t")["why"], "no-picker")

    def test_bad_hyprctl_answers(self):
        for out in ("non json", "{}", json.dumps([{"pid": 7, "address": "0x1;dispatch exec rm"}])):
            system.run = lambda argv, timeout=10, o=out: (self.calls.append(argv) or True, o)
            self.calls.clear()
            picker.bring_to_front(7, tries=2, sleep=lambda s: None)
            self.assertFalse([c for c in self.calls if "--batch" in c])        # niente comandi strani


if __name__ == "__main__":
    unittest.main()
