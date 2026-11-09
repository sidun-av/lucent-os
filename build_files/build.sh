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
    zstd                                    # unpacks the installer's offline app bundle (iso/)
)
# Wine is installed piecewise, NOT via the `wine` metapackage: that pulls
# wine-desktop -> wine-systemd, which registers its own binfmt handler for
# Windows (MZ) executables and would compete with the binfmt.d entry that
# lucent-bridge ships (its RPM conflicts with wine-systemd).
WINE_PKGS=(wine-core wine-common wine-winefonts wine-cms wine-ldap wine-smartcard
           wine-twain wine-mono)
OPTIONAL=()
case "$ARCH" in
    x86_64)
        # Gecko (both bitnesses) and DXVK are required, not optional: a
        # first launch must never ask to download anything, and Direct3D
        # 9-11 apps need DXVK. lucent-bridge's E2E installs exactly this set
        # on Fedora 45.
        INSTALL+=("${WINE_PKGS[@]}" wine-pulseaudio mingw64-wine-gecko mingw32-wine-gecko wine-dxvk)
        OPTIONAL+=(wine-opencl) ;;
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
        INSTALL+=("${WINE_PKGS[@]}" fex-emu fex-emu-wine wine-dxvk)
        # The x86 rootfs (fex-emu-rootfs-fedora, ~1 GB) is only needed by
        # lucent-bridge's fallback runner, so it is not in every ARM image.
        ;;
esac
"$DNF" "${DNF_OPTS[@]}" install "${INSTALL[@]}"
if ((${#OPTIONAL[@]})); then
    "$DNF" "${DNF_OPTS[@]}" install --skip-unavailable "${OPTIONAL[@]}"
fi
if [ "$ARCH" = aarch64 ]; then
    rpm -q --qf '%{NAME}-%{VERSION}-%{RELEASE} from %{VENDOR}\n' wine-core fex-emu-wine wine-dxvk
fi

# Fedora's wine-dxvk %posttrans asks `vulkaninfo` for a GPU; in an image
# build there is none, so it registers DXVK *below* wined3d and every
# machine would silently run Direct3D on wined3d. Switch the alternatives
# to DXVK (lucent-bridge's script), then prove it took.
/ctx/build_files/enable-dxvk.sh
shopt -s nullglob
d3d11_links=(/etc/alternatives/wine-d3d11*)
shopt -u nullglob
if ((${#d3d11_links[@]})); then
    # Fedora's wine-dxvk covers 64-bit programs only; the 32-bit (x86-32)
    # alternative has no DXVK candidate and stays on wined3d. 64-bit must
    # be DXVK.
    for link in "${d3d11_links[@]}"; do echo "${link##*/} -> $(readlink -f "$link")"; done
    # The 64-bit alternative is named after the native PE arch:
    # wine-d3d11(x86-64) on x86_64, wine-d3d11(aarch-64) on aarch64.
    case "$ARCH" in aarch64) d3d11_64='wine-d3d11(aarch-64)' ;; *) d3d11_64='wine-d3d11(x86-64)' ;; esac
    d3d11=$(readlink -f "/etc/alternatives/$d3d11_64" || true)
    case "$d3d11" in
        *dxvk*) ;;
        *) echo "DXVK is not the 64-bit Direct3D 11 implementation (got: ${d3d11:-nothing})"; exit 1 ;;
    esac
else
    # No alternatives at all: wine-dxvk installs its DLLs directly (the
    # aarch64 COPR build does this, as in lucent-bridge's E2E).
    rpm -ql wine-dxvk | grep -i 'd3d11.*\.dll' | head -n3
fi

# ---------------------------------------------------------------------------
# 3. Lucent Bridge: double-click a Windows .exe/.msi and it runs.
# Release RPM from GitHub, verified against the release's SHA256SUMS and
# against the hashes pinned in build_files/lucent-bridge.sha256.
# ---------------------------------------------------------------------------
PIN=/ctx/build_files/lucent-bridge.sha256
BRIDGE_VERSION=$(awk '$1 == "version" {print $2}' "$PIN")
BRIDGE_RPM="lucent-bridge-$BRIDGE_VERSION-1.fc$(rpm -E %fedora).$ARCH.rpm"
BRIDGE_URL="https://github.com/sidun-av/lucent-bridge/releases/download/v$BRIDGE_VERSION"
dl=$(mktemp -d)
curl -fsSL --retry 3 -o "$dl/$BRIDGE_RPM" "$BRIDGE_URL/$BRIDGE_RPM"
curl -fsSL --retry 3 -o "$dl/SHA256SUMS" "$BRIDGE_URL/SHA256SUMS"
pinned=$(awk -v f="$BRIDGE_RPM" '$2 == f {print $1}' "$PIN")
released=$(awk -v f="$BRIDGE_RPM" '$2 == f {print $1}' "$dl/SHA256SUMS")
actual=$(sha256sum "$dl/$BRIDGE_RPM" | cut -d' ' -f1)
if [ -z "$pinned" ] || [ "$actual" != "$pinned" ] || [ "$actual" != "$released" ]; then
    echo "lucent-bridge RPM hash mismatch: file $actual, pinned ${pinned:-none}, release ${released:-none}"
    exit 1
fi
# dnf, not `rpm -i`: Fedora 45's rpm refuses unsigned packages.
"$DNF" "${DNF_OPTS[@]}" install "$dl/$BRIDGE_RPM"
rm -rf "$dl"

# A local RPM dropped into ./rpms/ (a bridge build under test) wins.
shopt -s nullglob
local_rpms=(/ctx/rpms/*."$ARCH".rpm /ctx/rpms/*.noarch.rpm)
if ((${#local_rpms[@]})); then
    "$DNF" "${DNF_OPTS[@]}" install "${local_rpms[@]}"
fi
shopt -u nullglob

# Double-click in Dolphin: the RPM ships its MIME defaults as a fragment;
# merge them into the distro-level mimeapps.list and into every
# higher-precedence list that exists, so nothing shadows them.
python3 /ctx/build_files/merge-mimeapps.py /usr/share/lucent-bridge/mimeapps.list \
    /usr/share/applications/mimeapps.list \
    /usr/share/applications/kde-mimeapps.list /etc/xdg/mimeapps.list /etc/xdg/kde-mimeapps.list

# The prefix template (1.7-2.4 GB) is NOT baked into the image: it is built
# at first boot into /var by lucent-bridge-template.service. lucent-bridge
# looks for it at /usr/share/lucent-bridge/prefix-template, so that path is
# a link into /var (dangling until the build is done; lucent-bridge then
# falls back to `wineboot`). In /var the per-app copy is also a btrfs
# reflink, which it can't be from composefs /usr.
ln -sfn /var/lib/lucent-bridge/prefix-template /usr/share/lucent-bridge/prefix-template

# --- Checks: fail the image build if Windows-app support is incomplete. ---
lucent-bridge --version
if rpm -q wine-systemd; then echo "wine-systemd must not be installed (binfmt clash with lucent-bridge)"; exit 1; fi
test -f /usr/lib/binfmt.d/lucent-bridge.conf
for mime in application/x-ms-dos-executable application/x-msdownload application/x-msi; do
    handler=$(XDG_CURRENT_DESKTOP=KDE XDG_CONFIG_HOME=/nonexistent XDG_DATA_HOME=/nonexistent \
              XDG_CONFIG_DIRS=/etc/xdg XDG_DATA_DIRS=/usr/local/share:/usr/share \
              gio mime "$mime" | sed -n 's/^Default application for .*: //p')
    echo "$mime -> ${handler:-nothing}"
    [ "$handler" = lucent-bridge.desktop ] || { echo "$mime must open with lucent-bridge"; exit 1; }
done

# ---------------------------------------------------------------------------
# 4. Lucent components and services
# ---------------------------------------------------------------------------
/ctx/build_files/lucent-store.sh          # the Store (replaces Discover in the launcher)
/ctx/build_files/lucent-settings.sh       # Settings (replaces System Settings in the launcher)
/ctx/build_files/lucent-bridge-sheet.sh   # "Preparing Windows program" sheet for lucent-bridge
/ctx/build_files/thispc.sh                # Files opens on "This PC" (kio_thispc, docs/this-pc.md)
python3 -m compileall -q /usr/lib/lucent   # /usr is read-only at runtime

# SELinux: Windows programs must be able to load Wine's DLLs from composefs
# /usr (see the module's comment; found by the x86_64 acceptance test).
grep -E '^\s*store-root' /etc/selinux/semanage.conf || echo "semanage store-root: default"
semodule -n -i /usr/share/selinux/packages/lucent/lucent_composefs_execmod.cil
semodule -l | grep -qx lucent_composefs_execmod || { echo "SELinux module not installed"; exit 1; }
ls -la /etc/selinux/targeted/policy/
# Lucent's own UI is written in English; translations (po/*.po) are compiled
# to /usr/share/locale/<lang>/LC_MESSAGES/lucent.mo and picked by locale.
PYTHONPATH=/usr/lib/lucent python3 -P -m lucent_migrate.i18n /ctx/migration-wizard/po /usr/share/locale
# Look: Papirus, rounded corners, icon caches (build_files/design.sh).
/ctx/build_files/design.sh
gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true

systemctl enable lucent-flatpak-setup.service lucent-flatpak-relabel.service lucent-drive-letters.service lucent-bridge-template.timer

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
