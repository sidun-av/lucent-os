#!/usr/bin/bash
# Lucent launch sheet (apps/lucent-bridge-sheet): the calm "Preparing Windows
# program" window lucent-bridge (>= 0.2) shows while it prepares a Windows
# program's first launch, and where it explains what can't work. The bridge
# finds it on PATH as lucent-bridge-sheet and writes its progress to the
# sheet's stdin. Called by build.sh; context at /ctx.
set -xeuo pipefail
src=/ctx/apps/lucent-bridge-sheet

cp -a "$src/lucent_bridge_sheet" /usr/lib/lucent/
install -m 0755 "$src/data/lucent-bridge-sheet" /usr/bin/lucent-bridge-sheet
# Translations: /usr/share/locale/<lang>/LC_MESSAGES/lucent-bridge-sheet.mo
PYTHONPATH=/usr/lib/lucent python3 -P -m lucent_bridge_sheet.i18n "$src/po" /usr/share/locale

# Render it offscreen, light and dark: proves PySide6, the Pebble Drift tokens
# (lucent_migrate) and the fonts load in the image.
out=$(mktemp -d)
for theme in light dark; do
    HOME=$out XDG_CACHE_HOME=$out QT_QPA_PLATFORM=offscreen timeout 120 \
        /usr/bin/lucent-bridge-sheet --preview preparing --theme "$theme" --out "$out/$theme.png"
    test -s "$out/$theme.png"
done
rm -rf "$out"
