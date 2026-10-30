#!/usr/bin/env bash
iso_name="pocketso"
iso_label="POCKETSO_$(date +%Y%m)"
iso_publisher="Pocketso Linux"
iso_application="Pocketso Linux USB Installer"
install_dir="pocketso"
buildmodes=('iso')
bootmodes=('bios.syslinux' 'uefi-iso')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
file_permissions=(
  ["/root/customize_airootfs.sh"]="0:0:755"
  ["/usr/local/bin/pocketso-flasher"]="0:0:755"
  ["/usr/share/pocketso/disk-guard"]="0:0:755"
)
