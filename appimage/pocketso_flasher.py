#!/usr/bin/env python3
"""Standalone Pocketso ISO downloader and USB flasher."""
from __future__ import annotations
import json, os, subprocess, sys, threading, urllib.request
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton, QTextEdit, QVBoxLayout, QWidget

REPOSITORY = "trail-b1az3r/pocketSO"
API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"

def run_text(args):
    try:
        return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""

def list_usb_drives():
    raw = run_text(["lsblk", "-J", "-b", "-p", "-o", "NAME,TYPE,SIZE,TRAN,RM,MODEL,SERIAL,RO"])
    if not raw:
        return []
    try:
        devices = json.loads(raw).get("blockdevices", [])
    except json.JSONDecodeError:
        return []
    protected = set()
    for mount in ("/", "/boot", "/run/archiso/bootmnt"):
        source = run_text(["findmnt", "-nro", "SOURCE", mount]).split("[", 1)[0]
        if source:
            rows = run_text(["lsblk", "-s", "-n", "-p", "-o", "NAME,TYPE", source])
            for row in rows.splitlines():
                bits = row.split()
                if len(bits) == 2 and bits[1] == "disk":
                    protected.add(os.path.realpath(bits[0]))
    drives = []
    for item in devices:
        path = item.get("name") or ""
        if item.get("type") != "disk" or not path or os.path.realpath(path) in protected:
            continue
        if item.get("tran") != "usb" and str(item.get("rm")).lower() not in ("1", "true"):
            continue
        if str(item.get("ro")).lower() in ("1", "true"):
            continue
        size = int(item.get("size") or 0)
        model = (item.get("model") or "USB drive").strip()
        serial = (item.get("serial") or "").strip()
        label = f"{path} — {size / (1024 ** 3):.1f} GiB — {model}"
        if serial:
            label += f" — {serial}"
        drives.append({"path": path, "label": label})
    return drives

class Worker(QObject):
    log = Signal(str)
    downloadDone = Signal(str)
    flashDone = Signal(bool, str)
    progress = Signal(int)
    downloadFinished = Signal()

    def download_latest(self):
        try:
            request = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json", "User-Agent": "Pocketso-AppImage"})
            with urllib.request.urlopen(request, timeout=30) as response:
                release = json.load(response)
            assets = [a for a in release.get("assets", []) if a.get("name", "").lower().endswith(".iso")]
            if not assets:
                raise RuntimeError("No ISO is attached to the latest GitHub release yet. Choose a local ISO or publish a release with an ISO asset.")
            asset = assets[0]
            destination = Path.home() / "Downloads" / asset["name"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            self.log.emit(f"Downloading {asset['name']} from GitHub Releases…")
            request = urllib.request.Request(asset["browser_download_url"], headers={"User-Agent": "Pocketso-AppImage"})
            with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
                total = int(response.headers.get("Content-Length") or asset.get("size") or 0)
                received = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    received += len(chunk)
                    if total:
                        self.progress.emit(min(100, int(received * 100 / total)))
            self.downloadDone.emit(str(destination))
        except Exception as exc:
            self.log.emit(f"Download failed: {exc}")
        finally:
            self.downloadFinished.emit()

    def flash(self, iso_path, target, confirmation):
        try:
            appdir = os.environ.get("APPDIR", "")
            helper = Path(appdir) / "usr/libexec/pocketso-flash-root"
            if not helper.is_file():
                raise RuntimeError("The privileged flasher helper is missing from this AppImage.")
            if not Path(iso_path).is_file() or not iso_path.lower().endswith(".iso"):
                raise RuntimeError("Choose a valid ISO file.")
            if not target or confirmation != target:
                raise RuntimeError("Type the exact USB device path to confirm.")
            self.log.emit("Requesting administrator authorization. The selected USB will be erased.")
            process = subprocess.Popen(["pkexec", str(helper), iso_path, target, confirmation],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            assert process.stdout is not None
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    self.log.emit(line)
                    if line.startswith("PROGRESS "):
                        try:
                            self.progress.emit(max(0, min(100, int(line.split()[1]))))
                        except (ValueError, IndexError):
                            pass
            code = process.wait()
            self.flashDone.emit(code == 0, "Flash completed. Safely eject the USB before booting." if code == 0 else f"Flashing failed or was cancelled (exit code {code}).")
        except Exception as exc:
            self.flashDone.emit(False, str(exc))

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pocketso Flasher")
        self.resize(720, 560)
        self.iso_path = ""
        self.worker = Worker()
        root = QWidget()
        layout = QVBoxLayout(root)
        heading = QLabel("Pocketso Flasher")
        heading.setStyleSheet("font-size: 26px; font-weight: 650;")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Download a Pocketso release or select an ISO, then write it to a USB drive."))
        form = QFormLayout()
        self.iso_label = QLabel("No ISO selected")
        self.iso_label.setWordWrap(True)
        iso_row = QHBoxLayout()
        iso_row.addWidget(self.iso_label, 1)
        browse = QPushButton("Choose ISO…")
        browse.clicked.connect(self.choose_iso)
        iso_row.addWidget(browse)
        self.download = QPushButton("Download latest ISO")
        self.download.clicked.connect(self.download_iso)
        form.addRow("Image", iso_row)
        form.addRow("", self.download)
        self.drives = QComboBox()
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_drives)
        drive_row = QHBoxLayout()
        drive_row.addWidget(self.drives, 1)
        drive_row.addWidget(refresh)
        form.addRow("Destination USB", drive_row)
        self.confirm = QLineEdit()
        self.confirm.setPlaceholderText("Type the exact device path, e.g. /dev/sdX")
        form.addRow("Confirm erase", self.confirm)
        layout.addLayout(form)
        warning = QLabel("WARNING: Flashing permanently erases the selected USB drive. Check the device path and capacity carefully.")
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #c45b38; font-weight: 600;")
        layout.addWidget(warning)
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Download and flashing output will appear here.")
        layout.addWidget(self.log, 1)
        self.flash_button = QPushButton("Flash Pocketso to USB")
        self.flash_button.clicked.connect(self.flash_iso)
        layout.addWidget(self.flash_button)
        self.setCentralWidget(root)
        self.worker.log.connect(self.log.append)
        self.worker.downloadDone.connect(self.set_iso)
        self.worker.downloadFinished.connect(lambda: self.download.setEnabled(True))
        self.worker.flashDone.connect(self.flash_finished)
        self.worker.progress.connect(self.progress.setValue)
        self.refresh_drives()

    def run_background(self, function, *args):
        threading.Thread(target=function, args=args, daemon=True).start()

    def choose_iso(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Pocketso ISO", str(Path.home()), "ISO images (*.iso)")
        if path:
            self.set_iso(path)

    def set_iso(self, path):
        self.iso_path = path
        self.iso_label.setText(path)
        self.progress.setValue(100)
        self.log.append(f"ISO ready: {path}")

    def refresh_drives(self):
        current = self.drives.currentData()
        self.drives.clear()
        for drive in list_usb_drives():
            self.drives.addItem(drive["label"], drive["path"])
        index = self.drives.findData(current)
        self.drives.setCurrentIndex(index if index >= 0 else -1)

    def download_iso(self):
        self.download.setEnabled(False)
        self.run_background(self.worker.download_latest)

    def flash_iso(self):
        target = self.drives.currentData()
        if not self.iso_path or not target:
            QMessageBox.warning(self, "Missing selection", "Choose an ISO and a USB drive first.")
            return
        if self.confirm.text().strip() != target:
            QMessageBox.warning(self, "Confirmation required", f"Type {target} exactly to confirm erasing that drive.")
            return
        answer = QMessageBox.warning(self, "Erase USB drive?",
            f"This will permanently erase ALL data on:\\n\\n{target}\\n\\nContinue only if this is the correct USB drive.",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.Cancel)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.flash_button.setEnabled(False)
        self.progress.setValue(0)
        self.run_background(self.worker.flash, self.iso_path, target, self.confirm.text().strip())

    def flash_finished(self, success, message):
        self.flash_button.setEnabled(True)
        self.download.setEnabled(True)
        self.log.append(message)
        if success:
            QMessageBox.information(self, "Pocketso USB ready", message)
        else:
            QMessageBox.critical(self, "Flashing failed", message)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pocketso Flasher")
    window = Window()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
