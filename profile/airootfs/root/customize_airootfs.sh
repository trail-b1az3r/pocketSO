#!/usr/bin/env bash
set -euo pipefail

ln -sf /usr/share/zoneinfo/UTC /etc/localtime
sed -i 's/^#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
locale-gen
printf 'LANG=en_US.UTF-8\n' > /etc/locale.conf
printf 'pocketso-installer\n' > /etc/hostname

pacman-key --init
pacman-key --populate archlinux

if ! id pocketso >/dev/null 2>&1; then
  useradd -m -G wheel,audio,video,storage,optical -s /bin/bash pocketso
fi
passwd -d pocketso
install -d -m 0750 /etc/sudoers.d
printf '%%wheel ALL=(ALL:ALL) NOPASSWD: ALL\n' > /etc/sudoers.d/10-pocketso-live
chmod 0440 /etc/sudoers.d/10-pocketso-live
visudo -cf /etc/sudoers.d/10-pocketso-live

install -d /etc/lightdm/lightdm.conf.d
cat > /etc/lightdm/lightdm.conf.d/20-pocketso-live.conf <<'EOF'
[Seat:*]
autologin-user=pocketso
autologin-user-timeout=0
autologin-session=mate
EOF

systemctl enable NetworkManager.service
systemctl enable lightdm.service
systemctl enable bluetooth.service
systemctl enable systemd-timesyncd.service
