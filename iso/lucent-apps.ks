# Lucent OS installer: put the default apps on the new system before its
# first boot, from the offline bundle on the install media (no network).
# Merged into the ISO's kickstart by iso/make-config.py; the bundle itself
# (/lucent-apps on the ISO) is made by iso/build-app-bundle.sh.
#
# The bundle is a ready /var/lib/flatpak (Flathub remote, the apps from
# /usr/share/lucent/flatpaks.list and their runtimes), built by Fedora's own
# flatpak. It is unpacked with the *new system's* tools (chroot), checked
# against its SHA256SUMS, and relabelled for SELinux. Any failure leaves an
# empty /var/lib/flatpak and the install continues: lucent-flatpak-setup
# then downloads the apps after first boot, as on the online path.
%post --nochroot --log=/tmp/lucent-apps.log
set -u
src=/run/install/repo/lucent-apps
root=/mnt/sysroot
if [ ! -f "$src/SHA256SUMS" ]; then
    echo "no offline app bundle on the install media; apps download after first boot"
    exit 0
fi
mkdir -p "$root/var/tmp/lucent-apps" "$root/var/lib/flatpak" "$root/var/log/lucent"
mount --bind "$src" "$root/var/tmp/lucent-apps"
start=$(date +%s)
chroot "$root" /usr/bin/bash -euo pipefail -c '
    cd /var/tmp/lucent-apps
    sha256sum --quiet -c SHA256SUMS
    cat flatpak.tar.zst.* | zstd -dc | tar -x --numeric-owner -C /var/lib/flatpak
    policy=$(sed -n "s/^SELINUXTYPE=//p" /etc/selinux/config)
    setfiles -F "/etc/selinux/${policy:-targeted}/contexts/files/file_contexts" /var/lib/flatpak
'
rc=$?
umount "$root/var/tmp/lucent-apps"
rmdir "$root/var/tmp/lucent-apps"
if [ "$rc" -ne 0 ]; then
    echo "offline app bundle failed (exit $rc); apps download after first boot instead"
    rm -rf "$root/var/lib/flatpak"
    mkdir -p "$root/var/lib/flatpak"
else
    echo "default apps installed from the install media in $(( $(date +%s) - start )) s:"
    ls "$root/var/lib/flatpak/app"
fi
cp /tmp/lucent-apps.log "$root/var/log/lucent/apps-install.log" 2>/dev/null || true
exit 0
%end
