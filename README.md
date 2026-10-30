# Pocketso Linux

**Website:** [Pocketso on GitHub Pages](https://trail-b1az3r.github.io/pocketSO/)

Pocketso is a portable, persistent Arch Linux installation designed to live entirely on a USB drive. It uses the host computer's CPU, memory, display, network and other supported hardware without installing to the host's internal storage.

## Current implementation

This repository builds a bootable Archiso installer. Boot it from one USB drive, then use the **Pocketso USB Installer** graphical app to install Pocketso onto a second USB drive.

- x86_64 Arch Linux base, Pacman and yay
- Python + PySide6 + Qt Quick/QML graphical installer
- MATE, KDE Plasma, or both selectable in the installer
- GPT with a BIOS boot partition and EFI System Partition
- GRUB for Legacy BIOS and UEFI (UEFI install uses `--no-nvram`)
- Persistent ext4 root filesystem
- Linux firmware, NetworkManager, iwd and common desktop hardware support
- Disk Guard marks non-system internal disks read-only in both the live installer and installed system
- A standalone Pocketso Flasher AppImage downloads the latest release ISO or flashes a local ISO to a USB drive
- GitHub Actions builds the installer ISO and AppImage; tagged releases publish both

## Project website

The Pocketso website lives in `site/` and is deployed to GitHub Pages by `.github/workflows/pages.yml` whenever the site changes on `main`. The first deployment requires GitHub Pages to use **GitHub Actions** as its build and deployment source in the repository Pages settings.

## Build the ISO

The supported build environment is Arch Linux with `archiso`.

```bash
sudo pacman -Syu --needed archiso
git clone https://github.com/trail-b1az3r/pocketSO.git
cd pocketSO
sudo mkarchiso -v -w /tmp/pocketso-work -o out profile
```

The ISO will be written to `out/`.

Every push to `main`, pull request and manual workflow dispatch runs the ISO build. CI also compiles the Python app/backend and checks the installer package names against current Arch repositories. Successful builds are uploaded as the `pocketso-installer-iso` artifact. A tag beginning with `v` also creates a GitHub Release containing the ISO, AppImage and checksums.

## Flash the installer USB from Linux

Download the `PocketsoFlasher-x86_64.AppImage` file from the latest GitHub Release, or from the `pocketso-flasher-appimage` artifact on the Actions page. Make it executable and launch it:

```bash
chmod +x PocketsoFlasher-x86_64.AppImage
./PocketsoFlasher-x86_64.AppImage
```

The app can download the latest published Pocketso ISO or use a local ISO. Select a USB device, type its exact device path, confirm the erase warning, and authorize the write. It refuses to flash the currently running system disk and requires a whole USB/removable drive. **The selected USB is erased completely.** See [appimage/README.md](appimage/README.md).

## Install Pocketso

1. Write the Pocketso installer ISO to a USB drive.
2. Boot a computer from that installer USB.
3. Connect to the internet (required to download the Arch packages).
4. Open **Pocketso USB Installer** from the MATE desktop. The legacy terminal flasher remains available as `sudo pocketso-flasher`.
5. Select a separate destination USB drive of at least 30 GB.
6. Select MATE, KDE, or both; create a user; type the exact destination device path to confirm.
7. Watch the installation log and wait for completion, then shut down and boot from the destination USB.

**The destination drive is erased completely.** Back up its contents first. The installer refuses to target the device containing the running installer and only offers removable/USB-transport disks. The privileged backend repeats these checks immediately before erasing and installs both bootloader targets to the selected USB only.

## Important limitations

- This is an initial installer implementation, not a claim of universal hardware compatibility. WiFi and graphics support depend on upstream Linux drivers and firmware.
- Internet access is required during installation. This is not yet an offline installer.
- The 30 GB minimum is checked against actual device capacity. A 64 GB USB 3.x drive is strongly recommended; USB 2.0 works but will be slow.
- The installer uses GPT. Legacy BIOS boot is supported through a BIOS boot partition; UEFI boot uses the USB's own ESP and does not create a firmware NVRAM entry.
- Disk Guard is installed on the target OS, not the live installer. It sets non-system physical disks read-only before the graphical login and again for newly attached disks. Do not treat software protection as a substitute for backups or firmware-level write protection.
- Secure Boot is not configured by this initial build.
- The installed system follows normal Arch rolling updates. Review Arch news before major upgrades.

## Development checks

```bash
bash -n profile/airootfs/usr/local/bin/pocketso-flasher
bash -n profile/airootfs/usr/local/bin/pocketso-installer
bash -n profile/airootfs/root/customize_airootfs.sh
python -m py_compile profile/airootfs/usr/share/pocketso/installer/app.py
python -m py_compile profile/airootfs/usr/share/pocketso/installer/backend.py
python scripts/check-installer-packages.py
python scripts/check-installer-qml.py
python -m py_compile appimage/pocketso_flasher.py appimage/pocketso-flash-root
bash -n appimage/build-appimage.sh
```

See [docs/INSTALLER.md](docs/INSTALLER.md) for implementation and safety details.
