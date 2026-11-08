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
# Wine is installed piecewise, NOT via the `wine` metapackage: that pulls
# wine-desktop -> wine-systemd, which registers its own binfmt handler for
# Windows (MZ) executables and would compete with the binfmt.d entry that
# lucent-bridge ships.
WINE_PKGS=(wine-core wine-common wine-winefonts wine-cms wine-ldap wine-smartcard
           wine-twain wine-mono)
OPTIONAL=()
case "$ARCH" in
    x86_64)
        INSTALL+=("${WINE_PKGS[@]}" wine-pulseaudio mingw64-wine-gecko)
        OPTIONAL+=(wine-opencl wine-dxvk mingw32-wine-gecko) ;;
    aarch64)
        # Windows x86/x64 apps on ARM: lucent-bridge's primary path is an
        # ARM64EC-enabled Wine + FEX's ARM64EC/WoW64 DLLs. Fedora proper
        # doesn't ship those yet; COPR lacamar/wine-arm64ec does (it has a
        # fedora-45-aarch64 chroot). Its release tags ("-ec2") sort *below*
        # Fedora's ("-1.fc45"), so the repo gets a higher priority instead.
        # TODO: drop the COPR once Fedora builds Wine with ARM64EC.
        FEDORA=$(rpm -E %fedora)
        curl -fsSL "https://copr.fedorainfracloud.org/coprs/lacamar/wine-arm64ec/repo/fedora-$FEDORA/lacamar-wine-arm64ec-fedora-$FEDORA.repo" \
            -o /etc/yum.repos.d/lacamar-wine-arm64ec.repo
        echo "priority=10" >> /etc/yum.repos.d/lacamar-wine-arm64ec.repo
        INSTALL+=("${WINE_PKGS[@]}" fex-emu fex-emu-wine)
        OPTIONAL+=(wine-dxvk)
        # The x86 rootfs (fex-emu-rootfs-fedora, ~1 GB) is fetched by
        # lucent-bridge on demand instead of bloating every ARM image.
        ;;
esac
"$DNF" "${DNF_OPTS[@]}" install "${INSTALL[@]}"
"$DNF" "${DNF_OPTS[@]}" install --skip-unavailable "${OPTIONAL[@]}"
if rpm -q wine-systemd; then echo "wine-systemd must not be installed (binfmt clash with lucent-bridge)"; exit 1; fi
if [ "$ARCH" = aarch64 ]; then
    rpm -q --qf '%{NAME}-%{VERSION}-%{RELEASE} from %{VENDOR}\n' wine-core fex-emu-wine
fi

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
# Lucent's own UI is written in English; translations (po/*.po) are compiled
# to /usr/share/locale/<lang>/LC_MESSAGES/lucent.mo and picked by locale.
PYTHONPATH=/usr/lib/lucent python3 -P -m lucent_migrate.i18n /ctx/migration-wizard/po /usr/share/locale
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
# Fedora 45 ships its repo definitions only in /usr/share/dnf5/repos.d, but
# bootc-image-builder (anaconda-iso) depsolves the installer from
# /etc/yum.repos.d and fails with "no enabled repositories". Same-named
# files in /etc simply override /usr for dnf5, so this adds no duplicates.
for repo in /usr/share/dnf5/repos.d/*.repo; do
    [ -e "/etc/yum.repos.d/${repo##*/}" ] || cp -a "$repo" /etc/yum.repos.d/
done
# Keep the shipped repo set clean (updates come from rebuilt images anyway).
[ -f /etc/yum.repos.d/lacamar-wine-arm64ec.repo ] && sed -i 's/^enabled=1/enabled=0/' /etc/yum.repos.d/lacamar-wine-arm64ec.repo
"$DNF" clean all
rm -rf /var/cache/* /var/log/* /var/lib/dnf /tmp/* /var/tmp/*
