"""Quickshell finto (in Python) per provare l'app senza Hyprland: i Process eseguono davvero i comandi."""
import os
import subprocess

from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer
from PySide6.QtQml import qmlRegisterType, qmlRegisterSingletonInstance


class StdioCollector(QObject):
    textChanged = Signal()
    streamFinished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""

    @Property(str, notify=textChanged)
    def text(self):
        return self._text


class Process(QObject):
    commandChanged = Signal()
    runningChanged = Signal()
    stdoutChanged = Signal()
    exited = Signal(int, int)
    log = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self._command, self._running, self._stdout = [], False, None

    @Property("QVariantList", notify=commandChanged)
    def command(self):
        return self._command

    @command.setter
    def command(self, v):
        self._command = list(v or [])
        self.commandChanged.emit()

    @Property(QObject, notify=stdoutChanged)
    def stdout(self):
        return self._stdout

    @stdout.setter
    def stdout(self, v):
        self._stdout = v
        self.stdoutChanged.emit()

    @Property(bool, notify=runningChanged)
    def running(self):
        return self._running

    @running.setter
    def running(self, v):
        if v and not self._running:
            self._running = True
            self.runningChanged.emit()
            QTimer.singleShot(0, self._run)

    def _run(self):
        argv = [str(a) for a in self._command]
        Process.log.append(argv)
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
            out, code = r.stdout, r.returncode
        except OSError:
            out, code = "", 127
        if self._stdout is not None:
            self._stdout._text = out
            self._stdout.textChanged.emit()
            self._stdout.streamFinished.emit()
        self._running = False
        self.runningChanged.emit()
        self.exited.emit(code, 0)


class FileView(QObject):
    pathChanged = Signal()
    watchChangesChanged = Signal()
    fileChanged = Signal()
    loaded = Signal()
    loadFailed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path, self._watch, self._text, self._mtime = "", False, "", None
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._poll)

    @Property(str, notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, v):
        self._path = v
        self.pathChanged.emit()
        QTimer.singleShot(0, self.reload)

    @Property(bool, notify=watchChangesChanged)
    def watchChanges(self):
        return self._watch

    @watchChanges.setter
    def watchChanges(self, v):
        self._watch = bool(v)
        self._timer.start() if v else self._timer.stop()

    def _poll(self):
        try:
            m = os.stat(self._path).st_mtime_ns
        except OSError:
            m = None
        if m != self._mtime:
            self._mtime = m
            self.fileChanged.emit()

    @Slot()
    def reload(self):
        try:
            with open(self._path, encoding="utf-8") as f:
                self._text = f.read()
            self._mtime = os.stat(self._path).st_mtime_ns
            self.loaded.emit()
        except OSError:
            self.loadFailed.emit(1)

    @Slot(result=str)
    def text(self):
        return self._text

    saved = Signal()

    @Slot(str)
    def setText(self, t):
        """Come il FileView vero: la scrittura avviene dopo (in background), non subito."""
        self._text = t
        def write():
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                f.write(t)
            self.saved.emit()
        QTimer.singleShot(400, write)


class QuickshellSingleton(QObject):
    def __init__(self, shell_dir):
        super().__init__()
        self._dir = shell_dir

    @Property(str, constant=True)
    def shellDir(self):
        return self._dir

    @Slot(str, result=str)
    def env(self, name):
        return os.environ.get(name, "")

    @Slot("QVariantList")
    def execDetached(self, argv):
        Process.log.append(["detached", *argv])


def register(shell_dir):
    qmlRegisterType(StdioCollector, "Quickshell.Io", 1, 0, "StdioCollector")
    qmlRegisterType(Process, "Quickshell.Io", 1, 0, "Process")
    qmlRegisterType(FileView, "Quickshell.Io", 1, 0, "FileView")
    global _INSTANCE
    _INSTANCE = QuickshellSingleton(shell_dir)          # deve vivere quanto il motore QML
    qmlRegisterSingletonInstance(QuickshellSingleton, "Quickshell", 1, 0, "Quickshell", _INSTANCE)
    return _INSTANCE


_INSTANCE = None
