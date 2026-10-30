#!/usr/bin/env python3
"""Parse and instantiate the Pocketso Qt Quick UI using the offscreen platform."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

class InstallerStub(QObject):
    drivesChanged = Signal(str)
    logLine = Signal(str)
    installFinished = Signal(str)
    installFailed = Signal(str)
    busyChanged = Signal(bool)

    @Slot()
    def refreshDrives(self):
        self.drivesChanged.emit("[]")

    @Slot(str, str, str, str, str)
    def startInstall(self, *_args):
        pass

app = QGuiApplication([])
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("installer", InstallerStub())
qml = Path("profile/airootfs/usr/share/pocketso/installer/Main.qml").resolve()
engine.load(QUrl.fromLocalFile(str(qml)))
if not engine.rootObjects():
    raise SystemExit("Pocketso QML UI failed to load")
print("Pocketso QML UI parsed and instantiated successfully.")
