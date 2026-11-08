#!/usr/bin/env bash
# SSH into the VM as `lucent`. With --session, the command runs inside the
# user's Plasma session environment (D-Bus, Wayland) so qdbus/kreadconfig work.
# Usage: ssh.sh [--session] [COMMAND...]
set -euo pipefail
. "$(dirname "$0")/lib.sh"
pre=
if [ "${1:-}" = --session ]; then
    shift
    pre='export XDG_RUNTIME_DIR=/run/user/$(id -u); export DBUS_SESSION_BUS_ADDRESS=unix:path=$XDG_RUNTIME_DIR/bus QT_QPA_PLATFORM=wayland; for s in $XDG_RUNTIME_DIR/wayland-?; do export WAYLAND_DISPLAY=${s##*/}; done; '
fi
opts=(-i "$LUCENT_VM_KEY" -p "$LUCENT_VM_SSH_PORT" -o IdentitiesOnly=yes
      -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR
      -o ConnectTimeout=5)
if [ -n "$pre" ]; then
    exec ssh "${opts[@]}" lucent@127.0.0.1 "$pre$*"
fi
exec ssh "${opts[@]}" lucent@127.0.0.1 "$@"
