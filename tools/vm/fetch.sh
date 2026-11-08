#!/usr/bin/env bash
# Download the newest test VM image from CI (workflow "vm") into $LUCENT_VM_DIR.
# Usage: fetch.sh [RUN_ID]   (default: latest successful run on main)
set -euo pipefail
. "$(dirname "$0")/lib.sh"
run=${1:-$(gh run list -R "$LUCENT_VM_REPO" -w vm -s success -L 1 --json databaseId -q '.[0].databaseId')}
[ -n "$run" ] || { echo "no successful 'vm' run found" >&2; exit 1; }
name=lucent-os-vm-$LUCENT_VM_ARCH
mkdir -p "$LUCENT_VM_DIR"
tmp="$LUCENT_VM_DIR/.download-$run"
rm -rf "$tmp"
echo "downloading $name from run $run ..."
gh run download "$run" -R "$LUCENT_VM_REPO" -n "$name" -D "$tmp"
(cd "$tmp" && shasum -a 256 -c SHA256SUMS)
# Replace the previous image; its overlays are now stale.
rm -f "$BASE" "$WINBASE" "$DISK" "$WINDISK" "$LUCENT_VM_DIR/vars-$LUCENT_VM_ARCH.fd"
mv "$tmp/lucent-$LUCENT_VM_ARCH.qcow2" "$BASE"
mv "$tmp/windows-disk.qcow2" "$WINBASE"
echo "$run $(cat "$tmp/image-revision.txt" 2>/dev/null)" > "$LUCENT_VM_DIR/IMAGE-$LUCENT_VM_ARCH"
rm -rf "$tmp"
ls -la "$LUCENT_VM_DIR"
