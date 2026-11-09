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
# 2. No Xwayland Video Bridge in every session.
# It lets X11-only apps (Webex and the like) screen-share Wayland windows,
# runs from login to logout either way, and was the third-largest process of
# an idle desktop (58 MiB PSS, after plasmashell and KWin). KDE has archived
# it and recommends distributions stop shipping it; Firefox, OBS and current
# Chromium-based apps share the screen through the desktop portal without
# it. The package stays: copying its entry to ~/.config/autostart (without
# Hidden=true) turns it back on.
# ---------------------------------------------------------------------------
xvb=/etc/xdg/autostart/org.kde.xwaylandvideobridge.desktop
if [ -f "$xvb" ]; then
    grep -q '^Hidden=true' "$xvb" || sed -i '0,/^\[Desktop Entry\]/s//[Desktop Entry]\nHidden=true/' "$xvb"
fi

# ---------------------------------------------------------------------------
# 3. Housekeeping Fedora runs at every boot, 5 minutes after boot instead.
# fedora-atomic-desktop-mandb-update (`mandb -q`), -appstream-cache-refresh
# (`appstreamcli refresh --force`) and fedora-third-party-refresh are
# oneshots in multi-user.target: on the first boot mandb alone held
# graphical.target for 7 s; with TuneD gone, third-party-refresh (0.8 s) was
# the last thing graphical.target waited for on every boot; and all of them
# compete with the login for CPU and disk. lucent-after-boot.timer starts
# them (through lucent-after-boot.target) when the desktop is idle.
# ---------------------------------------------------------------------------
for unit in fedora-atomic-desktop-mandb-update.service fedora-atomic-desktop-appstream-cache-refresh.service \
            fedora-third-party-refresh.service; do
    if systemctl cat "$unit" &>/dev/null; then systemctl disable "$unit"; fi
done
systemctl enable lucent-after-boot.timer
