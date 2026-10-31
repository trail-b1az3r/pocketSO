# Paket package manager

`paket` is Pocketso's optional command-line frontend for Arch package management. It delegates dependency resolution, package database updates, hooks, package transactions, and integrity checks to the native Pacman executable. It does not create a separate package database.

The ISO builder offers two modes:

- **Arch mode:** normal Pacman and yay workflow; no `paket` command is installed.
- **Paket mode:** installs `paket` as an additional frontend. Pacman remains installed as its transaction engine, and yay remains available.

Build with `sudo ./build.sh --manager paket` or choose option 2 in the interactive menu.

## All commands

| Command | What it does |
| --- | --- |
| `paket -I PACKAGE...` | Install one or more packages (`pacman -S --needed`). |
| `paket -S` | Refresh repository databases and perform a full system upgrade (`pacman -Syu`). |
| `paket -ISu`, `-ISU`, `-ISyu`, `-Su`, `-Syu` | Aliases for a full system update. |
| `paket -Sy` | Refresh repository databases without upgrading packages. |
| `paket -Syy` | Force-refresh all repository databases without upgrading. |
| `paket -Syyu` | Force-refresh repository databases and upgrade the whole system. |
| `paket -R PACKAGE...` | Remove packages using normal dependency checks. |
| `paket -Rdd PACKAGE...` | Remove packages while ignoring dependency checks. Dangerous; can break the system. |
| `paket -G QUERY...` | Search synchronized repository databases. |
| `paket -L` | List explicitly installed packages. |
| `paket -B [FILE]` | Export explicitly installed package names and versions (default: `packages.jsonl5`). |
| `paket -Bdd PACKAGE [DIR]` | Copy an already-cached archive for one installed package (default directory: `paket-backup`). |
| `paket -X [FILE]` | Export a JSONL5 package manifest (default: `packages.jsonl5`). |
| `paket -Z FILE` | Install package names from a JSONL5 manifest, using currently available repository versions. |
| `paket -C` | Clean unused cached package archives and cached sync databases (`pacman -Sc`). |
| `paket -H PACKAGE...` | Show detailed package information. Uses installed-package details when installed, otherwise repository details. |
| `paket -O [PACKAGE...]` | Verify installed package files with Pacman's `-Qkk`. With no names, checks all installed packages. |
| `paket --help` | Show the CLI help and available options. |

## All modifiers

| Modifier | Meaning |
| --- | --- |
| `-V` | Verbose Pacman output. |
| `-Q` | Quiet Pacman output. |
| `-K` | Disable package signature verification for that Pacman invocation. Unsafe; use only when you independently trust the source. |
| `-N` | Skip Pacman's confirmation prompts. |
| `-T SECONDS` | Stop waiting after the specified number of seconds. A timeout during a transaction can leave it incomplete. |
| `-F` | Force file-conflict overwrites using Pacman's `--overwrite '*'`. Supported only with install, full sync/upgrade, or manifest import (`-I`, `-S`, `-Z`). This can overwrite files owned by other packages. |
| `-P` | Preview a supported sync/install transaction using Pacman's `--print`; it lists targets without applying the transaction. Supported only with `-I`, `-S`, or `-Z`. It cannot be combined with `-F`. |
| `-C` | This is a standalone cache-cleaning command, not a general modifier. |
| `-H` | This is a standalone package-information command, not a general modifier. |
| `-O` | This is a standalone installed-file verification command, not a general modifier. |

## Modifier compatibility by command

The table shows which modifiers can be used with each operation. “Yes” means the modifier is accepted and passed through or applied as described. “Limited” means it has the stated operation-specific behavior. “No” means Paket rejects the combination instead of silently ignoring it.

| Operation | `-V` | `-Q` | `-K` | `-N` | `-T` | `-F` | `-P` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `-I` install | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `-S` full update | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `-Sy` / `-Syy` refresh only | Yes | Yes | Yes | Yes | Yes | No | No |
| `-Syyu` force-refresh update | Yes | Yes | Yes | Yes | Yes | Yes | No* |
| `-R` remove | Yes | Yes | Yes | Yes | Yes | No | No |
| `-Rdd` dependency-ignoring remove | Yes | Yes | Yes | Yes | Yes | No | No |
| `-G` search | Yes | Yes | Limited (does not affect an already-synced search) | No practical effect | Yes | No | No |
| `-L` list | Yes | Yes | Limited (local query; no signature check) | Limited (no prompt) | Yes | No | No |
| `-B` / `-X` export | No (rejected) | No (rejected) | No (rejected) | No (rejected) | No (rejected) | No | No |
| `-Bdd` archive backup | No (rejected) | No (rejected) | No (rejected) | No (rejected) | No (rejected) | No | No |
| `-Z` manifest import | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `-C` cache clean | Yes | Yes | Limited (no package download/signature check) | Yes (can skip cleanup confirmation) | Yes | No | No |
| `-H` package info | Yes | Yes | Limited (metadata query; no package download) | No practical effect | Yes | No | No |
| `-O` verify | Yes | Yes | No | No | Yes | No | No |

`-P` is intentionally not enabled for `-Syyu`: the force-refresh-upgrade shortcut has its own dedicated Pacman operation and is not included in Paket's preview allowlist. Use `paket -P -S` for a preview of the ordinary full-upgrade operation.

For operations that Paket rejects, do not assume a modifier was ignored. Run the operation without that modifier or use the matching supported command.

## Compact modifier clusters

For install, remove, and search, supported modifiers can be grouped after the operation letter:

```bash
sudo paket -IVN firefox       # install + verbose + no confirmation
sudo paket -IP firefox       # preview installation
sudo paket -IF package       # install with file-conflict overwrite
sudo paket -RVN package      # remove + verbose + no confirmation
paket -GV firefox            # search + verbose
```

The update aliases are explicit shortcuts, not arbitrary combinations:

```bash
sudo paket -ISu              # full system update
sudo paket -Su               # full system update
sudo paket -Syyu             # force-refresh and full system update
sudo paket -P -S             # preview ordinary full system update
```

Paket allows exactly one main operation per invocation. Do not combine unrelated operations.

## Examples

```bash
sudo paket -S
sudo paket -I firefox fastfetch
paket -G browser
paket -L
paket -H firefox
sudo paket -O firefox
sudo paket -O                 # verify all installed packages
paket -X packages.jsonl5
sudo paket -Z packages.jsonl5
sudo paket -B packages.jsonl5
sudo paket -Bdd firefox ./package-backups
sudo paket -R package-name
sudo paket -Rdd package-name
sudo paket -C
sudo paket -T 900 -I large-package
sudo paket -N -I package-name
sudo paket -P -I firefox
sudo paket -F -I package-name
```

A JSONL5 manifest is one JSON object per line, using the `.jsonl5` extension:

```json
{"name":"firefox","version":"132.0-1"}
{"name":"fastfetch","version":"2.30.0-1"}
```

The version is recorded for reference; imports install the currently available repository version. This keeps manifests portable across Arch snapshots.

## Safety notes

- Run install, remove, sync, import, cache-clean, and backup operations with root privileges where Pacman requires them.
- `-Rdd` can break dependencies and leave the system unusable.
- `-F` deliberately allows overwriting conflicting filesystem paths. Use it only to resolve a known conflict; it can damage files belonging to another package.
- `-P` is a preview for sync/install targets, not a guarantee that every later transaction hook or script will succeed.
- `-K` turns off package signature checks for only that invocation. Avoid it; use it only when you independently trust the package source.
- `-O` verifies package-owned files against Pacman's local package metadata. It does not repair altered or missing files.
- `-C` invokes Pacman's interactive cache cleanup. Review the prompt before confirming.
- `-B` exports explicitly installed package names and versions. `-Bdd` backs up an archive only if it is already in Pacman's package cache.
- `-T` stops waiting after the timeout. A timeout during a package transaction can leave work incomplete; inspect Pacman's state before retrying.
