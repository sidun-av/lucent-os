#!/usr/bin/bash
# Build the installer's offline app bundle: a ready /var/lib/flatpak with
# Lucent's default apps, packed for iso/lucent-apps.ks.
#
# Runs as root inside a Fedora container of the target release and
# architecture (so the repo is written by the same flatpak the OS ships):
#   podman run --rm -v .:/src:ro -v OUT:/out quay.io/fedora/fedora:45 /src/iso/build-app-bundle.sh /out
# Produces OUT/lucent-apps/{flatpak.tar.zst.NN,SHA256SUMS,apps.txt,sizes.txt}.
set -euo pipefail
out=$1/lucent-apps
list=/src/system_files/usr/share/lucent/flatpaks.list

dnf -y -q --setopt=install_weak_deps=False install flatpak zstd tar python3 >/dev/null
mapfile -t APPS < <(grep -Ev '^\s*(#|$)' "$list")

# Same remote setup as the installed system (lucent-flatpak-setup).
flatpak remote-add --system --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak remote-modify --system --enable --no-filter flathub
# App translations (.Locale extensions) follow the system's languages; the
# build container has none, so ask for Lucent's own (English, Russian).
# Unset again afterwards: on the installed system later updates follow the
# languages the user actually chose.
flatpak config --system --set languages 'en;ru'
flatpak install --system --noninteractive flathub "${APPS[@]}"
flatpak config --system --unset languages
# Old commits and partial downloads aren't needed on a fresh system.
flatpak uninstall --system --noninteractive --unused || true
flatpak repair --system >/dev/null 2>&1 || true
rm -rf /var/lib/flatpak/repo/tmp/* /var/lib/flatpak/.removed

flatpak list --system --columns=application,branch,arch,size > /tmp/apps.txt
cat /tmp/apps.txt
installed=$(du -sb /var/lib/flatpak | cut -f1)

rm -rf "$out"
mkdir -p "$out"
# Member order (iso/bundle-members.py): the same file of two versions of a
# runtime side by side, so zstd stores the second copy cheaply; deployed
# files before the repo's hard links to them. tar keeps those hard links, so
# each file's content is stored once.
# zstd -19 with a 2^27 window: the largest window decoders accept by default
# (the installer's `zstd -dc` included), so unpacking needs no extra memory
# or flags.
python3 /src/iso/bundle-members.py /var/lib/flatpak > /tmp/members
tar -C /var/lib/flatpak --numeric-owner --no-recursion --null -T /tmp/members -cf - \
    | zstd -T0 -19 --long=27 -q \
    | split -b 1024M -d -a 2 - "$out/flatpak.tar.zst."
if [ -n "${LUCENT_BUNDLE_COMPARE:-}" ]; then
    # Measurement only: the previous packing (plain order, zstd -12).
    old=$(tar -C /var/lib/flatpak --numeric-owner -cf - . | zstd -T0 -12 --long=27 -q | wc -c)
    echo "previous_packing_bytes $old" | tee "$1/bundle-compare.txt"
fi
(cd "$out" && sha256sum flatpak.tar.zst.* > SHA256SUMS)
cp /tmp/apps.txt "$out/apps.txt"
packed=$(cat "$out"/flatpak.tar.zst.* | wc -c)
printf 'installed_bytes %s\npacked_bytes %s\n' "$installed" "$packed" | tee "$out/sizes.txt"
ls -la "$out"
