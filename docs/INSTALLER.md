# Installer and disk safety notes

## Booting the installer

The ISO is a live Archiso environment with MATE. Open **Pocketso USB Installer** from the desktop menu. The graphical frontend is written in Python with PySide6 and Qt Quick/QML; a separate privileged Python backend performs the installation after authentication through the desktop PolicyKit agent.

A legacy terminal-based `pocketso-flasher` remains available for troubleshooting. Connect to a network before installing.

## Graphical installation flow

1. The app enumerates whole USB/removable disks with at least 30 GB capacity.
2. It excludes the disk backing the live installer and root filesystem.
3. The user selects MATE, KDE Plasma, or both and enters a new account name/password.
4. The user must type the exact destination device path.
5. The privileged backend independently revalidates the device, transport/removable flag, capacity, mount state, source disk exclusion, and typed confirmation immediately before erasing.
6. The backend creates the partition table, installs Arch, configures services and user account, builds yay as the unprivileged user, and installs GRUB to the USB.
7. The UI streams command output and displays success/failure.

The GUI does not run destructive commands itself. It requests privilege through `pkexec`; the backend receives its configuration over standard input and never places the account password in command-line arguments or log output.

## Destination layout

The installer creates a GPT:

1. 1-3 MiB: unformatted BIOS boot partition (GRUB `bios_grub` flag)
2. 3-1027 MiB: FAT32 EFI System Partition, mounted at `/boot`
3. Remaining capacity: ext4 root filesystem

The installer requires at least 30,000,000,000 bytes. It does not create a separate swap partition; zram is configured in the installed system.

## Safety model

- Candidate disks must report USB transport or removable status.
- The device backing the running live ISO and root filesystem is excluded.
- The exact destination path must be typed before destructive operations.
- The backend repeats all device checks immediately before erasing.
- The installer unmounts destination partitions, then erases the destination partition table.
- GRUB BIOS and UEFI targets are both installed to the selected USB. UEFI uses `--no-nvram` and `--removable`, so the host firmware boot entries are not changed.
- Disk Guard identifies the live ISO boot medium or installed Pocketso root disk and sets every non-system internal disk read-only with `blockdev --setro`. A udev rule repeats protection for newly attached internal disks. Other USB/removable drives remain writable.
- The live installer does not enable Disk Guard, because it must be able to write to the destination USB.

This protection is defense in depth, not a hardware write blocker. It cannot protect against firmware, another OS, a kernel compromise, or writes occurring before the installed service starts. Do not use this initial implementation as a forensic write blocker.

## Networking and packages

The target installation is built with `pacstrap` from current Arch repositories. A working network is required. The target keyring is initialized and populated after installation. yay is built from the AUR as the newly created unprivileged user. CI resolves all package names in the backend against the current Arch repositories before building the ISO.

## Desktop choices

- MATE: Xorg, MATE, LightDM and the GTK greeter.
- KDE: Plasma, Dolphin, Konsole and SDDM.
- Both: both desktop stacks are installed; LightDM is the initial display manager.

## Known limitations

- x86_64 only.
- Secure Boot signing is not configured.
- Firmware and kernel support cannot guarantee every WiFi chipset.
- The installer source and target must be separate USB devices.
- No offline package repository/cache is bundled.
- This first version does not yet provide encrypted root, automatic snapshots, a recovery partition, or an offline rollback mechanism.
- The graphical installer has CI/static validation but still needs physical-device boot and install testing before it should be considered production-ready.
