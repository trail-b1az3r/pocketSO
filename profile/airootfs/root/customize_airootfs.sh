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

# Install the real Fastfetch binary's Pocketso-specific ASCII logo/config.
install -D -m 0644 /usr/share/pocketso/fastfetch/config.jsonc /etc/skel/.config/fastfetch/config.jsonc
install -d -m 0755 /home/pocketso/.config/fastfetch
install -m 0644 /usr/share/pocketso/fastfetch/config.jsonc /home/pocketso/.config/fastfetch/config.jsonc
chown -R pocketso:pocketso /home/pocketso/.config
if ! grep -q 'Pocketso Fastfetch' /home/pocketso/.bashrc 2>/dev/null; then
  cat >> /home/pocketso/.bashrc <<'EOF'

# Pocketso Fastfetch
if [[ $- == *i* ]] && command -v fastfetch >/dev/null 2>&1; then
  fastfetch
fi
EOF
  chown pocketso:pocketso /home/pocketso/.bashrc
fi

# Paket is included only in ISO builds that explicitly select manager mode 2.
if [[ -f /etc/pocketso/package-manager ]] && [[ "$(tr -d '[:space:]' < /etc/pocketso/package-manager)" == "paket" ]]; then
  install -D -m 0755 /usr/share/pocketso/paket /usr/local/bin/paket
fi

install -d /etc/lightdm/lightdm.conf.d
cat > /etc/lightdm/lightdm.conf.d/20-pocketso-live.conf <<'EOF'
[Seat:*]
autologin-user=pocketso
autologin-user-timeout=0
autologin-session=mate
EOF

# Protect internal disks in the live installer before the desktop starts.
install -D -m 0755 /usr/share/pocketso/disk-guard /usr/local/libexec/pocketso-disk-guard
install -D -m 0644 /usr/share/pocketso/pocketso-disk-guard.service /etc/systemd/system/pocketso-disk-guard.service
install -D -m 0644 /usr/share/pocketso/pocketso-disk-guard@.service /etc/systemd/system/pocketso-disk-guard@.service
install -D -m 0644 /usr/share/pocketso/80-pocketso-disk-guard.rules /etc/udev/rules.d/80-pocketso-disk-guard.rules
systemctl enable pocketso-disk-guard.service

systemctl enable NetworkManager.service
systemctl enable lightdm.service
systemctl enable bluetooth.service
systemctl enable systemd-timesyncd.service
