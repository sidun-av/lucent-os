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

step "launch before the template exists (wineboot fallback)"
as_anna lucent-bridge plan "$exe"
t0=$(date +%s%N)
as_anna lucent-bridge run -- "$exe"
echo "first launch without template: $(( ($(date +%s%N) - t0) / 1000000 )) ms"

step "build the prefix template the way lucent-bridge-template.service does"
/usr/libexec/lucent/bridge-template
test -f /usr/share/lucent-bridge/prefix-template/system.reg
/usr/libexec/lucent/bridge-template | tee /tmp/second-run
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

step "udev and polkit rules"
udevadm verify /usr/lib/udev/rules.d/99-lucent-windows-readonly.rules
test -r /usr/share/polkit-1/rules.d/50-lucent-windows-disks.rules

echo; echo "smoke test passed"
