#!/usr/bin/bash
# TEST-ONLY (tests/devices/vm): record what udev and the kernel saw on this
# boot onto the disk labelled DEVOUT, run lucent-devices, power off.
set -u
udevadm settle -t 120
sleep 20   # late binds and firmware requests
out=/run/devout
mkdir -p "$out"
if ! mount LABEL=DEVOUT "$out"; then
    echo "lucent-devices-ci: no DEVOUT disk"
    systemctl poweroff
    exit 1
fi
udevadm info --export-db > "$out/udev.txt" 2>&1
journalctl -k -b 0 -o cat --no-pager > "$out/kernel.log" 2>&1
lspci -nnk > "$out/lspci.txt" 2>&1
{ lsusb; lsusb -t; } > "$out/lsusb.txt" 2>&1
uname -r > "$out/uname.txt"
rpm -qa --qf '%{NAME}\n' | sort > "$out/rpm-qa.txt"
if command -v lucent-devices > /dev/null; then
    lucent-devices --json > "$out/devices.json" 2> "$out/devices.err"
    echo "json rc=$?" >> "$out/devices.err"
    lucent-devices > "$out/devices.txt" 2>> "$out/devices.err"
    LANG=ru_RU.UTF-8 lucent-devices > "$out/devices.ru.txt" 2>> "$out/devices.err"
    # Without the right to read the kernel log it must say so, not guess.
    runuser -u nobody -- lucent-devices --json > "$out/devices-nobody.json" 2>> "$out/devices.err"
fi
ls -la "$out"
sync
umount "$out"
echo "lucent-devices-ci: done"
systemctl poweroff
