#!/usr/bin/bash
# TEST-ONLY (hardware-live), on the runner, as root.
#   sticks.sh make DIR    three 512 MB USB stick images as Windows formats
#                         them (MBR, one partition): FAT32, exFAT, NTFS, each
#                         with hello.txt on it
#   sticks.sh check DIR   after the test: is the file the computer wrote on
#                         each stick there, and is each file system clean
#                         (safely ejected)? One line per stick.
set -uo pipefail
cmd=$1 dir=$2
STICKS=("fat32 0c LUCENTFAT32" "exfat 07 LucentExFAT" "ntfs 07 LucentNTFS")
mnt=$(mktemp -d)
trap 'umount "$mnt" 2> /dev/null; rmdir "$mnt"' EXIT
for s in "${STICKS[@]}"; do
    read -r fs type label <<< "$s"
    img=$dir/stick-$fs.img
    if [ "$cmd" = make ]; then
        rm -f "$img"
        truncate -s 512M "$img"
        echo "type=$type" | sfdisk -q -X dos "$img"
        loop=$(losetup -fP --show "$img")
        for _ in $(seq 50); do [ -b "${loop}p1" ] && break; udevadm settle; sleep 0.1; done
        case $fs in
            fat32) mkfs.vfat -F 32 -n "$label" "${loop}p1" > /dev/null ;;
            exfat) mkfs.exfat -L "$label" "${loop}p1" > /dev/null ;;
            ntfs) mkntfs -Q -F -L "$label" "${loop}p1" > /dev/null ;;
        esac
        mount "${loop}p1" "$mnt"
        echo "Hello from a $fs stick made on the runner" > "$mnt/hello.txt"
        umount "$mnt"
        losetup -d "$loop"
        chown "${SUDO_UID:-0}:${SUDO_GID:-0}" "$img"
        echo "$fs: $img ($label)"
    else
        loop=$(losetup -fP --show "$img")
        for _ in $(seq 50); do [ -b "${loop}p1" ] && break; udevadm settle; sleep 0.1; done
        case $fs in
            fat32) clean=$(fsck.vfat -n "${loop}p1" 2>&1) ;;
            exfat) clean=$(fsck.exfat -n "${loop}p1" 2>&1) ;;
            ntfs) clean=$(ntfsfix -n "${loop}p1" 2>&1) ;;
        esac
        clean="rc=$? $(tr '\n\t' '  ' <<< "$clean")"
        mount -o ro "${loop}p1" "$mnt"
        written=$(cat "$mnt/written-by-lucent.txt" 2> /dev/null || echo MISSING)
        umount "$mnt"
        losetup -d "$loop"
        printf '%s\t%s\t%s\n' "$fs" "$written" "$clean"
    fi
done
