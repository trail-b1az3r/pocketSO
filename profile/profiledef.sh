#!/usr/bin/env bash
iso_name="pocketso"
iso_label="POCKETSO_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"
iso_publisher="Pocketso Linux"
iso_application="Pocketso Linux USB Installer"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
install_dir="pocketso"
bootmodes=('bios.syslinux' 'uefi.grub')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
file_permissions=(
  ["/root/customize_airootfs.sh"]="0:0:755"
  ["/usr/local/bin/pocketso-flasher"]="0:0:755"
  ["/usr/local/bin/pocketso-installer"]="0:0:755"
  ["/usr/share/pocketso/disk-guard"]="0:0:755"
)
