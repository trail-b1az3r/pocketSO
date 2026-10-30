# Pocketso Flasher AppImage

The AppImage runs on an existing Linux desktop and writes the Pocketso installer ISO to a USB drive. It is not the live-ISO installer that installs Pocketso onto a second USB drive.

## Use

1. Download the PocketsoFlasher-x86_64.AppImage build artifact from GitHub Actions (or a published release).
2. Make it executable with: chmod +x PocketsoFlasher-x86_64.AppImage
3. Run it, download the latest published ISO or select a local .iso file.
4. Select the USB device, read the device path and type it exactly.
5. Confirm the erase prompt and authorize the write when prompted.

The app uses pkexec for administrator authorization and the bundled root helper rechecks the target. It accepts whole USB/removable disks only, refuses the running system disk, unmounts destination partitions, verifies that the image fits, writes the raw ISO, and synchronizes disk writes.

**All data on the selected USB drive is erased.** Verify the path and disconnect unrelated external drives before flashing.

## Build

On Ubuntu 22.04 or a compatible build host:

    python -m pip install PySide6 pyinstaller
    bash appimage/build-appimage.sh

The GitHub Actions workflow assembles the AppDir and produces the AppImage with appimagetool.
