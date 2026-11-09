#!/usr/bin/env bash
# Render the Pebble Drift wallpapers (docs/mockups/concepts-2026/pebble-drift/
# drift-shell.js: Drift, Tide, Aurora, day and night) at 4K into the Plasma
# wallpaper packages in system_files/usr/share/wallpapers/{Drift,Tide,Aurora}.
# Needs Google Chrome (headless) and Python with Pillow.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
chrome=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cat > "$work/render.html" <<HTML
<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;overflow:hidden}#w{position:absolute;inset:0}#w svg{width:100%;height:100%;display:block}</style>
<script src="file://$repo/docs/mockups/lucent.js"></script>
<script src="file://$repo/docs/mockups/concepts-2026/pebble-drift/drift-shell.js"></script>
</head><body><div id="w"></div><script>
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('w').innerHTML = window.LucentDrift.WALLS[location.hash.slice(1)]();
});</script></body></html>
HTML
for key in drift tide aurora; do
    name=$(echo "${key:0:1}" | tr a-z A-Z)${key:1}
    for mode in light dark; do
        sub=images; [ "$mode" = dark ] && sub=images_dark
        mkdir -p "$repo/system_files/usr/share/wallpapers/$name/contents/$sub"
        for size in 3840x2160 3840x2400; do
            "$chrome" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
                --allow-file-access-from-files --virtual-time-budget=8000 --window-size="${size/x/,}" \
                --screenshot="$work/$key-$mode-$size.png" "file://$work/render.html#$key-$mode" >/dev/null 2>&1
            python3 -c 'import sys; from PIL import Image; Image.open(sys.argv[1]).convert("RGB").save(sys.argv[2], quality=90, optimize=True, progressive=True)' \
                "$work/$key-$mode-$size.png" "$repo/system_files/usr/share/wallpapers/$name/contents/$sub/$size.jpg"
        done
    done
done
