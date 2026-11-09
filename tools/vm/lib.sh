# Shared settings for the Lucent OS VM harness. Sourced, not executed.
# Override any of these in the environment.
: "${LUCENT_VM_DIR:=$HOME/VMs/lucent}"
: "${LUCENT_VM_ARCH:=arm64}"
: "${LUCENT_VM_SSH_PORT:=2222}"
: "${LUCENT_VM_VNC_DISPLAY:=1}"          # VNC on 127.0.0.1:590N
: "${LUCENT_VM_RES:=1920x1080}"          # virtio-gpu mode; 2560x1440 matches docs/mockups
: "${LUCENT_VM_KEY:=$HOME/.ssh/lucent_vm_ed25519}"
: "${LUCENT_VM_REPO:=sidun-av/lucent-os}"
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BASE="$LUCENT_VM_DIR/lucent-$LUCENT_VM_ARCH.qcow2"     # pristine, from CI
DISK="$LUCENT_VM_DIR/run-$LUCENT_VM_ARCH.qcow2"        # overlay the VM writes to
WINBASE="$LUCENT_VM_DIR/windows-disk.qcow2"
WINDISK="$LUCENT_VM_DIR/run-windows-disk.qcow2"
QMP="$LUCENT_VM_DIR/qmp.sock"
PIDFILE="$LUCENT_VM_DIR/qemu.pid"
qmp() { python3 -I "$HERE/qmp.py" "$QMP" "$@"; }
