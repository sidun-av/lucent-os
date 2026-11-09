#!/usr/bin/bash
# CI smoke test, run as root inside the freshly built image (not part of it):
#   podman run --rm -v ./build_files:/t:ro IMAGE /t/smoke-test.sh
# Checks what an image build can't: that a Windows program actually starts,
# first without the prefix template (first minutes after boot) and then with
# it, and that Lucent's systemd units and udev rules parse.
set -euo pipefail

step() { printf '\n== %s ==\n' "$*"; }

step "lucent-bridge"
lucent-bridge --version
if rpm -q wine-systemd; then echo "wine-systemd must not be installed"; exit 1; fi
test -L /usr/share/lucent-bridge/prefix-template

# A console program that ships with Wine itself: no download needed.
# x86-64 first (on aarch64 that exercises FEX), then 32-bit x86, then any.
exe=""
for arch in x86_64 i386 ''; do
    exe=$(find /usr/lib64 /usr/lib -path "*${arch}-windows/hostname.exe" 2>/dev/null | head -n1)
    [ -n "$exe" ] && break
done
[ -n "$exe" ]
echo "test program: $exe"
useradd -m anna
as_anna() { runuser -u anna -- env HOME=/home/anna USER=anna LANG=C.UTF-8 "$@"; }

step "lucent-bridge 0.2 pieces: filtered-token helper, bundled DXVK, launch sheet"
test -f /usr/share/lucent-bridge/windows/lucent-start.exe
command -v lucent-bridge-sheet
if [ "$(uname -m)" = x86_64 ]; then
    test -f /usr/share/lucent-bridge/dxvk/x64/d3d11.dll
    test -f /usr/share/lucent-bridge/dxvk/x32/d3d11.dll
fi
# A GUI program (Wine's own notepad) starts through lucent-start.exe, like
# Windows starts programs for an administrator with UAC: not elevated.
gui=$(find /usr/lib64 /usr/lib -path '*x86_64-windows/notepad.exe' 2>/dev/null | head -n1)
if [ -n "$gui" ]; then
    as_anna lucent-bridge plan --json "$gui" | grep -q 'lucent-start\.exe'
fi

step "launch before the template exists (wineboot fallback)"
as_anna lucent-bridge plan "$exe"
t0=$(date +%s%N)
as_anna lucent-bridge run -- "$exe"
echo "first launch without template: $(( ($(date +%s%N) - t0) / 1000000 )) ms"

step "build the prefix template the way lucent-bridge-template.service does"
# A system service's environment: no HOME, no XDG variables (a real boot
# showed lucent-bridge 0.1.0 refusing to build there).
as_service() { env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin LANG=C.UTF-8 "$@"; }
as_service /usr/libexec/lucent/bridge-template
test -f /usr/share/lucent-bridge/prefix-template/system.reg
as_service /usr/libexec/lucent/bridge-template | tee /tmp/second-run
grep -q 'is current' /tmp/second-run   # no rebuild when nothing changed

step "launch from the template (new prefix for a different user)"
useradd -m boris
plan=$(runuser -u boris -- env HOME=/home/boris USER=boris lucent-bridge plan "$exe")
echo "$plan"
grep -q 'prefix-template' <<<"$plan"
t0=$(date +%s%N)
runuser -u boris -- env HOME=/home/boris USER=boris LANG=C.UTF-8 lucent-bridge run -- "$exe"
echo "first launch with template: $(( ($(date +%s%N) - t0) / 1000000 )) ms"
test -d /home/boris/.local/share/lucent-bridge/prefixes/*/drive_c/users/boris

step "systemd units"
systemd-analyze verify \
    /usr/lib/systemd/system/lucent-bridge-template.service \
    /usr/lib/systemd/system/lucent-bridge-template.timer \
    /usr/lib/systemd/system/lucent-flatpak-setup.service \
    /usr/lib/systemd/system/lucent-flatpak-relabel.service \
    /usr/lib/systemd/system/lucent-drive-letters.service
systemctl is-enabled lucent-bridge-template.timer lucent-flatpak-setup.service lucent-flatpak-relabel.service
if systemctl cat mcelog.service >/dev/null 2>&1; then
    systemctl cat mcelog.service | grep -q 'ExecCondition=.*GenuineIntel'
fi

step "boot and idle (docs/performance.md)"
# systemd-remount-fs: skipped for a composefs / listed in fstab, run otherwise.
systemctl cat systemd-remount-fs.service | grep -q '^ExecCondition=/usr/libexec/lucent/remount-fs-needed$'
printf 'UUID=x / btrfs subvol=root,compress=zstd:1,ro 0 0\nUUID=y /boot ext4 defaults 1 2\n' > /tmp/fstab.test
if LUCENT_ROOT_FSTYPE=overlay /usr/libexec/lucent/remount-fs-needed /tmp/fstab.test; then
    echo "remount-fs-needed should skip a composefs / line"; exit 1
fi
/usr/libexec/lucent/fstab-drop-root /tmp/fstab.test
LUCENT_ROOT_FSTYPE=overlay /usr/libexec/lucent/remount-fs-needed /tmp/fstab.test
grep -q '^#UUID=x / btrfs' /tmp/fstab.test && grep -q '^UUID=y /boot' /tmp/fstab.test
rm /tmp/fstab.test
# Power profiles from power-profiles-daemon; no TuneD.
rpm -q power-profiles-daemon
systemctl is-enabled power-profiles-daemon.service
for p in tuned tuned-ppd; do if rpm -q "$p"; then exit 1; fi; done
# KDE Connect: the daemon starts at login only after pairing (user unit).
grep -q '^Hidden=true' /etc/xdg/autostart/org.kde.kdeconnect.daemon.desktop
test "$(systemctl --global is-enabled lucent-kdeconnect.service)" = enabled
# Initramfs without nouveau and its NVIDIA GSP firmware (105 MB on x86_64);
# Tegra SoC firmware (USB, video) on aarch64 is not nouveau's and stays.
initramfs=$(ls /usr/lib/modules/*/initramfs.img | head -n1)
lsinitrd "$initramfs" > /tmp/initramfs.list
if grep -E 'drm/nouveau/|firmware/nvidia/[^/]+/gsp/' /tmp/initramfs.list; then echo "nouveau is in the initramfs"; exit 1; fi
if [ "$(uname -m)" = x86_64 ]; then   # the other GPU drivers stay
    grep -q 'drm/amd/amdgpu/amdgpu.ko' /tmp/initramfs.list
    grep -q 'drm/i915/i915.ko' /tmp/initramfs.list
fi
echo "initramfs: $(( $(stat -c %s "$initramfs") / 1048576 )) MB"
rm /tmp/initramfs.list
# A hung app is killed after 10 s at logout/shutdown (no SIGABRT + second timeout).
grep -qx 'TimeoutStopFailureMode=kill' /usr/lib/systemd/user/service.d/50-lucent-stop-kill.conf
grep -qx 'DefaultTimeoutStopSec=10s' /usr/lib/systemd/user.conf.d/50-lucent-timeouts.conf
# Xwayland Video Bridge not autostarted; man-db/AppStream caches after the login.
xvb=/etc/xdg/autostart/org.kde.xwaylandvideobridge.desktop
if [ -f "$xvb" ]; then grep -q '^Hidden=true' "$xvb"; fi
systemd-analyze verify /usr/lib/systemd/system/lucent-after-boot.timer /usr/lib/systemd/system/lucent-after-boot.target
systemctl is-enabled lucent-after-boot.timer
for unit in fedora-atomic-desktop-mandb-update.service fedora-atomic-desktop-appstream-cache-refresh.service; do
    if systemctl cat "$unit" >/dev/null 2>&1; then test "$(systemctl is-enabled "$unit")" = disabled; fi
done

step "udev and polkit rules"
udevadm verify /usr/lib/udev/rules.d/99-lucent-windows-readonly.rules
test -r /usr/share/polkit-1/rules.d/50-lucent-windows-disks.rules

step "updates: staged in the background, applied at the next restart"
grep -qx 'AutomaticUpdatePolicy=stage' /etc/rpm-ostreed.conf
systemctl cat rpm-ostreed-automatic.service | grep -q 'ExecStart='
test -s /etc/containers/registries.d/lucent-os.yaml
if [ -f /etc/pki/containers/lucent-os.pub ]; then
    python3 -c 'import json, sys
p = json.load(open("/etc/containers/policy.json"))
assert p["default"] == [{"type": "reject"}], p["default"]
r = p["transports"]["docker"]["ghcr.io/sidun-av/lucent-os"][0]
assert r["type"] == "sigstoreSigned" and r["keyPath"] == "/etc/pki/containers/lucent-os.pub", r
assert p["transports"]["docker"][""] == [{"type": "insecureAcceptAnything"}]'
    echo "signature policy: updates must be signed with /etc/pki/containers/lucent-os.pub"
else
    echo "signature policy: no Lucent key in the image yet, updates are not signature-checked"
fi
updates_enabled() {
    systemctl is-enabled -q rpm-ostreed-automatic.timer
    state=$(systemctl is-enabled bootc-fetch-apply-updates.timer 2>/dev/null || true)
    echo "rpm-ostreed-automatic.timer: enabled; bootc-fetch-apply-updates.timer: ${state:-absent}"
    [ "$state" != enabled ]
}
updates_enabled
# First boot applies the presets (systemd: enable-only); they must not undo
# this. The container is thrown away, so applying them here is harmless.
systemctl preset-all --preset-mode=enable-only
updates_enabled

echo; echo "smoke test passed"
