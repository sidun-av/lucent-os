#!/usr/bin/env bash
# Plug a USB stick image into the running VM, or pull it out again (QMP
# hotplug on the VM's xhci bus, as if a real stick were inserted/removed).
# Usage: usb.sh attach IMAGE.img | usb.sh detach
# Make an image on macOS:  mkfile -n 32g stick.img &&
#   newfs_msdos -F 32 -S 512 -s 67108864 -h 255 -u 63 -v KINGSTON stick.img
set -euo pipefail
. "$(dirname "$0")/lib.sh"
case "${1:-}" in
    attach)
        [ -f "${2:-}" ] || { echo "usage: usb.sh attach IMAGE" >&2; exit 2; }
        img=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
        qmp blockdev-add "{\"node-name\": \"usbstick\", \"driver\": \"raw\", \"file\": {\"driver\": \"file\", \"filename\": \"$img\"}}" >/dev/null
        qmp device_add '{"driver": "usb-storage", "drive": "usbstick", "id": "usbstick0", "removable": true}' >/dev/null
        echo "attached $img" ;;
    detach)
        qmp device_del '{"id": "usbstick0"}' >/dev/null || true
        sleep 2
        qmp blockdev-del '{"node-name": "usbstick"}' >/dev/null || true
        echo detached ;;
    *) echo "usage: usb.sh attach IMAGE | usb.sh detach" >&2; exit 2 ;;
esac
