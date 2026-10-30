#!/usr/bin/env python3
"""Pocketso USB installer GUI (PySide6 + Qt Quick)."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

QML_PATH = Path("/usr/share/pocketso/installer/Main.qml")
BACKEND_PATH = Path("/usr/share/pocketso/installer/backend.py")


def command_output(args: list[str]) -> str:
    try:
        result = subprocess.run(args, check=True, text=True, capture_output=True)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def parent_disk(source: str) -> str:
    if not source:
        return ""
    source = source.split("[", 1)[0]
    rows = command_output(["lsblk", "-s", "-n", "-p", "-o", "NAME,TYPE", source])
    disks = [line.split()[0] for line in rows.splitlines() if len(line.split()) == 2 and line.split()[1] == "disk"]
    return disks[-1] if disks else ""


def protected_system_disks() -> set[str]:
    protected: set[str] = set()
    for mount in ("/", "/run/archiso/bootmnt"):
        source = command_output(["findmnt", "-nro", "SOURCE", mount])
        disk = parent_disk(source)
        if disk:
            protected.add(os.path.realpath(disk))
    return protected


def available_drives() -> list[dict]:
    raw = command_output([
        "lsblk", "-J", "-b", "-p",
        "-o", "NAME,TYPE,SIZE,TRAN,RM,MODEL,SERIAL,RO",
    ])
    if not raw:
        return []
    try:
        devices = json.loads(raw).get("blockdevices", [])
    except json.JSONDecodeError:
        return []
    protected = protected_system_disks()
    found = []
    for item in devices:
        path = item.get("name") or ""
        if item.get("type") != "disk" or not path or os.path.realpath(path) in protected:
            continue
        if item.get("tran") != "usb" and str(item.get("rm")).lower() not in ("1", "true"):
            continue
        size = int(item.get("size") or 0)
        if size < 30_000_000_000:
            continue
        model = (item.get("model") or "USB drive").strip()
        serial = (item.get("serial") or "").strip()
        gib = size / (1024 ** 3)
        found.append({
            "path": path,
            "label": f"{path}  |  {gib:.1f} GiB  |  {model}" + (f"  |  {serial}" if serial else ""),
        })
    return found


class InstallerBridge(QObject):
    drivesChanged = Signal(str)
    logLine = Signal(str)
    installFinished = Signal(str)
    installFailed = Signal(str)
    busyChanged = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._busy = False

    @Slot()
    def refreshDrives(self) -> None:
        self.drivesChanged.emit(json.dumps(available_drives()))

    @Slot(str, str, str, str, str)
    def startInstall(self, target: str, desktop: str, username: str, password: str, confirmation: str) -> None:
        if self._busy:
            return
        if not target or confirmation != target:
            self.installFailed.emit("Select a drive and type its exact device path to confirm.")
            return
        if desktop not in ("mate", "kde", "both"):
            self.installFailed.emit("Choose MATE, KDE Plasma, or both.")
            return
        if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", username):
            self.installFailed.emit("Use a valid lowercase Linux username (letters, numbers, _ or -).")
            return
        if len(password) < 10 or "\n" in password or "\r" in password:
            self.installFailed.emit("Use a password with at least 10 characters and no line breaks.")
            return
        self._busy = True
        self.busyChanged.emit(True)
        config = {
            "target": target,
            "desktop": desktop,
            "username": username,
            "password": password,
            "confirmation": confirmation,
        }
        password = ""
        threading.Thread(target=self._run_backend, args=(config,), daemon=True).start()

    def _run_backend(self, config: dict) -> None:
        try:
            self.logLine.emit("Requesting administrator permission…")
            process = subprocess.Popen(
                ["pkexec", "/usr/bin/python", str(BACKEND_PATH)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert process.stdin is not None
            process.stdin.write(json.dumps(config))
            process.stdin.close()
            config["password"] = ""
            assert process.stdout is not None
            for line in process.stdout:
                clean = line.rstrip()
                if clean:
                    self.logLine.emit(clean)
            code = process.wait()
            if code == 0:
                self.installFinished.emit("Pocketso was installed successfully. Shut down, remove the installer USB, and boot from the destination drive.")
            else:
                self.installFailed.emit(f"Installation stopped (exit code {code}). Review the log for details. No host internal disk was selected as a target.")
        except Exception as exc:
            self.installFailed.emit(f"Could not start the installer: {exc}")
        finally:
            self._busy = False
            self.busyChanged.emit(False)


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Pocketso USB Installer")
    app.setOrganizationName("Pocketso")
    engine = QQmlApplicationEngine()
    bridge = InstallerBridge()
    engine.rootContext().setContextProperty("installer", bridge)
    if not QML_PATH.is_file():
        print(f"QML interface not found: {QML_PATH}", file=sys.stderr)
        return 1
    engine.load(QUrl.fromLocalFile(str(QML_PATH)))
    if not engine.rootObjects():
        return 1
    bridge.refreshDrives()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
