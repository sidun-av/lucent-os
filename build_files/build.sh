#!/usr/bin/bash
# Lucent OS image build, run once inside the Containerfile.
# Build context is bind-mounted at /ctx (read-only).
set -xeuo pipefail

ARCH=$(uname -m)
DNF=$(command -v dnf5 || command -v dnf)
# Never let `remove` autoremove "unused" deps: in an image built by
# rpm-ostree the install-reason database is incomplete, and dnf would
# happily strip half of Plasma.
DNF_OPTS=(-y --setopt=install_weak_deps=False --setopt=clean_requirements_on_remove=False)

echo "== Base image packages (for the build log) =="
rpm -qa --qf '%{NAME}\n' | sort > /tmp/base-packages.txt
wc -l /tmp/base-packages.txt

# ---------------------------------------------------------------------------
# 1. Declutter. Removed only if the base image actually contains them.
# ---------------------------------------------------------------------------
REMOVE=(
    # Replaced by Flathub builds (one source, upstream-maintained, sandboxed)
    firefox firefox-langpacks okular
    # Donation/"welcome" nag screens and Fedora-specific promo pages
    plasma-welcome plasma-welcome-fedora
    # Crash reporters that upload data (on consent) to Fedora/KDE servers
    abrt abrt-desktop abrt-cli abrt-gui abrt-libs abrt-addon-ccpp abrt-addon-kerneloops
    abrt-addon-pstoreoops abrt-addon-vmcore abrt-addon-xorg abrt-dbus abrt-plugin-bodhi
    abrt-tui gnome-abrt plasma-drkonqi
    # Games
    kmahjongg kpat kmines kpatience ksudoku kbounce
    # Rarely used for this audience; all still installable from Flathub
    kjournald neochat kamoso krfb akregator kmail kontact korganizer kaddressbook
    mediawriter kde-inotify-survey
)
present=()
for p in "${REMOVE[@]}"; do rpm -q "$p" &>/dev/null && present+=("$p"); done
if ((${#present[@]})); then
    "$DNF" "${DNF_OPTS[@]}" remove "${present[@]}"
fi

# ---------------------------------------------------------------------------
# 2. Add what Lucent needs.
# ---------------------------------------------------------------------------
INSTALL=(
    rsms-inter-fonts jetbrains-mono-fonts   # UI and monospace fonts
    python3-pyside6                         # migration wizard GUI
    ntfsprogs                               # ntfsls: find the Windows (C:) volume without mounting
    udisks2 ntfs-3g                         # read-only Windows disk access (normally present)
)
case "$ARCH" in
    x86_64)
        # Windows apps: plain Wine. lucent-bridge (below) adds the friendly layer.
        INSTALL+=(wine) ;;
    aarch64)
        # Windows (x86) apps on ARM: FEX-Emu x86 emulator, packaged by Fedora.
        # The x86 rootfs (fex-emu-rootfs-fedora, ~1 GB) is fetched by
        # lucent-bridge on demand instead of bloating every ARM image.
        INSTALL+=(fex-emu) ;;
esac
"$DNF" "${DNF_OPTS[@]}" install "${INSTALL[@]}"

# ---------------------------------------------------------------------------
# 3. ===== LUCENT-BRIDGE HOOK =====
# The sibling project lucent-bridge (Wine on x86_64, FEX+Wine on aarch64)
# will ship as an RPM. Until it is published to a repo, CI or a developer
# drops it into ./rpms/ and it gets installed here. When a COPR/repo exists,
# replace this block with: dnf install lucent-bridge
# ---------------------------------------------------------------------------
shopt -s nullglob
bridge=(/ctx/rpms/lucent-bridge-*."$ARCH".rpm /ctx/rpms/lucent-bridge-*.noarch.rpm)
if ((${#bridge[@]})); then
    "$DNF" "${DNF_OPTS[@]}" install "${bridge[@]}"
else
    echo "LUCENT-BRIDGE HOOK: no lucent-bridge RPM in ./rpms, skipping"
fi
shopt -u nullglob

# ---------------------------------------------------------------------------
# 4. Lucent components and services
# ---------------------------------------------------------------------------
python3 -m compileall -q /usr/lib/lucent   # /usr is read-only at runtime
python3 /ctx/build_files/make_wallpaper.py /usr/share/wallpapers/Lucent/contents
gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true

systemctl enable lucent-flatpak-setup.service lucent-drive-letters.service

# Privacy: Fedora's "countme" sends a weekly anonymous ping used to count
# installations. Lucent promises no telemetry, so it is masked.
for unit in rpm-ostree-countme.timer rpm-ostree-countme.service; do
    if systemctl cat "$unit" &>/dev/null; then systemctl mask "$unit"; fi
done
sed -i 's/^countme=.*/countme=0/' /etc/dnf/dnf.conf 2>/dev/null || true

# Identify the OS while keeping ID=fedora so Fedora tooling keeps working.
sed -i \
    -e 's/^PRETTY_NAME=.*/PRETTY_NAME="Lucent OS 0.1 (prototype, Fedora '"$(rpm -E %fedora)"' base)"/' \
    -e 's/^VARIANT=.*/VARIANT="Lucent"/' \
    -e 's/^VARIANT_ID=.*/VARIANT_ID=lucent/' \
    /usr/lib/os-release
grep -q '^VARIANT_ID=' /usr/lib/os-release || echo 'VARIANT_ID=lucent' >> /usr/lib/os-release

# ---------------------------------------------------------------------------
# 5. Clean up (bootc wants an empty /var and /tmp in the image)
# ---------------------------------------------------------------------------
"$DNF" clean all
rm -rf /var/cache/* /var/log/* /var/lib/dnf /tmp/* /var/tmp/*
