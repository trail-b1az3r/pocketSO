# Pocketso Linux

Pocketso is a portable, persistent Arch Linux installation designed to live entirely on a USB drive. It uses the host computer's CPU, memory, display, network and other supported hardware without installing to the host's internal storage.

## Current implementation

This repository builds a bootable Archiso installer. Boot it from one USB drive, then use **Pocketso USB Flasher** to install Pocketso onto a second USB drive.

- x86_64 Arch Linux base, Pacman and yay
- MATE, KDE Plasma, or both selectable in the installer
- GPT with a BIOS boot partition and EFI System Partition
- GRUB for Legacy BIOS and UEFI (UEFI install uses `--no-nvram`)
- Persistent ext4 root filesystem
- Linux firmware, NetworkManager, iwd and common desktop hardware support
- Installed-system Disk Guard marks every non-system physical disk read-only
- GitHub Actions builds the installer ISO and publishes it as an artifact

## Build the ISO

The supported build environment is Arch Linux with `archiso`.

```bash
sudo pacman -Syu --needed archiso
git clone https://github.com/trail-b1az3r/pocketSO.git
cd pocketSO
sudo mkarchiso -v -w /tmp/pocketso-work -o out profile
```

The ISO will be written to `out/`.

Every push, pull request and manual workflow dispatch runs the ISO build. Successful builds are uploaded as the `pocketso-installer-iso` artifact. A tag beginning with `v` also creates a GitHub Release containing the ISO and checksum.

## Install Pocketso

1. Write the Pocketso installer ISO to a USB drive.
2. Boot a computer from that installer USB.
3. Connect to the internet (required to download the Arch packages).
4. Open **Pocketso USB Flasher** from the MATE desktop, or run `sudo pocketso-flasher` in a terminal.
5. Select a separate destination USB drive of at least 30 GB.
6. Select MATE, KDE, or both; create a user; confirm the exact destination device.
7. Wait for installation and verification to finish, then shut down and boot from the destination USB.

**The destination drive is erased completely.** Back up its contents first. The installer refuses to target the device containing the running installer and only offers removable/USB-transport disks. It never writes a bootloader to the host's internal disk.

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
bash -n profile/airootfs/root/customize_airootfs.sh
python -m py_compile profile/airootfs/usr/share/pocketso/disk-guard
```

See [docs/INSTALLER.md](docs/INSTALLER.md) for implementation and safety details.
