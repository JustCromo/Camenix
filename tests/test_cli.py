"""Comando camenix: codici di uscita, --json stabile, NO_COLOR, errori chiari."""
import json
import pathlib
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin", "camenix")


def run(*args, env_extra=None):
    tmp = run.tmp
    env = {"PATH": "/usr/bin:/bin", "XDG_CONFIG_HOME": tmp, "HOME": tmp, "NO_COLOR": "1", "LANG": "C.UTF-8"}
    env.update(env_extra or {})
    return subprocess.run([sys.executable, BIN, *args], capture_output=True, text=True, env=env, timeout=30)


class TestCli(unittest.TestCase):
    def setUp(self):
        run.tmp = tempfile.mkdtemp()
        self.theme = os.path.join(run.tmp, "camenix", "theme.json")

    def test_status_without_theme(self):
        r = run("status")
        self.assertEqual(r.returncode, 0)
        self.assertIn("camenix init", r.stdout)

    def test_status_json_is_stable(self):
        r = run("status", "--json")
        d = json.loads(r.stdout)
        for key in ("version", "path", "exists", "theme", "problems"):
            self.assertIn(key, d)
        self.assertFalse(d["exists"])

    def test_init_then_check(self):
        self.assertEqual(run("init").returncode, 0)
        self.assertTrue(os.path.exists(self.theme))
        r = run("check", "--json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["ok"], True)

    def test_init_does_not_overwrite(self):
        run("init")
        pathlib.Path(self.theme).write_text('{"name": "mio"}')
        r = run("init")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--force", r.stderr)
        self.assertEqual(pathlib.Path(self.theme).read_text(), '{"name": "mio"}')
        self.assertEqual(run("init", "--force").returncode, 0)

    def test_check_reports_problems(self):
        os.makedirs(os.path.dirname(self.theme))
        pathlib.Path(self.theme).write_text('{"colors": {"text": "rosso"}}')
        r = run("check", "--json")
        self.assertEqual(r.returncode, 1)
        self.assertTrue(json.loads(r.stdout)["problems"])

    def test_unknown_command(self):
        r = run("\x1b[31mrm -rf")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("\x1b", r.stderr)

    def test_no_color(self):
        r = run("status")
        self.assertNotIn("\x1b[", r.stdout)

    def test_ascii_fallback(self):
        r = run("status", env_extra={"LANG": "C", "LC_ALL": "C", "PYTHONIOENCODING": "ascii"})
        self.assertEqual(r.returncode, 0)
        self.assertIn("##", r.stdout)

    def test_symlink_theme_is_an_error(self):
        os.makedirs(os.path.dirname(self.theme))
        os.symlink("/etc/passwd", self.theme)
        r = run("status")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("root:", r.stdout + r.stderr)

    def test_set_says_applied_even_without_linked_files(self):
        r = run("set", "accent", "#3FE0D0")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Tema applicato", r.stdout)
        self.assertIn("#3FE0D0", pathlib.Path(self.theme).read_text())

    def test_set_rejects_bad_input(self):
        self.assertEqual(run("set", "accent", "red").returncode, 2)
        self.assertEqual(run("set", "__proto__", "#FFFFFF").returncode, 2)
        self.assertFalse(os.path.exists(self.theme))

    def test_version(self):
        self.assertRegex(run("--version").stdout.strip(), r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
