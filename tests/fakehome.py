"""Home finta per i test: config di esempio + programmi esterni finti (nessun file vero toccato)."""
import os
import pathlib
import struct
import tempfile
import unittest
import zlib

from camenix import apply as ap, system


def png(path, color=(63, 224, 208)):
    raw = b"".join(b"\x00" + bytes(color) * 4 for _ in range(4))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    pathlib.Path(path).write_bytes(data)
    return path


CONFIGS = {
    ".config/mako/config": "font=Mono 11\nbackground-color=#FBF8FFD9\ntext-color=#2B2236\n"
                           "progress-color=over #FFD25A\n\n[urgency=high]\nborder-color=#E8892A\n",
    ".config/rofi/config.rasi": "* {\n    tuorlo: #FFD25A;\n    prugna: #2b2236;\n    altro: #123456;\n}\n"
                                "inputbar { background-color: #FFF4DAF2; }\n",
    ".config/hypr/hyprlock.conf": "background {\n    path = ~/sfondo.png\n    blur_passes = 3\n}\n"
                                 "input-field {\n    outer_color = rgba(D4C8FAee) rgba(FFD25Aee) 45deg\n}\n",
    ".config/hypr/config/decoration.lua": 'hl.config({ general = { col = {\n'
                                          '    active_border = { colors = {"rgba(E0B0FFff)", "rgba(FFBF00ff)"}, angle = 45 },\n'
                                          '    inactive_border = "rgba(FEFEFAaa)" } } })\n',
    ".config/kitty/kitty.conf": "font_size 11.0\nbackground_opacity 0.80\n",
}


class FakeHome(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self._env = {k: os.environ.get(k) for k in ("HOME", "XDG_CONFIG_HOME")}
        os.environ["HOME"] = self.home
        os.environ.pop("XDG_CONFIG_HOME", None)
        for rel, text in CONFIGS.items():
            p = pathlib.Path(self.home, rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        self.wall = png(os.path.join(self.home, "sfondo.png"))
        self.calls = []
        self.running = {"swaybg": [(1, ["swaybg", "-i", self.wall, "-m", "fill"])]}
        self._sys = (system.run, system.spawn, system.signal_own, system.own_processes, system.has)
        system.run = lambda argv, timeout=10: (self.calls.append(argv) or True, "")
        system.spawn = lambda argv: self.calls.append(argv) or True
        system.signal_own = lambda name, sig: self.calls.append([name, sig]) or 1
        system.own_processes = lambda name: self.running.get(name, [])
        system.has = lambda p: p in ("swaybg", "hyprctl", "makoctl")

    def tearDown(self):
        system.run, system.spawn, system.signal_own, system.own_processes, system.has = self._sys
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def p(self, rel):
        return os.path.join(self.home, rel)

    def read(self, rel):
        return pathlib.Path(self.home, rel).read_text()

    def snapshot(self):
        return {rel: self.read(rel) for rel in CONFIGS}
