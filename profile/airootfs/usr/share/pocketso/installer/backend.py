#!/usr/bin/env python3
"""Privileged Pocketso USB installation backend. Configuration is read from stdin."""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

MIN_BYTES = 30_000_000_000
MOUNT = Path("/mnt/pocketso-target")
PROFILE = Path("/usr/share/pocketso")
PACKAGE_MANAGER_FILE = Path("/etc/pocketso/package-manager")


def emit(message: str) -> None:
    print(message, flush=True)


def run(args: list[str], *, input_text: str | None = None) -> str:
    emit("$ " + " ".join(args[:4]) + (" …" if len(args) > 4 else ""))
    process = subprocess.Popen(
        args,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if input_text is not None:
        assert process.stdin is not None
        process.stdin.write(input_text)
        process.stdin.close()
    assert process.stdout is not None
    for line in process.stdout:
        line = line.rstrip()
        if line:
            emit(line)
    code = process.wait()
    if code:
        raise RuntimeError(f"Command failed with exit code {code}: {args[0]}")
    return ""


def output(args: list[str]) -> str:
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout.strip()


def disk_for_source(source: str) -> str:
    if not source:
        return ""
    source = source.split("[", 1)[0]
    try:
        rows = output(["lsblk", "-s", "-n", "-p", "-o", "NAME,TYPE", source])
    except (OSError, subprocess.CalledProcessError):
        return ""
    disks = [line.split()[0] for line in rows.splitlines() if len(line.split()) == 2 and line.split()[1] == "disk"]
    return os.path.realpath(disks[-1]) if disks else ""


def protected_disks() -> set[str]:
    result = set()
    for mount in ("/", "/run/archiso/bootmnt"):
        try:
            source = output(["findmnt", "-nro", "SOURCE", mount])
        except (OSError, subprocess.CalledProcessError):
            source = ""
        disk = disk_for_source(source)
        if disk:
            result.add(disk)
    return result


def disk_info(target: str) -> dict:
    if not target.startswith("/dev/") or not os.path.exists(target):
        raise RuntimeError("Destination is not a valid /dev block device.")
    if not os.path.realpath(target) == target:
        target = os.path.realpath(target)
    if not os.path.exists(target):
        raise RuntimeError("Destination device no longer exists.")
    data = json.loads(output([
        "lsblk", "-J", "-b", "-d", "-o", "NAME,PATH,TYPE,SIZE,TRAN,RM,MODEL,SERIAL",
        target,
    ]))
    items = data.get("blockdevices", [])
    if len(items) != 1:
        raise RuntimeError("Could not identify exactly one destination disk.")
    return items[0]


def validate_target(target: str, confirmation: str) -> None:
    if confirmation != target:
        raise RuntimeError("Typed confirmation does not match the destination device.")
    info = disk_info(target)
    if info.get("type") != "disk":
        raise RuntimeError("Choose a whole USB disk, not a partition.")
    if info.get("tran") != "usb" and str(info.get("rm")).lower() not in ("1", "true"):
        raise RuntimeError("Safety block: destination is not identified as USB/removable storage.")
    if int(info.get("size") or 0) < MIN_BYTES:
        raise RuntimeError("Destination must be at least 30 GB.")
    if os.path.realpath(target) in protected_disks():
        raise RuntimeError("Safety block: destination contains the running installer or system.")


def desktop_packages(desktop: str) -> list[str]:
    mate = [
        "caja", "marco", "mate-backgrounds", "mate-control-center", "mate-desktop",
        "mate-icon-theme", "mate-menus", "mate-notification-daemon", "mate-panel",
        "mate-polkit", "mate-session-manager", "mate-settings-daemon", "mate-themes",
        "mate-user-guide", "mate-terminal", "atril", "engrampa", "eom", "mate-applets",
        "mate-calc", "mate-media", "mate-power-manager", "mate-screensaver",
        "mate-system-monitor", "mate-utils", "mozo", "pluma", "lightdm",
        "lightdm-gtk-greeter",
    ]
    kde = ["plasma-meta", "plasma-nm", "konsole", "dolphin", "sddm", "xorg-server"]
    if desktop == "mate":
        return mate
    if desktop == "kde":
        return kde
    if desktop == "both":
        return mate + kde
    raise RuntimeError("Unknown desktop selection.")


def install(config: dict) -> None:
    target = str(config.get("target", ""))
    desktop = str(config.get("desktop", ""))
    username = str(config.get("username", ""))
    password = str(config.get("password", ""))
    confirmation = str(config.get("confirmation", ""))
    if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", username):
        raise RuntimeError("Invalid Linux username.")
    if len(password) < 10 or "\n" in password or "\r" in password or ":" in password:
        raise RuntimeError("Password must be at least 10 characters and cannot contain colon or line breaks.")
    if os.geteuid() != 0:
        raise RuntimeError("The installer backend must run as root.")

    validate_target(target, confirmation)
    try:
        socket.gethostbyname("geo.mirror.pkgbuild.com")
    except OSError as exc:
        raise RuntimeError("Internet connection required. Connect to Wi-Fi and retry.") from exc

    info = disk_info(target)
    emit(f"Destination: {target} ({info.get('model') or 'USB drive'}; {int(info.get('size')) // (1024**3)} GiB)")
    emit("Rechecking destination safety immediately before erasing.")
    validate_target(target, confirmation)

    MOUNT.mkdir(parents=True, exist_ok=True)
    mounted = False
    try:
        emit("Unmounting any mounted destination partitions.")
        parts = output(["lsblk", "-lnpo", "NAME", target]).splitlines()[1:]
        for part in parts:
            subprocess.run(["umount", part], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        mounts = output(["lsblk", "-nrpo", "MOUNTPOINT", target])
        if any(line.strip() for line in mounts.splitlines()):
            raise RuntimeError("Could not unmount every destination partition; no data was erased.")

        emit("Erasing partition signatures and creating the USB partition table.")
        run(["wipefs", "--all", "--force", target])
        run(["parted", "--script", target, "mklabel", "gpt"])
        run(["parted", "--script", target, "mkpart", "BIOS", "1MiB", "3MiB"])
        run(["parted", "--script", target, "set", "1", "bios_grub", "on"])
        run(["parted", "--script", target, "mkpart", "ESP", "fat32", "3MiB", "1027MiB"])
        run(["parted", "--script", target, "set", "2", "esp", "on"])
        run(["parted", "--script", target, "mkpart", "ROOT", "ext4", "1027MiB", "100%"])
        run(["partprobe", target])
        run(["udevadm", "settle"])
        time.sleep(1)
        parts = output(["lsblk", "-lnpo", "NAME", target]).splitlines()[1:]
        if len(parts) != 3:
            raise RuntimeError("Could not detect the three destination partitions.")
        efi_part, root_part = parts[1], parts[2]

        run(["mkfs.fat", "-F", "32", "-n", "POCKETSO_EFI", efi_part])
        run(["mkfs.ext4", "-F", "-L", "POCKETSO_ROOT", root_part])
        run(["mount", root_part, str(MOUNT)])
        mounted = True
        (MOUNT / "boot").mkdir(exist_ok=True)
        run(["mount", efi_part, str(MOUNT / "boot")])

        base = [
            "base", "linux", "linux-lts", "linux-firmware", "archlinux-keyring", "grub",
            "python", "fastfetch",
            "efibootmgr", "dosfstools", "e2fsprogs", "networkmanager", "iwd",
            "wpa_supplicant", "sudo", "git", "base-devel", "go", "dialog", "nano",
            "vim", "man-db", "man-pages", "texinfo", "mesa", "vulkan-icd-loader",
            "pipewire", "pipewire-alsa", "pipewire-pulse", "wireplumber", "bluez",
            "bluez-utils", "zram-generator", "network-manager-applet", "udisks2",
            "gvfs", "gvfs-mtp", "gvfs-smb", "polkit", "firefox",
        ]
        emit(f"Installing Arch Linux base and {desktop.upper()} desktop packages. This may take a while.")
        run(["pacstrap", "-K", str(MOUNT), *base, *desktop_packages(desktop)])
        fstab = output(["genfstab", "-U", str(MOUNT)])
        with (MOUNT / "etc/fstab").open("w") as handle:
            handle.write(fstab + "\n")

        def chroot(*args: str, input_text: str | None = None) -> None:
            run(["arch-chroot", str(MOUNT), *args], input_text=input_text)

        emit("Initializing the installed system and creating your user.")
        chroot("pacman-key", "--init")
        chroot("pacman-key", "--populate", "archlinux")
        chroot("ln", "-sf", "/usr/share/zoneinfo/UTC", "/etc/localtime")
        chroot("bash", "-lc", "sed -i 's/^#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen")
        (MOUNT / "etc/locale.conf").write_text("LANG=en_US.UTF-8\n")
        (MOUNT / "etc/hostname").write_text("pocketso\n")
        chroot("useradd", "-m", "-G", "wheel,audio,video,storage,optical", "-s", "/bin/bash", username)
        chroot("chpasswd", input_text=f"{username}:{password}\n")
        password = ""

        # Carry the Pocketso Fastfetch identity into the installed USB system.
        fastfetch_dir = MOUNT / "usr/share/pocketso/fastfetch"
        fastfetch_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROFILE / "fastfetch/pocketso.txt", fastfetch_dir / "pocketso.txt")
        shutil.copy2(PROFILE / "fastfetch/config.jsonc", fastfetch_dir / "config.jsonc")
        user_home = MOUNT / "home" / username
        user_config = user_home / ".config/fastfetch"
        user_config.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROFILE / "fastfetch/config.jsonc", user_config / "config.jsonc")
        shutil.chown(user_home / ".config", user=username, group=username)
        shutil.chown(user_config, user=username, group=username)
        shutil.chown(user_config / "config.jsonc", user=username, group=username)
        bashrc = user_home / ".bashrc"
        with bashrc.open("a", encoding="utf-8") as handle:
            handle.write("\n# Pocketso Fastfetch\nif [[ $- == *i* ]] && command -v fastfetch >/dev/null 2>&1; then\n  fastfetch\nfi\n")

        # The builder writes this marker only for package-manager option 2.
        manager = PACKAGE_MANAGER_FILE.read_text(encoding="utf-8").strip() if PACKAGE_MANAGER_FILE.is_file() else "arch"
        if manager == "paket":
            paket_target = MOUNT / "usr/local/bin/paket"
            paket_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROFILE / "paket", paket_target)
            paket_target.chmod(0o755)
            emit("Paket frontend enabled on the installed USB system.")
        elif manager != "arch":
            raise RuntimeError(f"Unknown Pocketso package manager mode: {manager}")

        (MOUNT / "etc/zram-generator.conf").write_text("[zram0]\nzram-size = ram / 2\ncompression-algorithm = zstd\nswap-priority = 100\n")
        sudoers = MOUNT / "etc/sudoers.d/10-wheel"
        sudoers.parent.mkdir(parents=True, exist_ok=True)
        sudoers.write_text("%wheel ALL=(ALL:ALL) ALL\n")
        sudoers.chmod(0o440)
        chroot("visudo", "-cf", "/etc/sudoers.d/10-wheel")

        emit("Installing Pocketso disk protection and enabling services.")
        guard_path = MOUNT / "usr/local/libexec/pocketso-disk-guard"
        guard_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROFILE / "disk-guard", guard_path)
        guard_path.chmod(0o755)
        for name, destination in (
            ("pocketso-disk-guard.service", "etc/systemd/system/pocketso-disk-guard.service"),
            ("pocketso-disk-guard@.service", "etc/systemd/system/pocketso-disk-guard@.service"),
            ("80-pocketso-disk-guard.rules", "etc/udev/rules.d/80-pocketso-disk-guard.rules"),
        ):
            dest = MOUNT / destination
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROFILE / name, dest)
        (MOUNT / "etc/systemd/system/pocketso-disk-guard.service").write_text(
            "[Unit]\nDescription=Protect non-system disks from writes (Pocketso)\n"
            "DefaultDependencies=no\nAfter=local-fs.target\n"
            "Before=udisks2.service display-manager.service graphical.target\n"
            "ConditionPathExists=/usr/local/libexec/pocketso-disk-guard\n\n"
            "[Service]\nType=oneshot\n"
            "ExecStart=/usr/local/libexec/pocketso-disk-guard --all\nRemainAfterExit=yes\n\n"
            "[Install]\nWantedBy=multi-user.target\n"
        )
        if desktop == "kde":
            chroot("systemctl", "enable", "NetworkManager", "bluetooth", "sddm", "pocketso-disk-guard")
        else:
            chroot("systemctl", "enable", "NetworkManager", "bluetooth", "lightdm", "pocketso-disk-guard")

        emit("Building yay as the unprivileged user.")
        yay_dir = f"/home/{username}/pocketso-yay"
        chroot("runuser", "-u", username, "--", "env", f"HOME=/home/{username}",
               "bash", "-lc", f"git clone https://aur.archlinux.org/yay.git {yay_dir} && cd {yay_dir} && makepkg -f --nodeps --noconfirm")
        packages = glob.glob(str(MOUNT / yay_dir.lstrip("/") / "yay-*.pkg.tar.zst"))
        packages = [p for p in packages if "debug" not in Path(p).name]
        if not packages:
            raise RuntimeError("Could not find the built yay package.")
        chroot("pacman", "-U", "--noconfirm", f"{yay_dir}/{Path(packages[0]).name}")
        shutil.rmtree(MOUNT / yay_dir.lstrip("/"), ignore_errors=True)

        emit("Installing BIOS and UEFI bootloaders to the USB drive only.")
        chroot("grub-install", "--target=i386-pc", target)
        chroot("grub-install", "--target=x86_64-efi", "--efi-directory=/boot",
               "--bootloader-id=Pocketso", "--removable", "--no-nvram")
        chroot("grub-mkconfig", "-o", "/boot/grub/grub.cfg")
        emit("Flushing disk writes and unmounting the destination.")
        run(["sync"])
        run(["umount", "-R", str(MOUNT)])
        mounted = False
        emit("SUCCESS: Pocketso installation finished.")
    finally:
        if mounted:
            subprocess.run(["umount", "-R", str(MOUNT)], check=False)
        password = ""


def main() -> int:
    try:
        config = json.load(sys.stdin)
        install(config)
        return 0
    except Exception as exc:
        emit("ERROR: " + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
