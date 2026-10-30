#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
rm -rf build/appimage dist/PocketsoFlasher AppDir
python -m PyInstaller --noconfirm --clean --windowed --name PocketsoFlasher --collect-all PySide6 appimage/pocketso_flasher.py
python -m PyInstaller --noconfirm --clean --onefile --console --name pocketso-flash-root appimage/pocketso-flash-root
mkdir -p AppDir/usr/bin AppDir/usr/libexec AppDir/usr/share/applications AppDir/usr/share/icons/hicolor/scalable/apps
cp -a dist/PocketsoFlasher AppDir/usr/bin/
cp dist/pocketso-flash-root AppDir/usr/libexec/pocketso-flash-root
chmod 0755 AppDir/usr/libexec/pocketso-flash-root
cp appimage/pocketso-flasher.desktop AppDir/usr/share/applications/pocketso-flasher.desktop
cp appimage/pocketso-flasher.svg AppDir/usr/share/icons/hicolor/scalable/apps/pocketso-flasher.svg
cp appimage/AppRun AppDir/AppRun
chmod 0755 AppDir/AppRun
