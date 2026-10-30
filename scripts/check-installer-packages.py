#!/usr/bin/env python3
"""Resolve every official-repository package used by the Pocketso USB installer."""
import ast
from pathlib import Path
import subprocess

path = Path("profile/airootfs/usr/share/pocketso/installer/backend.py")
tree = ast.parse(path.read_text(), filename=str(path))
packages: set[str] = set()

for node in ast.walk(tree):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    if node.name == "install":
        for child in ast.walk(node):
            if isinstance(child, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "base"
                for target in child.targets
            ):
                packages.update(ast.literal_eval(child.value))
    if node.name == "desktop_packages":
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                names = {
                    target.id for target in child.targets if isinstance(target, ast.Name)
                }
                if names & {"mate", "kde"}:
                    packages.update(ast.literal_eval(child.value))

if not packages:
    raise SystemExit("No target package names found in installer backend")

ordered = sorted(packages)
print(f"Resolving {len(ordered)} target package names against current Arch repositories")
subprocess.run(
    ["pacman", "-Sp", "--print-format", "%n", "--noconfirm", *ordered],
    check=True,
)
print("All target package names resolve.")
