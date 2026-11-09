#!/usr/bin/bash
# TEST-ONLY (hardware-live). Runs in a fedora:45 container on the runner:
# fetches and builds the test rig's helpers for the test VM.
#   fetch-tools.sh OUT KERNEL_VERSION   (e.g. 7.2.5-200.fc45.x86_64)
# OUT/rpms: kernel-modules-internal for EXACTLY the image's kernel (has
#   mac80211_hwsim), hostapd, dnsmasq, iw and their dependencies (the VM
#   installs only those it lacks, into a transient /usr overlay)
# OUT/bin:  hostapd, dnsmasq (unpacked; run from /var/tmp, unconfined) and
#   btvirt (BlueZ's emulator, not packaged by Fedora: built from the
#   release tarball of the bluez version Fedora ships)
set -euxo pipefail
out=$1 kver=$2
mkdir -p "$out/rpms" "$out/bin"
dnf -y -q --setopt=install_weak_deps=False install dnf5-plugins cpio xz gcc make \
    glib2-devel dbus-devel libical-devel readline-devel python3-docutils > /dev/null
cd "$out/rpms"
dnf -y -q download --resolve --arch=x86_64,noarch hostapd dnsmasq iw
if ! dnf -y -q download "kernel-modules-internal-${kver%.x86_64}"; then
    v=${kver%%-*} r=${kver#*-}
    r=${r%.x86_64}
    curl -fsSLO --retry 5 "https://kojipkgs.fedoraproject.org/packages/kernel/$v/$r/x86_64/kernel-modules-internal-$v-$r.x86_64.rpm"
fi
ls -la
tmp=$(mktemp -d)
for p in hostapd dnsmasq; do
    (cd "$tmp" && rpm2cpio "$out"/rpms/$p-[0-9]*.rpm | cpio -idm --quiet)
done
cp "$tmp/usr/sbin/hostapd" "$tmp/usr/sbin/dnsmasq" "$out/bin/"
bz=$(dnf -q repoquery --qf '%{version}\n' --latest-limit=1 bluez | tail -n1)
cd "$tmp"
curl -fsSL --retry 5 -o bluez.tar.xz "https://www.kernel.org/pub/linux/bluetooth/bluez-$bz.tar.xz"
tar xf bluez.tar.xz
cd "bluez-$bz"
./configure -q --enable-testing --disable-systemd --disable-udev --disable-cups --disable-obex \
    --disable-client --disable-manpages --disable-datafiles --disable-monitor \
    --disable-mesh --disable-midi --disable-a2dp --disable-avrcp --disable-network --disable-hid \
    --disable-hog --disable-bap --disable-bass --disable-mcp --disable-vcp --disable-micp \
    --disable-csip --disable-asha > /dev/null
make -s -j"$(nproc)" emulator/btvirt
cp emulator/btvirt "$out/bin/"
echo "bluez $bz" > "$out/bin/btvirt.version"
rm -rf "$tmp"
ls -la "$out/bin"
