# Pocketso Linux

**Website:** [Pocketso on GitHub Pages](https://trail-b1az3r.github.io/pocketSO/)

Pocketso is a portable, persistent Arch Linux installation designed to live entirely on a USB drive. It uses the host computer's CPU, memory, display, network and other supported hardware without installing to the host's internal storage.

## Current implementation

This repository builds a bootable Archiso installer. Boot it from one USB drive, then use the **Pocketso USB Installer** graphical app to install Pocketso onto a second USB drive.

- x86_64 Arch Linux base, Pacman and yay
- Optional **paket** package-management frontend for the custom-manager ISO build
- Real Fastfetch binary with a Pocketso USB-drive ASCII logo and custom configuration
- Python + PySide6 + Qt Quick/QML graphical installer
- MATE, KDE Plasma, or both selectable in the installer
- GPT with a BIOS boot partition and EFI System Partition
- GRUB for Legacy BIOS and UEFI (UEFI install uses `--no-nvram`)
- Persistent ext4 root filesystem
- Linux firmware, NetworkManager, iwd and common desktop hardware support
- Disk Guard marks non-system internal disks read-only in both the live installer and installed system
- A native Qt 6 / QML + C++ Pocketso Flasher downloads the latest release ISO or flashes a local ISO to a USB drive
- GitHub Actions builds the installer ISO and a native Linux flasher executable; tagged releases publish both

## Project website

The Pocketso website lives in `site/` and is deployed to GitHub Pages by `.github/workflows/pages.yml` whenever the site changes on `main`. The first deployment requires GitHub Pages to use **GitHub Actions** as its build and deployment source in the repository Pages settings.

## Build the ISO

The supported build environment is Arch Linux with `archiso`. Use the interactive builder to choose the package-manager mode:

```bash
sudo pacman -Syu --needed archiso
git clone https://github.com/trail-b1az3r/pocketSO.git
cd pocketSO
sudo bash build.sh
```

Or select a mode directly:

```bash
sudo bash build.sh --manager arch
sudo bash build.sh --manager paket
```

1. **Arch package managers:** standard Pacman + yay; no `paket` command is installed.
2. **Pocketso paket:** installs `paket` as the user-facing frontend, while Pacman remains the native dependency, signature, hook, and transaction engine. yay remains available.

Archiso itself always uses Pacman internally to assemble an Arch ISO; the second option changes the package-management tools installed in the resulting Pocketso environment, not Archiso's build engine.

The ISO is written to `out/` and a `SHA256SUMS` file is generated. Build output and work directories can be changed with `--out DIR` and `--work DIR`. See [docs/PAKET.md](docs/PAKET.md) for all Paket commands.

Every push to `main`, pull request and manual workflow dispatch runs the CI ISO build. CI checks the installer package names against current Arch repositories and compiles the native C++/QML flasher. Successful builds are uploaded as the `pocketso-installer-iso` and `pocketso-flasher-linux-x86_64` artifacts. A tag beginning with `v` also creates a GitHub Release containing the ISO, native Linux flasher tarball and checksums.

## Flash the installer USB from Linux

Download `PocketsoFlasher-linux-x86_64.tar.gz` from the latest GitHub Release, or from the `pocketso-flasher-linux-x86_64` artifact on the Actions page. This is a native Qt 6 / QML + C++ Linux build, not an AppImage.

Install the required runtime dependencies on Arch Linux:

```bash
sudo pacman -S --needed qt6-base qt6-declarative qt6-quickcontrols2 qt6-wayland polkit util-linux
tar -xzf PocketsoFlasher-linux-x86_64.tar.gz
sudo install -Dm755 usr/bin/PocketsoFlasher /usr/local/bin/PocketsoFlasher
sudo install -Dm755 usr/libexec/pocketso-flash-root /usr/local/libexec/pocketso-flash-root
sudo install -Dm644 usr/share/applications/pocketso-flasher.desktop /usr/local/share/applications/pocketso-flasher.desktop
sudo install -Dm644 usr/share/icons/hicolor/scalable/apps/pocketso-flasher.svg /usr/local/share/icons/hicolor/scalable/apps/pocketso-flasher.svg
```

Launch it as your normal desktop user:

```bash
PocketsoFlasher
```

The GUI does not need `sudo`. When you start flashing, PolicyKit (`pkexec`) requests administrator authentication for the separate C++ USB writer only. A desktop PolicyKit authentication agent must be running. The app can download the latest published Pocketso ISO or use a local ISO. Select a USB device, type its exact device path, confirm the erase warning, and authorize the write. It refuses to flash the running system disk and requires a whole USB/removable drive. **The selected USB is erased completely.** See [flasher/README.md](flasher/README.md) for build and installation details.

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
bash -n build.sh
bash -n profile/airootfs/usr/local/bin/pocketso-flasher
bash -n profile/airootfs/usr/local/bin/pocketso-installer
bash -n profile/airootfs/root/customize_airootfs.sh
python -m py_compile profile/airootfs/usr/share/pocketso/paket
python -m py_compile profile/airootfs/usr/share/pocketso/installer/app.py
python -m py_compile profile/airootfs/usr/share/pocketso/installer/backend.py
python scripts/check-installer-packages.py
python scripts/check-installer-qml.py
cmake -S flasher -B build/flasher -DCMAKE_BUILD_TYPE=Release
cmake --build build/flasher --parallel
```

See [docs/INSTALLER.md](docs/INSTALLER.md) and [docs/PAKET.md](docs/PAKET.md) for more details.
