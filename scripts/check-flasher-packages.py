#!/usr/bin/env python3
"""Validate all package sets used by the Pocketso USB installer."""
from pathlib import Path
import re
import shlex
import subprocess

flasher = Path("profile/airootfs/usr/local/bin/pocketso-flasher").read_text()
base = re.search(r"^BASE_PKGS=\(([^)]*)\)", flasher, re.MULTILINE)
if base is None:
    raise SystemExit("Could not extract BASE_PKGS from the USB flasher")

packages = set(shlex.split(base.group(1)))
desktop_groups = re.findall(
    r"^\s*(?:mate|kde|both)\) DESKTOP_PKGS=\(([^)]*)\)",
    flasher,
    re.MULTILINE,
)
if len(desktop_groups) != 3:
    raise SystemExit(
        f"Expected MATE, KDE, and both desktop package lists; found {len(desktop_groups)}"
    )

for group in desktop_groups:
    packages.update(shlex.split(group))

packages = sorted(packages)
print(f"Validating {len(packages)} unique target-system package names")
result = subprocess.run(
    ["pacman", "-Sp", "--print-format", "%n", "--noconfirm", *packages],
    check=True,
    text=True,
    capture_output=True,
)
plan = result.stdout.splitlines()
Path("/tmp/pocketso-target-package-plan.txt").write_text(result.stdout)
print(f"Pacman resolved {len(plan)} packages including dependencies")
