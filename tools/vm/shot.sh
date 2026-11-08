#!/usr/bin/env bash
# Screenshot the VM display to PNG via QMP screendump.
# Usage: shot.sh OUT.png
set -euo pipefail
. "$(dirname "$0")/lib.sh"
out=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
qmp screendump "{\"filename\": \"$out\", \"format\": \"png\"}" >/dev/null
echo "$out"
