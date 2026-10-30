# Installer and disk safety notes

## Booting the installer

The ISO is a live Archiso environment. It uses MATE and provides the `pocketso-flasher` command. Boot it from a source USB, connect to a network, then install to a second USB drive.

## Destination layout

The flasher creates a GPT:

1. 1-3 MiB: unformatted BIOS boot partition (GRUB `bios_grub` flag)
2. 3-1027 MiB: FAT32 EFI System Partition, mounted at `/boot`
3. Remaining capacity: ext4 root filesystem

The installer requires at least 30,000,000,000 bytes. It does not create a separate swap partition; zram can be added in a later release.

## Safety model

- Candidate disks must report USB transport or removable status.
- The device backing the running live ISO and root filesystem is excluded.
- The exact destination path must be typed before destructive operations.
- The installer unmounts destination partitions, then erases the destination partition table.
- GRUB BIOS and UEFI targets are both installed to the selected USB. UEFI uses `--no-nvram` and `--removable`, so the host firmware boot entries are not changed.
- The installed Disk Guard identifies the disk containing the Pocketso root filesystem and sets every other physical disk read-only with `blockdev --setro`. A udev rule repeats protection for newly attached disks.
- The live installer does not enable Disk Guard, because it must be able to write to the destination USB.

This protection is defense in depth, not a hardware write blocker. It cannot protect against firmware, another OS, a kernel compromise, or writes occurring before the installed service starts. Do not use this initial implementation as a forensic write blocker.

## Networking and packages

The target installation is built with `pacstrap` from current Arch repositories. A working network is required. The target keyring is initialized and populated after installation. yay is built from the AUR as the newly created unprivileged user.

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
