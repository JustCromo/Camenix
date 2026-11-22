"""Paracadute che sopravvive all'app, e foto per la dissolvenza."""
import json
import os
import pathlib
import stat
import tempfile
import time

from camenix import apply as ap, safety, system, theme as th
from tests.fakehome import FakeHome


class TestGuard(FakeHome):
    def setUp(self):
        super().setUp()
        ap.setup()
        self.undos = []

    def undo(self):
        self.undos.append(1)

    def test_nobody_keeps_then_guard_reverts(self):
        token = safety.arm(seconds=0, spawn=False)
        self.assertTrue(safety.guard(token, self.undo, sleep=lambda s: None))
        self.assertEqual(self.undos, [1])
        self.assertFalse(os.path.exists(safety.pending_path()))

    def test_keep_wins(self):
        token = safety.arm(seconds=0, spawn=False)
        self.assertTrue(safety.keep())
        self.assertFalse(safety.guard(token, self.undo, sleep=lambda s: None))
        self.assertEqual(self.undos, [])
        self.assertFalse(safety.keep())                       # una volta sola

    def test_newer_apply_is_not_touched(self):
        old = safety.arm(seconds=0, spawn=False)
        new = {}
        def sleep(_):                                         # durante l'attesa arriva un altro "Applica"
            new["t"] = safety.arm(seconds=0, spawn=False)
        self.assertFalse(safety.guard(old, self.undo, sleep=sleep))
        self.assertEqual(self.undos, [])
        self.assertTrue(safety.guard(new["t"], self.undo, sleep=lambda s: None))   # il nuovo funziona ancora
        self.assertEqual(self.undos, [1])

    def test_spawns_a_detached_guard(self):
        token = safety.arm(seconds=16)
        call = [c for c in self.calls if "guard" in c][0]
        self.assertEqual(call[-1], token)
        self.assertEqual(stat.S_IMODE(os.stat(safety.pending_path()).st_mode), 0o600)

    def test_hostile_tokens_and_files(self):
        self.assertFalse(safety.guard("../../etc", self.undo, sleep=lambda s: None))
        self.assertFalse(safety.guard("a" * 32, self.undo, sleep=lambda s: None))         # nessuna attesa
        pathlib.Path(safety.pending_path()).write_text('{"token": "' + "a" * 32 + '", "deadline": 1e300}')
        waits = []
        safety.guard("a" * 32, self.undo, sleep=waits.append)
        self.assertLessEqual(waits[0], 60)                                               # mai più di un minuto
        pathlib.Path(safety.pending_path()).write_text("non json")
        self.assertFalse(safety.guard("a" * 32, self.undo, sleep=lambda s: None))
        self.assertEqual(self.undos, [1])

    def test_real_undo_restores_theme(self):
        before = th.read()[0]["colors"]["accent"]
        t = th.read()[0]
        t["colors"]["accent"] = "#123456"
        self.assertTrue(ap.change_theme(t).as_dict()["ok"])
        token = safety.arm(seconds=0, spawn=False)
        safety.guard(token, ap.undo, sleep=lambda s: None)
        self.assertEqual(th.read()[0]["colors"]["accent"], before)


class TestSnapshot(FakeHome):
    def setUp(self):
        super().setUp()
        self.rt = tempfile.mkdtemp()
        os.chmod(self.rt, 0o700)
        os.environ["XDG_RUNTIME_DIR"] = self.rt
        self.addCleanup(os.environ.pop, "XDG_RUNTIME_DIR", None)

        def run(argv, timeout=10):
            self.calls.append(argv)
            if argv[:2] == ["hyprctl", "monitors"]:
                return True, json.dumps([{"name": "eDP-1"}, {"name": "../../x"}, {"name": "HDMI-A-1"}])
            if argv[0] == "grim":
                pathlib.Path(argv[-1]).write_bytes(b"\x89PNG")
                return True, ""
            return True, ""
        system.run = run
        system.has = lambda p: True

    def test_snapshot_and_clean(self):
        r = safety.snapshot()
        self.assertTrue(r["ok"])
        self.assertEqual([s["name"] for s in r["shots"]], ["eDP-1", "HDMI-A-1"])          # nome ostile scartato
        for s in r["shots"]:
            self.assertTrue(s["path"].startswith(os.path.join(self.rt, "camenix")))
            self.assertEqual(stat.S_IMODE(os.stat(s["path"]).st_mode), 0o600)
        self.assertEqual(safety.clean(), 2)
        self.assertEqual(os.listdir(os.path.join(self.rt, "camenix")), [])

    def test_unsafe_runtime_dir(self):
        os.makedirs(os.path.join(self.rt, "camenix"), mode=0o755)
        os.chmod(os.path.join(self.rt, "camenix"), 0o755)                                 # leggibile da altri
        self.assertFalse(safety.snapshot()["ok"])
        os.rmdir(os.path.join(self.rt, "camenix"))
        os.symlink("/tmp", os.path.join(self.rt, "camenix"))                              # link
        self.assertFalse(safety.snapshot()["ok"])
        os.environ["XDG_RUNTIME_DIR"] = "relativo"
        self.assertFalse(safety.snapshot()["ok"])

    def test_no_grim(self):
        system.has = lambda p: p != "grim"
        self.assertEqual(safety.snapshot(), {"ok": False, "shots": []})


if __name__ == "__main__":
    import unittest
    unittest.main()
