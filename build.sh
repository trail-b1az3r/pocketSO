#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROFILE="$ROOT/profile"
WORK_DIR="${POCKETSO_WORK_DIR:-/tmp/pocketso-work}"
OUT_DIR="${POCKETSO_OUT_DIR:-$ROOT/out}"
TEMP_PROFILE=""

cleanup() {
  if [[ -n "$TEMP_PROFILE" && -d "$TEMP_PROFILE" ]]; then
    rm -rf -- "$TEMP_PROFILE"
  fi
}
trap cleanup EXIT

usage() {
  cat <<'EOF'
Pocketso ISO builder

Usage:
  ./build.sh [--manager arch|paket] [--work DIR] [--out DIR] [--help]

Build options:
  arch   Standard Arch package management (Pacman + yay).
  paket  Enable the Pocketso paket frontend (Pacman remains the
         transaction/signature/dependency engine underneath).

Archiso itself always uses Pacman to resolve and assemble an Arch ISO.
EOF
}

MANAGER=""
while (($#)); do
  case "$1" in
    --manager)
      [[ $# -ge 2 ]] || { echo "Missing value for --manager" >&2; exit 2; }
      MANAGER="$2"; shift 2 ;;
    --work)
      [[ $# -ge 2 ]] || { echo "Missing value for --work" >&2; exit 2; }
      WORK_DIR="$2"; shift 2 ;;
    --out)
      [[ $# -ge 2 ]] || { echo "Missing value for --out" >&2; exit 2; }
      OUT_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$MANAGER" ]]; then
  echo "Select the package-management option for this Pocketso ISO:"
  echo "  1) Arch package managers (Pacman + yay)"
  echo "  2) Pocketso paket frontend (Pacman backend + yay)"
  read -r -p "Choice [1/2]: " choice
  case "$choice" in
    1) MANAGER="arch" ;;
    2) MANAGER="paket" ;;
    *) echo "Invalid choice." >&2; exit 2 ;;
  esac
fi

case "$MANAGER" in
  arch) ;;
  paket) ;;
  *) echo "Manager must be 'arch' or 'paket'." >&2; exit 2 ;;
esac

if [[ $EUID -ne 0 ]]; then
  echo "Run this build script as root: sudo ./build.sh" >&2
  exit 1
fi
if ! command -v mkarchiso >/dev/null 2>&1; then
  echo "mkarchiso is missing. Install archiso first: pacman -S archiso" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
BUILD_PROFILE="$PROFILE"

if [[ "$MANAGER" == "paket" ]]; then
  TEMP_PROFILE="$(mktemp -d "${TMPDIR:-/tmp}/pocketso-profile.XXXXXX")"
  cp -a "$PROFILE/." "$TEMP_PROFILE/"
  mkdir -p "$TEMP_PROFILE/airootfs/etc/pocketso"
  printf 'paket\n' > "$TEMP_PROFILE/airootfs/etc/pocketso/package-manager"
  BUILD_PROFILE="$TEMP_PROFILE"
  echo "Building with paket enabled. Pacman remains the package transaction engine."
else
  echo "Building with standard Arch package management."
fi

echo "Profile: $BUILD_PROFILE"
echo "Work directory: $WORK_DIR"
echo "Output directory: $OUT_DIR"
mkarchiso -v -w "$WORK_DIR" -o "$OUT_DIR" "$BUILD_PROFILE"

shopt -s nullglob
isos=("$OUT_DIR"/*.iso)
if (("${#isos[@]}" == 0)); then
  echo "Build finished without producing an ISO." >&2
  exit 1
fi
(
  cd "$OUT_DIR"
  sha256sum -- *.iso > SHA256SUMS
)
echo "Build complete:"
printf '  %s\n' "${isos[@]}"
echo "Checksums: $OUT_DIR/SHA256SUMS"
