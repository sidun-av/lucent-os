#!/usr/bin/env bash
# Send key combos to the VM via QMP send-key (QEMU qcode names, '-' joins a chord).
# Usage: keys.sh meta | meta-e | alt-tab | alt-shift | ctrl-alt-t | esc ...
#        keys.sh alt-tab:2500     (hold the chord 2.5 s, e.g. to screenshot the switcher)
#        keys.sh --type 'some text'
set -euo pipefail
. "$(dirname "$0")/lib.sh"
if [ "${1:-}" = --type ]; then shift; qmp type "$@"; else qmp keys "$@"; fi
