# Pocketso Flasher (native Linux build)

Pocketso Flasher is a native Qt 6 / QML application with a C++ backend and a separate C++ privileged writer. It produces a normal dynamically linked Linux executable named `PocketsoFlasher`; it is not an AppImage and does not require launching the GUI with `sudo`.

## Build on Arch Linux

```bash
sudo pacman -S --needed base-devel cmake ninja qt6-base qt6-declarative qt6-quickcontrols2 qt6-tools polkit util-linux
cmake -S flasher -B build/flasher -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
cmake --build build/flasher
sudo cmake --install build/flasher
```

Run it from the desktop menu or:

```bash
PocketsoFlasher
```

The application binary is installed to `/usr/bin/PocketsoFlasher`; its C++ USB writer is installed to `/usr/libexec/pocketso-flash-root`. The PolicyKit action is installed under `/usr/share/polkit-1/actions`.

## Use

1. Launch `PocketsoFlasher` as your normal desktop user.
2. Choose a local ISO, or select either **Installer ISO** or **Pocketso Live ISO** in the image selector and download that variant from the latest GitHub Release.
3. Select a USB/removable whole disk. The running system disk is filtered out.
4. Type the exact device path shown by the drive selector.
5. Confirm the erase warning.
6. Approve the PolicyKit authentication prompt. Only the separate C++ writer runs with elevated privileges.

The helper rechecks the target at write time, rejects partitions and non-USB/non-removable disks, refuses the running system disk, checks capacity, unmounts destination partitions, verifies that none remain mounted, writes with `dd`, and runs `sync`.

The installer image launches the graphical USB installer. The live image boots to the Pocketso desktop and does not launch an installer. Both are raw hybrid ISO images and use the same verified USB-writing safety checks.\n\n## Runtime dependencies

- Qt 6 Core, Gui, Qml, Quick, Quick Controls and Network libraries and QML modules
- PolicyKit (`pkexec` and a desktop authentication agent)
- `lsblk`, `findmnt`, `umount`, `dd`, and `sync` from util-linux/coreutils

The executable is dynamically linked against the Qt libraries on the target Linux distribution. CI publishes the binary and helper as a tarball so both executables can be installed together. It is not a self-contained portable binary; use the matching distribution packages for Qt 6 and PolicyKit.
