#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROFILE="$ROOT/profile"
WORK_DIR="${POCKETSO_WORK_DIR:-/tmp/pocketso-work}"
OUT_DIR="${POCKETSO_OUT_DIR:-$ROOT/out}"
TEMP_PROFILE=""

cleanup() {
  if [[ -n "$TEMP_PROFILE" && -d "$TEMP_PROFILE" ]]; then rm -rf -- "$TEMP_PROFILE"; fi
}
trap cleanup EXIT

usage() {
  cat <<'EOF'
Pocketso ISO builder

Usage:
  sudo ./build.sh [--type all|installer|live] [--manager arch|paket] [--work DIR] [--out DIR]

Image types:
  installer  Bootable live installer used to deploy Pocketso to another USB.
  live       Bootable Pocketso desktop live image; does not launch the installer.
  all        Build both images (default).

Package manager:
  arch       Standard Pacman + yay.
  paket      Add the Pocketso paket frontend (Pacman remains the transaction engine).
EOF
}

MANAGER=""
IMAGE_TYPE="all"
while (($#)); do
  case "$1" in
    --manager) [[ $# -ge 2 ]] || { echo "Missing value for --manager" >&2; exit 2; }; MANAGER="$2"; shift 2 ;;
    --type) [[ $# -ge 2 ]] || { echo "Missing value for --type" >&2; exit 2; }; IMAGE_TYPE="$2"; shift 2 ;;
    --work) [[ $# -ge 2 ]] || { echo "Missing value for --work" >&2; exit 2; }; WORK_DIR="$2"; shift 2 ;;
    --out) [[ $# -ge 2 ]] || { echo "Missing value for --out" >&2; exit 2; }; OUT_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$MANAGER" ]]; then
  echo "Select package management:"
  echo "  1) Arch package managers (Pacman + yay)"
  echo "  2) Pocketso paket frontend (Pacman backend + yay)"
  read -r -p "Choice [1/2]: " choice
  case "$choice" in 1) MANAGER=arch ;; 2) MANAGER=paket ;; *) echo "Invalid choice." >&2; exit 2 ;; esac
fi
[[ "$MANAGER" == arch || "$MANAGER" == paket ]] || { echo "Manager must be arch or paket." >&2; exit 2; }
[[ "$IMAGE_TYPE" == all || "$IMAGE_TYPE" == installer || "$IMAGE_TYPE" == live ]] || { echo "Type must be all, installer, or live." >&2; exit 2; }
[[ $EUID -eq 0 ]] || { echo "Run this build script as root: sudo ./build.sh" >&2; exit 1; }
command -v mkarchiso >/dev/null 2>&1 || { echo "mkarchiso is missing. Install archiso first." >&2; exit 1; }

mkdir -p "$OUT_DIR"
build_one() {
  local type="$1"
  TEMP_PROFILE="$(mktemp -d "${TMPDIR:-/tmp}/pocketso-${type}.XXXXXX")"
  cp -a "$PROFILE/." "$TEMP_PROFILE/"
  mkdir -p "$TEMP_PROFILE/airootfs/etc/pocketso"
  printf '%s\n' "$MANAGER" > "$TEMP_PROFILE/airootfs/etc/pocketso/package-manager"

  if [[ "$type" == live ]]; then
    cp "$ROOT/scripts/customize_live_airootfs.sh" "$TEMP_PROFILE/airootfs/root/customize_airootfs.sh"
    chmod 0755 "$TEMP_PROFILE/airootfs/root/customize_airootfs.sh"
    rm -f "$TEMP_PROFILE/airootfs/usr/local/bin/pocketso-installer"
    rm -rf "$TEMP_PROFILE/airootfs/usr/share/pocketso/installer"
    sed -i -e '/^pyside6$/d' -e '/^qt6-declarative$/d' "$TEMP_PROFILE/packages.x86_64"
    sed -i 's/^iso_name="pocketso"$/iso_name="pocketso-live"/' "$TEMP_PROFILE/profiledef.sh"
    sed -i 's/USB Installer/Live Desktop/' "$TEMP_PROFILE/profiledef.sh"
  else
    sed -i 's/^iso_name="pocketso"$/iso_name="pocketso-installer"/' "$TEMP_PROFILE/profiledef.sh"
  fi

  echo "Building Pocketso $type ISO (package manager: $MANAGER)."
  mkarchiso -v -w "${WORK_DIR}-${type}" -o "$OUT_DIR" "$TEMP_PROFILE"
  rm -rf -- "$TEMP_PROFILE"
  TEMP_PROFILE=""
}

if [[ "$IMAGE_TYPE" == all ]]; then
  build_one installer
  build_one live
else
  build_one "$IMAGE_TYPE"
fi

shopt -s nullglob
isos=("$OUT_DIR"/*.iso)
(("${#isos[@]}" >= 1)) || { echo "Build finished without producing an ISO." >&2; exit 1; }
(
  cd "$OUT_DIR"
  sha256sum -- *.iso > SHA256SUMS
)
echo "Build complete:"
printf '  %s\n' "${isos[@]}"
echo "Checksums: $OUT_DIR/SHA256SUMS"
