# Lucent OS installer: put the default apps on the new system before its
# first boot, from the offline bundle on the install media (no network).
# Merged into the ISO's kickstart by iso/make-config.py; the bundle itself
# (/lucent-apps on the ISO) is made by iso/build-app-bundle.sh.
#
# The bundle is a ready /var/lib/flatpak (Flathub remote, the apps from
# /usr/share/lucent/flatpaks.list and their runtimes), built by Fedora's own
# flatpak. It is unpacked with the *new system's* tools (chroot), checked
# against its SHA256SUMS, and relabelled for SELinux (at the latest on first
# boot, by lucent-flatpak-relabel.service). Any failure leaves an
# empty /var/lib/flatpak and the install continues: lucent-flatpak-setup
# then downloads the apps after first boot, as on the online path.
%post --nochroot --interpreter=/usr/bin/bash --log=/tmp/lucent-apps.log
set -u
# Also on the serial console when there is one (CI's install test reads it).
if [ -c /dev/ttyS0 ]; then exec > >(tee -a /dev/ttyS0) 2>&1; fi
echo "lucent-apps: start"
src=/run/install/repo/lucent-apps
root=/mnt/sysroot
if [ ! -f "$src/SHA256SUMS" ]; then
    echo "no offline app bundle at $src; apps download after first boot"
    ls -la /run/install/repo/ 2>&1 | head -20
    exit 0
fi
# /mnt/sysroot is the new deployment, but its /var is not the /var the
# booted system will use: that is the stateroot's, on the physical root
# (/mnt/sysimage/ostree/deploy/<stateroot>/var). Write there, and show it to
# the chroot at /var/lib/flatpak so SELinux labels are computed for the
# right path.
var=""
if mountpoint -q "$root/var"; then
    var=$root/var
else
    for d in /mnt/sysimage/ostree/deploy/*/var; do [ -d "$d" ] && var=$d && break; done
fi
if [ -z "$var" ]; then
    echo "cannot find the new system's /var; apps download after first boot"
    exit 0
fi
echo "unpacking into $var/lib/flatpak"
mkdir -p "$var/lib/flatpak" "$var/log/lucent" "$root/var/lib/flatpak" "$root/var/tmp/lucent-apps"
mount --bind "$var/lib/flatpak" "$root/var/lib/flatpak"
mount --bind "$src" "$root/var/tmp/lucent-apps"
start=$(date +%s)
chroot "$root" /usr/bin/bash -euo pipefail -c '
    cd /var/tmp/lucent-apps
    sha256sum --quiet -c SHA256SUMS
    cat flatpak.tar.zst.* | zstd -dc | tar -x --numeric-owner -C /var/lib/flatpak
    # Label with the policy of the new system (-c: validate against its
    # binary policy, not the one the installer runs, which lacks some types).
    # If that is refused, lucent-flatpak-relabel.service does it at first boot.
    policy=$(sed -n "s/^SELINUXTYPE=//p" /etc/selinux/config)
    sel=/etc/selinux/${policy:-targeted}
    bin=$(ls "$sel"/policy/policy.* 2>/dev/null | sort -V | tail -n1)
    if ! setfiles -F -c "$bin" "$sel/contexts/files/file_contexts" /var/lib/flatpak; then
        echo "SELinux labels deferred to first boot"
        mkdir -p /var/lib/lucent
        touch /var/lib/lucent/relabel-flatpak
    fi
'
rc=$?
umount "$root/var/tmp/lucent-apps" "$root/var/lib/flatpak"
rmdir "$root/var/tmp/lucent-apps" 2>/dev/null || true
if [ "$rc" -ne 0 ]; then
    echo "offline app bundle failed (exit $rc); apps download after first boot instead"
    rm -rf "$var/lib/flatpak"
    mkdir -p "$var/lib/flatpak"
else
    echo "default apps installed from the install media in $(( $(date +%s) - start )) s:"
    ls "$var/lib/flatpak/app"
fi
cp /tmp/lucent-apps.log "$var/log/lucent/apps-install.log" 2>/dev/null || true
exit 0
%end
