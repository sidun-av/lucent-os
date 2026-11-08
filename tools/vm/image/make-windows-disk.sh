#!/usr/bin/bash
# Build a small fake "Windows" disk (GPT + one NTFS partition with a
# Windows\System32 dir and a user profile) so the VM test can check that the
# migration wizard autostarts on first login and finds something to move.
# Runs on a Linux CI runner as root; needs ntfs-3g, util-linux, qemu-utils.
# Usage: make-windows-disk.sh OUT.qcow2
set -euo pipefail
out=$1
raw=$(mktemp --suffix=.raw)
mnt=$(mktemp -d)
trap 'umount "$mnt" 2>/dev/null || true; [ -n "${loop:-}" ] && losetup -d "$loop"; rm -f "$raw"; rmdir "$mnt"' EXIT

# > 1 GiB: lucent-drive-letters ignores smaller (OEM tool) partitions.
truncate -s 4G "$raw"
# Microsoft basic data partition
echo 'type=EBD0A0A2-B9E5-4433-87C0-68B6B72699C7, name="Basic data partition"' | sfdisk -q -X gpt "$raw"
loop=$(losetup -fP --show "$raw")
mkntfs -Q -F -L Windows "${loop}p1" >/dev/null
mount -t ntfs-3g "${loop}p1" "$mnt"

mkdir -p "$mnt/Windows/System32" "$mnt/Users/Public/Documents" "$mnt/Users/Default"
u="$mnt/Users/Anna"
mkdir -p "$u/Desktop" "$u/Documents/Работа" "$u/Pictures/Отпуск" "$u/Downloads" "$u/Music" "$u/Videos" \
         "$u/AppData/Local/Google/Chrome/User Data/Default"
: > "$u/NTUSER.DAT"
echo "Договор аренды" > "$u/Documents/Работа/Договор аренды 2026.txt"
echo "Бюджет" > "$u/Documents/Семейный бюджет.csv"
printf 'P1\n2 2\n1 0\n0 1\n' > "$u/Pictures/Отпуск/Сочи-014.pbm"
echo "list" > "$u/Desktop/Список покупок.txt"
echo "desktop.ini junk" > "$u/Desktop/desktop.ini"
cat > "$u/AppData/Local/Google/Chrome/User Data/Default/Bookmarks" <<'EOF'
{"roots": {"bookmark_bar": {"type": "folder", "name": "Bookmarks bar", "children": [
  {"type": "url", "name": "Госуслуги", "url": "https://www.gosuslugi.ru/"},
  {"type": "url", "name": "Wikipedia", "url": "https://ru.wikipedia.org/"}]},
 "other": {"type": "folder", "name": "Other", "children": []}}, "version": 1}
EOF
sync
umount "$mnt"
qemu-img convert -O qcow2 "$raw" "$out"
ls -la "$out"
