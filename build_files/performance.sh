#!/usr/bin/bash
# Lucent OS: boot time and idle memory. Called by build.sh; context at /ctx.
# docs/performance.md has the before/after numbers and the reasoning for
# every change; each one is checked here so a base-image change can't undo
# it silently.
set -xeuo pipefail
DNF=$(command -v dnf5 || command -v dnf)
DNF_OPTS=(-y --setopt=install_weak_deps=False --setopt=clean_requirements_on_remove=False)

# ---------------------------------------------------------------------------
# 1. Power profiles: power-profiles-daemon instead of TuneD + tuned-ppd.
# Both serve the same D-Bus API (org.freedesktop.UPower.PowerProfiles) that
# Plasma's battery applet and PowerDevil use: Power Save / Balanced /
# Performance, battery-aware. TuneD is two resident Python daemons, and on a
# bootc system it runs `rpm-ostree status` and `bootc loader-entries
# set-options-for-source` at every profile change, three times per boot:
# that starts rpm-ostreed, remounts /boot read-write, and bootc's SELinux
# self-test (chcon to an invalid label) is denied in tuned_t: six AVC
# denials plus six SELINUX_ERR records on every boot.
# ---------------------------------------------------------------------------
if rpm -q tuned-ppd &>/dev/null; then
    "$DNF" "${DNF_OPTS[@]}" swap tuned-ppd power-profiles-daemon
fi
if rpm -q tuned &>/dev/null; then
    # Nothing else may need it (dnf would quietly remove that too).
    needs=$(rpm -q --whatrequires tuned --qf '%{NAME}\n' | grep -v '^no package' || true)
    if [ -n "$needs" ]; then echo "tuned is still required by: $needs"; exit 1; fi
    "$DNF" "${DNF_OPTS[@]}" remove tuned
fi
systemctl enable power-profiles-daemon.service
rpm -q power-profiles-daemon
for p in tuned tuned-ppd; do
    if rpm -q "$p" &>/dev/null; then echo "$p must not be installed (power-profiles-daemon serves the API)"; exit 1; fi
done

# ---------------------------------------------------------------------------
# 2. KDE Connect's daemon only once a phone is paired.
# Fedora autostarts kdeconnectd in every session: memory, and the computer
# announced on the local network although most people never pair a phone.
# lucent-kdeconnect.service (user unit) starts it at login when
# ~/.config/kdeconnect/trusted_devices exists; before that, opening KDE
# Connect starts it over D-Bus, so pairing works as before.
# ---------------------------------------------------------------------------
kdc=/etc/xdg/autostart/org.kde.kdeconnect.daemon.desktop
test -f "$kdc"
test -f /usr/share/dbus-1/services/org.kde.kdeconnect.service
grep -q '^Exec=/usr/bin/kdeconnectd$' "$kdc"
grep -q '^Hidden=true' "$kdc" || sed -i '0,/^\[Desktop Entry\]/s//[Desktop Entry]\nHidden=true/' "$kdc"
systemctl --global enable lucent-kdeconnect.service
