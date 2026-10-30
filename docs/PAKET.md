# Paket package manager

`paket` is Pocketso's optional command-line frontend for Arch package management. It uses the native Pacman executable for dependency resolution, package database updates, hooks, and transactions. It does not create a separate package database or bypass Arch's package format.

The ISO builder offers two modes:

- **Arch mode:** normal Pacman and yay workflow; no `paket` command is installed.
- **Paket mode:** installs `paket` as an additional frontend. Pacman remains installed as its transaction engine, and yay remains available.

Build with `sudo ./build.sh --manager paket` or choose option 2 in the interactive menu.

## Commands

| Command | Action |
| --- | --- |
| `paket -I package...` | Install packages (Pacman `-S --needed`) |
| `paket -S` | Refresh repository databases and perform a full upgrade (`pacman -Syu`) |
| `paket -R package...` | Remove packages |
| `paket -Rdd package...` | Remove packages while skipping dependency checks; dangerous |
| `paket -B [file]` | Back up the explicitly installed package list |
| `paket -Bdd package [dir]` | Copy one installed package's cached archive into a backup directory |
| `paket -G query` | Search synchronized repositories |
| `paket -L` | List installed packages |
| `paket -V operation` | Enable verbose Pacman output for an operation |
| `paket -T seconds operation` | Set a hard timeout for an operation |
| `paket -Q operation` | Quiet Pacman output for an operation |
| `paket -K operation` | Disable signature verification for that operation only; unsafe |
| `paket -X [file]` | Export a `packages.jsonl5` manifest |
| `paket -Z file` | Install package names from a JSONL5 manifest |
| `paket -N operation` | Skip confirmation prompts |

Examples:

```bash
sudo paket -S
sudo paket -I firefox fastfetch
paket -G browser
paket -L
paket -X packages.jsonl5
sudo paket -Z packages.jsonl5
sudo paket -B packages.jsonl5
sudo paket -Bdd firefox ./package-backups
sudo paket -R package-name
sudo paket -Rdd package-name
sudo paket -T 900 -I large-package
sudo paket -N -I package-name
```

A JSONL5 manifest is one JSON object per line, using the `.jsonl5` extension. For example:

```json
{"name":"firefox","version":"132.0-1"}
{"name":"fastfetch","version":"2.30.0-1"}
```

The version is recorded for reference; imports install the currently available repository version. This keeps manifests portable across Arch snapshots.

## Safety notes

- Run install, remove, sync, import, and backup operations with root privileges where Pacman requires them.
- `-Rdd` can break dependencies and leave the system unusable.
- `-K` turns off package signature checks for only that invocation. Avoid it; use it only when you independently trust the package source.
- `-B` exports explicitly installed package names and versions. `-Bdd` backs up an archive only if it is already in Pacman's package cache.
- `-T` terminates an operation that exceeds its timeout. A timeout during a package transaction can leave work incomplete; inspect Pacman's state before retrying.
