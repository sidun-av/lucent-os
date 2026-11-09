#!/usr/bin/bash
# Lucent Settings (apps/lucent-settings): the default "Settings", replacing
# KDE System Settings in the launcher and taskbar. Called by build.sh;
# context at /ctx.
set -xeuo pipefail
src=/ctx/apps/lucent-settings

cp -a "$src/lucent_settings" /usr/lib/lucent/
install -m 0755 "$src/data/lucent-settings" /usr/bin/lucent-settings
install -m 0644 "$src/data/org.lucent.Settings.desktop" /usr/share/applications/org.lucent.Settings.desktop
# The one root-only change (automatic updates on/off) goes through pkexec.
install -D -m 0755 "$src/data/settings-helper" /usr/libexec/lucent/settings-helper
install -D -m 0644 "$src/data/org.lucent.settings.policy" /usr/share/polkit-1/actions/org.lucent.settings.policy
# Keeps a chosen accent colour when Auto switches light/dark at sunset.
install -m 0644 "$src/data/lucent-settings-accent.path" "$src/data/lucent-settings-accent.service" \
    /usr/lib/systemd/user/
systemctl --global enable lucent-settings-accent.path

# Translations: /usr/share/locale/<lang>/LC_MESSAGES/lucent-settings.mo, with
# the migration wizard's .mo writer (no gettext tools in the image).
for po in "$src"/po/*.po; do
    lang=$(basename "$po" .po)
    PYTHONPATH=/usr/lib/lucent python3 -P -c \
        'import sys; from pathlib import Path; from lucent_migrate.i18n import compile_po; compile_po(Path(sys.argv[1]), Path(sys.argv[2]))' \
        "$po" "/usr/share/locale/$lang/LC_MESSAGES/lucent-settings.mo"
done

# KDE System Settings stays installed (Settings' "Advanced settings…" opens
# it, and so do Plasma's own "Configure…" entries) but leaves the launcher.
f=/usr/share/applications/systemsettings.desktop
if [ -f "$f" ]; then
    grep -q '^NoDisplay=true' "$f" || sed -i '0,/^\[Desktop Entry\]/s//[Desktop Entry]\nNoDisplay=true/' "$f"
fi

# Checks: the tools the backends drive are in the image, and every page's
# QML loads offscreen with this image's Qt (no QML warning allowed).
for tool in nmcli busctl kscreen-doctor wpctl pactl rpm-ostree flatpak kwriteconfig6 \
            plasma-apply-lookandfeel plasma-apply-colorscheme plasma-apply-wallpaperimage lscpu pkexec; do
    command -v "$tool"
done
python3 -c "import PySide6.QtQuick, PySide6.QtQuickControls2, PySide6.QtSvg, PySide6.QtDBus"
out=$(mktemp -d)
HOME=$out XDG_CONFIG_HOME=$out XDG_CACHE_HOME=$out XDG_STATE_HOME=$out timeout 120 /usr/bin/lucent-settings --check
rm -rf "$out"
