#!/usr/bin/env bash
# Move the VM's pointer and click (usb-tablet, absolute coordinates in pixels).
# Usage: click.sh X Y [left|right|middle]  |  click.sh --move X Y  |  click.sh --drag X1 Y1 X2 Y2
set -euo pipefail
. "$(dirname "$0")/lib.sh"
what=click
if [ "${1:-}" = --move ]; then what=move; shift; fi
if [ "${1:-}" = --drag ]; then shift; qmp drag "$1" "$2" "$3" "$4" "${LUCENT_VM_RES%x*}" "${LUCENT_VM_RES#*x}"; exit; fi
qmp "$what" "$1" "$2" "${LUCENT_VM_RES%x*}" "${LUCENT_VM_RES#*x}" "${3:-left}"
