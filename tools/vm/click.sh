#!/usr/bin/env bash
# Move the VM's pointer and click (usb-tablet, absolute coordinates in pixels).
# Usage: click.sh X Y [left|right|middle]   |   click.sh --move X Y
set -euo pipefail
. "$(dirname "$0")/lib.sh"
what=click
if [ "${1:-}" = --move ]; then what=move; shift; fi
qmp "$what" "$1" "$2" "${LUCENT_VM_RES%x*}" "${LUCENT_VM_RES#*x}" "${3:-left}"
