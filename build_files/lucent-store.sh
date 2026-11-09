#!/usr/bin/bash
# Lucent Store (apps/lucent-store): the default "Store", replacing KDE
# Discover in the launcher and taskbar. Called by build.sh; context at /ctx.
set -xeuo pipefail
src=/ctx/apps/lucent-store

cp -a "$src/lucent_store" /usr/lib/lucent/
install -m 0755 "$src/data/lucent-store" /usr/bin/lucent-store
install -m 0644 "$src/data/org.lucent.Store.desktop" /usr/share/applications/org.lucent.Store.desktop
# Translations: /usr/share/locale/<lang>/LC_MESSAGES/lucent-store.mo
PYTHONPATH=/usr/lib/lucent python3 -P -m lucent_store.i18n "$src/po" /usr/share/locale

# Discover stays installed (it still opens .flatpakref files and appstream://
# links) but leaves the launcher and search: the Store is the one place for apps.
f=/usr/share/applications/org.kde.discover.desktop
if [ -f "$f" ]; then
    # Discover's own entry says NoDisplay=false further down; with two keys
    # the last one wins (KService, GIO), so drop it before adding ours.
    sed -i '/^NoDisplay=/d' "$f"
    sed -i '0,/^\[Desktop Entry\]/s//[Desktop Entry]\nNoDisplay=true/' "$f"
    [ "$(grep -c '^NoDisplay=' "$f")" = 1 ]
fi

# The Qt modules the store needs are all in Fedora's python3-pyside6 and
# qt6-qtdeclarative; render one page offscreen to prove the QML loads.
python3 -c "import PySide6.QtQuick, PySide6.QtQuickControls2, PySide6.QtSvg"
out=$(mktemp -d)
HOME=$out XDG_CACHE_HOME=$out timeout 120 /usr/bin/lucent-store --fake --page home \
    --screenshot "$out/home.png" --size 1280x800 --delay 1500
test -s "$out/home.png"
rm -rf "$out"
