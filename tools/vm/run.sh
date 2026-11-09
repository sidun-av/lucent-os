#!/usr/bin/env bash
# Start the Lucent OS test VM headless (VNC 127.0.0.1:590$LUCENT_VM_VNC_DISPLAY,
# QMP socket, SSH on 127.0.0.1:$LUCENT_VM_SSH_PORT).
# Usage: run.sh [--fresh] [--no-windows-disk] | run.sh --stop
#   --fresh   throw away the overlay = boot as if for the very first time
set -euo pipefail
. "$(dirname "$0")/lib.sh"
fresh=0 windisk=1
for a in "$@"; do
    case "$a" in
        --fresh) fresh=1 ;;
        --no-windows-disk) windisk=0 ;;
        --stop)
            if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
                qmp system_powerdown >/dev/null || true
                for _ in $(seq 60); do kill -0 "$(cat "$PIDFILE")" 2>/dev/null || break; sleep 1; done
                kill "$(cat "$PIDFILE")" 2>/dev/null || true
            fi
            rm -f "$PIDFILE" "$QMP"; echo stopped; exit 0 ;;
        *) echo "unknown option $a" >&2; exit 2 ;;
    esac
done
[ -f "$BASE" ] || { echo "no $BASE — run fetch.sh first" >&2; exit 1; }
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "already running (pid $(cat "$PIDFILE"))"; exit 0
fi
share=$(brew --prefix qemu)/share/qemu
vars="$LUCENT_VM_DIR/vars-$LUCENT_VM_ARCH.fd"
if ((fresh)); then rm -f "$DISK" "$WINDISK" "$vars"; fi
[ -f "$DISK" ] || qemu-img create -q -f qcow2 -F qcow2 -b "$BASE" "$DISK"
[ -f "$vars" ] || cp "$share/edk2-arm-vars.fd" "$vars"
drives=(-drive "if=virtio,file=$DISK,discard=unmap,cache=writeback")
if ((windisk)) && [ -f "$WINBASE" ]; then
    [ -f "$WINDISK" ] || qemu-img create -q -f qcow2 -F qcow2 -b "$WINBASE" "$WINDISK"
    drives+=(-drive "if=virtio,file=$WINDISK")
fi
rm -f "$QMP"
qemu-system-aarch64 \
    -name "lucent-$(basename "$LUCENT_VM_DIR")" -M virt,highmem=on -accel hvf -cpu host -smp "$LUCENT_VM_CPUS" -m "$LUCENT_VM_MEM" \
    -drive "if=pflash,format=raw,readonly=on,file=$share/edk2-aarch64-code.fd" \
    -drive "if=pflash,format=raw,file=$vars" \
    "${drives[@]}" \
    -device "virtio-gpu-pci,xres=${LUCENT_VM_RES%x*},yres=${LUCENT_VM_RES#*x}" \
    -device qemu-xhci -device usb-kbd -device usb-tablet \
    -netdev "user,id=n0,hostfwd=tcp:127.0.0.1:$LUCENT_VM_SSH_PORT-:22" -device virtio-net-pci,netdev=n0 \
    -device virtio-rng-pci \
    -display none -vnc "127.0.0.1:$LUCENT_VM_VNC_DISPLAY" \
    -qmp "unix:$QMP,server=on,wait=off" \
    -serial "file:$LUCENT_VM_DIR/serial.log" \
    -daemonize -pidfile "$PIDFILE"
echo "started pid $(cat "$PIDFILE"): VNC 127.0.0.1:590$LUCENT_VM_VNC_DISPLAY, ssh via $(dirname "$0")/ssh.sh, serial log $LUCENT_VM_DIR/serial.log"
